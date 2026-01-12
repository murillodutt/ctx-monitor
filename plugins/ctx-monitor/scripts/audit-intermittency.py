#!/usr/bin/env python3
"""
audit-intermittency.py - Detect intermittent failures in execution traces

Checks for:
- Tools that succeed sometimes and fail others
- Hooks that didn't fire when expected (PreToolUse without PostToolUse)
- Partial executions and oscillating error patterns
- Session stability issues

Usage:
    python audit-intermittency.py <traces_dir> [--format json|text|md] [--threshold 0.1]
"""

import json
import sys
import argparse
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any, Tuple


class IntermittencyAuditor:
    """Auditor for detecting intermittent failures in traces."""

    def __init__(self, threshold: float = 0.1):
        """
        Initialize the auditor.

        Args:
            threshold: Error rate threshold to flag as intermittent (0.1 = 10%)
        """
        self.threshold = threshold
        self.issues: List[Dict[str, Any]] = []

    def load_traces(self, traces_dir: Path) -> List[Dict[str, Any]]:
        """Load all trace files from directory."""
        all_events = []
        for trace_file in traces_dir.glob("session_*.jsonl"):
            with open(trace_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            event = json.loads(line)
                            event['_source_file'] = trace_file.name
                            all_events.append(event)
                        except json.JSONDecodeError:
                            pass
        return all_events

    def load_sessions_index(self, traces_dir: Path) -> Dict[str, Any]:
        """Load sessions index if available."""
        index_file = traces_dir / "sessions.json"
        if index_file.exists():
            try:
                content = index_file.read_text().strip()
                if not content:
                    return {}
                return json.loads(content)
            except (json.JSONDecodeError, KeyError):
                return {}
        return {}

    def audit_tool_intermittency(self, events: List[Dict[str, Any]]) -> None:
        """Check for tools with inconsistent success/failure rates."""
        tool_stats = defaultdict(lambda: {"success": 0, "error": 0, "sessions": set()})

        for event in events:
            if event.get("event_type") == "PostToolUse":
                tool_name = event.get("tool_name", "unknown")
                session_id = event.get("session_id", "unknown")
                status = event.get("status", "unknown")

                tool_stats[tool_name]["sessions"].add(session_id)
                if status == "error":
                    tool_stats[tool_name]["error"] += 1
                else:
                    tool_stats[tool_name]["success"] += 1

        for tool, stats in tool_stats.items():
            total = stats["success"] + stats["error"]
            if total < 2:
                continue

            error_rate = stats["error"] / total

            # Flag if error rate is between threshold and 100% (intermittent, not always failing)
            if self.threshold <= error_rate < 1.0:
                self.issues.append({
                    "type": "intermittent_tool_failure",
                    "severity": "warning" if error_rate < 0.3 else "critical",
                    "tool": tool,
                    "success_count": stats["success"],
                    "error_count": stats["error"],
                    "error_rate": round(error_rate * 100, 1),
                    "sessions_affected": len(stats["sessions"]),
                    "message": f"Tool '{tool}' has {error_rate*100:.1f}% failure rate ({stats['error']}/{total} calls)",
                    "remediation": f"Investigate why '{tool}' fails intermittently. Check input patterns and error messages."
                })

    def audit_unpaired_events(self, events: List[Dict[str, Any]]) -> None:
        """Check for PreToolUse events without matching PostToolUse."""
        # Group by session
        sessions = defaultdict(list)
        for event in events:
            sessions[event.get("session_id", "unknown")].append(event)

        for session_id, session_events in sessions.items():
            # Track PreToolUse events waiting for PostToolUse
            pending_pre = {}  # key: (tool_name, timestamp_prefix) -> event

            for event in sorted(session_events, key=lambda e: e.get("timestamp", "")):
                event_type = event.get("event_type")
                tool_name = event.get("tool_name", "unknown")
                timestamp = event.get("timestamp", "")[:19]  # Truncate to seconds

                if event_type == "PreToolUse":
                    key = (tool_name, timestamp)
                    pending_pre[key] = event
                elif event_type == "PostToolUse":
                    # Find matching PreToolUse
                    key = (tool_name, timestamp)
                    if key in pending_pre:
                        del pending_pre[key]
                    else:
                        # Try finding any pending PreToolUse for this tool
                        for k in list(pending_pre.keys()):
                            if k[0] == tool_name:
                                del pending_pre[k]
                                break

            # Report unpaired PreToolUse events
            for (tool_name, timestamp), event in pending_pre.items():
                self.issues.append({
                    "type": "unpaired_pretooluse",
                    "severity": "warning",
                    "tool": tool_name,
                    "session_id": session_id,
                    "timestamp": event.get("timestamp"),
                    "message": f"PreToolUse for '{tool_name}' has no matching PostToolUse",
                    "remediation": "Tool execution may have been interrupted. Check for timeouts or crashes."
                })

    def audit_oscillating_errors(self, events: List[Dict[str, Any]]) -> None:
        """Check for oscillating error patterns (success-fail-success-fail)."""
        # Group by session and tool
        tool_sequences = defaultdict(list)  # (session_id, tool_name) -> [status, status, ...]

        for event in sorted(events, key=lambda e: e.get("timestamp", "")):
            if event.get("event_type") == "PostToolUse":
                key = (event.get("session_id"), event.get("tool_name"))
                status = "error" if event.get("status") == "error" else "success"
                tool_sequences[key].append(status)

        for (session_id, tool_name), sequence in tool_sequences.items():
            if len(sequence) < 4:
                continue

            # Count status changes
            changes = sum(1 for i in range(1, len(sequence)) if sequence[i] != sequence[i-1])
            change_rate = changes / (len(sequence) - 1)

            # If more than 40% of consecutive calls flip status, it's oscillating
            if change_rate > 0.4 and changes >= 3:
                self.issues.append({
                    "type": "oscillating_errors",
                    "severity": "warning",
                    "tool": tool_name,
                    "session_id": session_id,
                    "pattern": "->".join(sequence[:10]),  # First 10
                    "change_rate": round(change_rate * 100, 1),
                    "message": f"Tool '{tool_name}' shows oscillating success/failure pattern",
                    "remediation": "Investigate environmental factors causing inconsistent behavior."
                })

    def audit_session_stability(self, events: List[Dict[str, Any]]) -> None:
        """Check for sessions with abnormal start/end patterns."""
        sessions = defaultdict(lambda: {"start": 0, "end": 0, "events": 0})

        for event in events:
            session_id = event.get("session_id", "unknown")
            event_type = event.get("event_type")
            sessions[session_id]["events"] += 1

            if event_type == "SessionStart":
                sessions[session_id]["start"] += 1
            elif event_type == "SessionEnd":
                sessions[session_id]["end"] += 1

        for session_id, stats in sessions.items():
            # Multiple starts without ends
            if stats["start"] > stats["end"] + 1:
                self.issues.append({
                    "type": "session_instability",
                    "severity": "info",
                    "session_id": session_id,
                    "starts": stats["start"],
                    "ends": stats["end"],
                    "message": f"Session has {stats['start']} starts but only {stats['end']} ends",
                    "remediation": "Session may have crashed or been interrupted multiple times."
                })

    def run_audit(self, traces_dir: Path) -> Dict[str, Any]:
        """Run all intermittency audits."""
        events = self.load_traces(traces_dir)

        if not events:
            return {
                "audit_type": "intermittency",
                "status": "no_data",
                "message": "No trace events found",
                "issues": []
            }

        # Run all checks
        self.audit_tool_intermittency(events)
        self.audit_unpaired_events(events)
        self.audit_oscillating_errors(events)
        self.audit_session_stability(events)

        # Categorize by severity
        critical = [i for i in self.issues if i.get("severity") == "critical"]
        warning = [i for i in self.issues if i.get("severity") == "warning"]
        info = [i for i in self.issues if i.get("severity") == "info"]

        return {
            "audit_type": "intermittency",
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "total_events_analyzed": len(events),
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
    lines.append("INTERMITTENCY AUDIT REPORT")
    lines.append("=" * 60)
    lines.append(f"\nStatus: {result.get('status')}")
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
        if issue.get("session_id"):
            lines.append(f"  Session: {issue.get('session_id')}")
        lines.append(f"  Remediation: {issue.get('remediation')}")

    lines.append("\n" + "=" * 60)
    return "\n".join(lines)


def format_markdown(result: Dict[str, Any]) -> str:
    """Format audit result as Markdown."""
    lines = []
    lines.append("# Intermittency Audit Report\n")
    lines.append(f"**Status:** {result.get('status')}")
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
                lines.append(f"**Tool:** `{issue.get('tool')}`\n")
            if issue.get("session_id"):
                lines.append(f"**Session:** `{issue.get('session_id')}`\n")
            if issue.get("error_rate"):
                lines.append(f"**Error Rate:** {issue.get('error_rate')}%\n")
            lines.append(f"**Remediation:** {issue.get('remediation')}\n")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Audit traces for intermittent failures")
    parser.add_argument("traces_dir", help="Path to traces directory")
    parser.add_argument("--format", choices=["json", "text", "md"], default="text")
    parser.add_argument("--threshold", type=float, default=0.1,
                        help="Error rate threshold for intermittency (default: 0.1 = 10%%)")
    args = parser.parse_args()

    traces_dir = Path(args.traces_dir)
    if not traces_dir.exists():
        print(f"Error: Directory not found: {traces_dir}", file=sys.stderr)
        sys.exit(1)

    auditor = IntermittencyAuditor(threshold=args.threshold)
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
