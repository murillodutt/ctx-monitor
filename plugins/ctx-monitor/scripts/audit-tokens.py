#!/usr/bin/env python3
"""
audit-tokens.py - Analyze token efficiency in execution traces

Checks for:
- Token usage per session and tool
- Redundant context loading patterns
- Oversized tool inputs/outputs
- Optimization opportunities

Usage:
    python audit-tokens.py <traces_dir> [--format json|text|md] [--threshold 5000]
"""

import json
import sys
import argparse
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any, Tuple


# Approximate token estimation (chars / 4 is a rough estimate)
def estimate_tokens(text: str) -> int:
    """Estimate token count from text length."""
    if not text:
        return 0
    return len(text) // 4


class TokensAuditor:
    """Auditor for analyzing token efficiency."""

    def __init__(self, threshold: int = 5000):
        """
        Initialize the auditor.

        Args:
            threshold: Token threshold for flagging oversized inputs (default: 5000)
        """
        self.threshold = threshold
        self.issues: List[Dict[str, Any]] = []

    def load_traces(self, traces_dir: Path) -> Dict[str, List[Dict[str, Any]]]:
        """Load all trace files grouped by session."""
        sessions = defaultdict(list)
        for trace_file in traces_dir.glob("session_*.jsonl"):
            with open(trace_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            event = json.loads(line)
                            session_id = event.get("session_id", trace_file.stem)
                            event['_source_file'] = trace_file.name
                            sessions[session_id].append(event)
                        except json.JSONDecodeError:
                            pass
        return dict(sessions)

    def audit_session_tokens(self, sessions: Dict[str, List[Dict[str, Any]]]) -> None:
        """Analyze token usage per session."""
        session_stats = {}

        for session_id, events in sessions.items():
            total_input_tokens = 0
            total_output_tokens = 0
            tool_tokens = defaultdict(lambda: {"input": 0, "output": 0, "count": 0})

            for event in events:
                event_type = event.get("event_type")
                tool_name = event.get("tool_name", "unknown")

                if event_type == "PreToolUse":
                    # Estimate input tokens from args_preview
                    args_preview = event.get("args_preview", "")
                    input_tokens = estimate_tokens(args_preview)
                    total_input_tokens += input_tokens
                    tool_tokens[tool_name]["input"] += input_tokens
                    tool_tokens[tool_name]["count"] += 1

                elif event_type == "PostToolUse":
                    # Estimate output tokens from result_preview
                    result_preview = event.get("result_preview", "")
                    output_tokens = estimate_tokens(result_preview)
                    total_output_tokens += output_tokens
                    tool_tokens[tool_name]["output"] += output_tokens

            session_stats[session_id] = {
                "total_input_tokens": total_input_tokens,
                "total_output_tokens": total_output_tokens,
                "total_tokens": total_input_tokens + total_output_tokens,
                "tool_breakdown": dict(tool_tokens),
                "event_count": len(events)
            }

        # Find sessions with high token usage
        if session_stats:
            avg_tokens = sum(s["total_tokens"] for s in session_stats.values()) / len(session_stats)

            for session_id, stats in session_stats.items():
                if stats["total_tokens"] > avg_tokens * 2:
                    self.issues.append({
                        "type": "high_token_session",
                        "severity": "warning",
                        "session_id": session_id,
                        "total_tokens": stats["total_tokens"],
                        "average_tokens": int(avg_tokens),
                        "message": f"Session uses {stats['total_tokens']} tokens (2x above average {int(avg_tokens)})",
                        "remediation": "Review session for unnecessary tool calls or oversized inputs."
                    })

    def audit_oversized_inputs(self, sessions: Dict[str, List[Dict[str, Any]]]) -> None:
        """Check for oversized tool inputs."""
        for session_id, events in sessions.items():
            for event in events:
                if event.get("event_type") != "PreToolUse":
                    continue

                tool_name = event.get("tool_name", "unknown")
                args_preview = event.get("args_preview", "")
                input_tokens = estimate_tokens(args_preview)

                if input_tokens > self.threshold:
                    self.issues.append({
                        "type": "oversized_input",
                        "severity": "warning",
                        "session_id": session_id,
                        "tool": tool_name,
                        "tokens": input_tokens,
                        "threshold": self.threshold,
                        "timestamp": event.get("timestamp"),
                        "message": f"Tool '{tool_name}' received ~{input_tokens} tokens (threshold: {self.threshold})",
                        "remediation": f"Consider reducing input size for '{tool_name}' calls."
                    })

    def audit_redundant_reads(self, sessions: Dict[str, List[Dict[str, Any]]]) -> None:
        """Check for redundant file read patterns."""
        for session_id, events in sessions.items():
            file_reads = defaultdict(list)

            for event in events:
                if event.get("event_type") != "PreToolUse":
                    continue

                tool_name = event.get("tool_name", "")
                if tool_name not in ["Read", "Glob", "Grep"]:
                    continue

                # Try to extract file path from args
                args_preview = event.get("args_preview", "")
                timestamp = event.get("timestamp", "")

                # Simple heuristic: use the preview as a key
                file_reads[args_preview].append(timestamp)

            # Flag files read multiple times
            for args, timestamps in file_reads.items():
                if len(timestamps) > 2:
                    self.issues.append({
                        "type": "redundant_reads",
                        "severity": "info",
                        "session_id": session_id,
                        "read_count": len(timestamps),
                        "args_preview": args[:100],
                        "message": f"Same read operation performed {len(timestamps)} times in session",
                        "remediation": "Consider caching file contents or reducing redundant reads."
                    })

    def audit_tool_efficiency(self, sessions: Dict[str, List[Dict[str, Any]]]) -> None:
        """Analyze tool usage efficiency patterns."""
        tool_usage = defaultdict(lambda: {"calls": 0, "errors": 0, "total_input": 0, "total_output": 0})

        for session_id, events in sessions.items():
            for event in events:
                event_type = event.get("event_type")
                tool_name = event.get("tool_name", "unknown")

                if event_type == "PreToolUse":
                    tool_usage[tool_name]["calls"] += 1
                    tool_usage[tool_name]["total_input"] += estimate_tokens(event.get("args_preview", ""))

                elif event_type == "PostToolUse":
                    tool_usage[tool_name]["total_output"] += estimate_tokens(event.get("result_preview", ""))
                    if event.get("status") == "error":
                        tool_usage[tool_name]["errors"] += 1

        # Flag tools with high token usage but high error rates
        for tool_name, stats in tool_usage.items():
            if stats["calls"] < 3:
                continue

            total_tokens = stats["total_input"] + stats["total_output"]
            error_rate = stats["errors"] / stats["calls"]
            tokens_per_call = total_tokens / stats["calls"]

            # High token usage with high error rate = waste
            if error_rate > 0.3 and tokens_per_call > 1000:
                self.issues.append({
                    "type": "inefficient_tool_usage",
                    "severity": "warning",
                    "tool": tool_name,
                    "total_calls": stats["calls"],
                    "error_rate": round(error_rate * 100, 1),
                    "tokens_per_call": int(tokens_per_call),
                    "message": f"Tool '{tool_name}' has {error_rate*100:.1f}% error rate with ~{int(tokens_per_call)} tokens/call",
                    "remediation": f"Reduce token waste by fixing errors in '{tool_name}' usage patterns."
                })

    def audit_context_patterns(self, sessions: Dict[str, List[Dict[str, Any]]]) -> None:
        """Analyze context loading patterns."""
        for session_id, events in sessions.items():
            # Track Read operations at session start
            session_events = sorted(events, key=lambda e: e.get("timestamp", ""))

            early_reads = []
            for i, event in enumerate(session_events[:20]):  # First 20 events
                if event.get("event_type") == "PreToolUse" and event.get("tool_name") == "Read":
                    early_reads.append(event)

            # If many reads at start, might be loading too much context
            if len(early_reads) > 5:
                total_tokens = sum(estimate_tokens(e.get("args_preview", "")) for e in early_reads)
                self.issues.append({
                    "type": "heavy_context_loading",
                    "severity": "info",
                    "session_id": session_id,
                    "read_count": len(early_reads),
                    "estimated_tokens": total_tokens,
                    "message": f"Session starts with {len(early_reads)} Read operations (~{total_tokens} tokens)",
                    "remediation": "Consider lazy loading or reducing initial context."
                })

    def run_audit(self, traces_dir: Path) -> Dict[str, Any]:
        """Run all token audits."""
        sessions = self.load_traces(traces_dir)

        if not sessions:
            return {
                "audit_type": "tokens",
                "status": "no_data",
                "message": "No trace sessions found",
                "issues": []
            }

        total_events = sum(len(events) for events in sessions.values())

        # Run all checks
        self.audit_session_tokens(sessions)
        self.audit_oversized_inputs(sessions)
        self.audit_redundant_reads(sessions)
        self.audit_tool_efficiency(sessions)
        self.audit_context_patterns(sessions)

        # Categorize by severity
        critical = [i for i in self.issues if i.get("severity") == "critical"]
        warning = [i for i in self.issues if i.get("severity") == "warning"]
        info = [i for i in self.issues if i.get("severity") == "info"]

        return {
            "audit_type": "tokens",
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "sessions_analyzed": len(sessions),
            "total_events_analyzed": total_events,
            "summary": {
                "total_issues": len(self.issues),
                "critical": len(critical),
                "warning": len(warning),
                "info": len(info)
            },
            "issues": self.issues
        }


def format_text(result: Dict[str, Any]) -> str:
    """Format audit result as plain text."""
    lines = []
    lines.append("=" * 60)
    lines.append("TOKEN EFFICIENCY AUDIT REPORT")
    lines.append("=" * 60)
    lines.append(f"\nStatus: {result.get('status')}")
    lines.append(f"Sessions Analyzed: {result.get('sessions_analyzed', 0)}")
    lines.append(f"Events Analyzed: {result.get('total_events_analyzed', 0)}")

    summary = result.get("summary", {})
    lines.append(f"\nIssues Found: {summary.get('total_issues', 0)}")
    lines.append(f"  - Critical: {summary.get('critical', 0)}")
    lines.append(f"  - Warning: {summary.get('warning', 0)}")
    lines.append(f"  - Info: {summary.get('info', 0)}")

    for issue in result.get("issues", []):
        severity = issue.get("severity", "info").upper()
        lines.append(f"\n[{severity}] {issue.get('type')}")
        lines.append(f"  Message: {issue.get('message')}")
        if issue.get("tool"):
            lines.append(f"  Tool: {issue.get('tool')}")
        if issue.get("tokens"):
            lines.append(f"  Tokens: ~{issue.get('tokens')}")
        lines.append(f"  Remediation: {issue.get('remediation')}")

    lines.append("\n" + "=" * 60)
    return "\n".join(lines)


def format_markdown(result: Dict[str, Any]) -> str:
    """Format audit result as Markdown."""
    lines = []
    lines.append("# Token Efficiency Audit Report\n")
    lines.append(f"**Status:** {result.get('status')}")
    lines.append(f"**Sessions Analyzed:** {result.get('sessions_analyzed', 0)}")
    lines.append(f"**Events Analyzed:** {result.get('total_events_analyzed', 0)}")
    lines.append(f"**Timestamp:** {result.get('timestamp')}\n")

    summary = result.get("summary", {})
    lines.append("## Summary\n")
    lines.append("| Severity | Count |")
    lines.append("|----------|-------|")
    lines.append(f"| Critical | {summary.get('critical', 0)} |")
    lines.append(f"| Warning | {summary.get('warning', 0)} |")
    lines.append(f"| Info | {summary.get('info', 0)} |")
    lines.append(f"| **Total** | **{summary.get('total_issues', 0)}** |")

    if result.get("issues"):
        lines.append("\n## Issues\n")
        for issue in result.get("issues", []):
            severity = issue.get("severity", "info").upper()
            emoji = {"CRITICAL": "🔴", "WARNING": "🟡", "INFO": "🔵"}.get(severity, "⚪")
            lines.append(f"### {emoji} [{severity}] {issue.get('type')}\n")
            lines.append(f"**Message:** {issue.get('message')}\n")
            if issue.get("tool"):
                lines.append(f"**Tool:** `{issue.get('tool')}`")
            if issue.get("tokens"):
                lines.append(f"**Estimated Tokens:** ~{issue.get('tokens')}")
            if issue.get("session_id"):
                lines.append(f"**Session:** `{issue.get('session_id')}`")
            lines.append(f"\n**Remediation:** {issue.get('remediation')}\n")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Audit traces for token efficiency")
    parser.add_argument("traces_dir", help="Path to traces directory")
    parser.add_argument("--format", choices=["json", "text", "md"], default="text")
    parser.add_argument("--threshold", type=int, default=5000,
                        help="Token threshold for oversized inputs (default: 5000)")
    args = parser.parse_args()

    traces_dir = Path(args.traces_dir)
    if not traces_dir.exists():
        print(f"Error: Directory not found: {traces_dir}", file=sys.stderr)
        sys.exit(1)

    auditor = TokensAuditor(threshold=args.threshold)
    result = auditor.run_audit(traces_dir)

    if args.format == "json":
        print(json.dumps(result, indent=2))
    elif args.format == "md":
        print(format_markdown(result))
    else:
        print(format_text(result))

    # Exit with error code if critical issues found
    if result.get("summary", {}).get("critical", 0) > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
