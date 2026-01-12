#!/usr/bin/env python3
"""
audit-compliance.py - Check output format compliance and standards

Checks for:
- Output format consistency across sessions
- Structured data format validation
- Error message pattern compliance
- Logging standards adherence
- Event schema compliance

Usage:
    python audit-compliance.py <traces_dir> [--format json|text|md] [--strict]
"""

import json
import sys
import re
import argparse
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any, Optional, Set


class ComplianceAuditor:
    """Auditor for checking output format compliance."""

    # Required fields for each event type
    REQUIRED_FIELDS = {
        "SessionStart": ["event_id", "session_id", "timestamp", "event_type", "status"],
        "SessionEnd": ["event_id", "session_id", "timestamp", "event_type", "status"],
        "PreToolUse": ["event_id", "session_id", "timestamp", "event_type", "tool_name"],
        "PostToolUse": ["event_id", "session_id", "timestamp", "event_type", "tool_name", "status"],
        "Stop": ["event_id", "session_id", "timestamp", "event_type"],
        "SubagentStop": ["event_id", "session_id", "timestamp", "event_type"],
        "UserPromptSubmit": ["event_id", "session_id", "timestamp", "event_type", "status"],
        "PreCompact": ["event_id", "session_id", "timestamp", "event_type", "status"],
        "Notification": ["event_id", "session_id", "timestamp", "event_type", "status"],
    }

    # Valid status values
    VALID_STATUSES = {"pending", "success", "error", "started", "ended", "completed", "unknown", "submitted", "compacting", "notified"}

    # Valid event types
    VALID_EVENT_TYPES = {
        "SessionStart", "SessionEnd", "PreToolUse", "PostToolUse",
        "Stop", "SubagentStop", "UserPromptSubmit", "PreCompact", "Notification"
    }

    def __init__(self, strict: bool = False):
        """
        Initialize the auditor.

        Args:
            strict: Enable strict mode for additional checks
        """
        self.strict = strict
        self.issues: List[Dict[str, Any]] = []

    def load_traces(self, traces_dir: Path) -> List[Dict[str, Any]]:
        """Load all trace events from directory."""
        events = []
        for trace_file in traces_dir.glob("session_*.jsonl"):
            line_num = 0
            with open(trace_file, 'r') as f:
                for line in f:
                    line_num += 1
                    line = line.strip()
                    if line:
                        try:
                            event = json.loads(line)
                            event['_source_file'] = trace_file.name
                            event['_line_num'] = line_num
                            events.append(event)
                        except json.JSONDecodeError as e:
                            self.issues.append({
                                "type": "invalid_json",
                                "severity": "critical",
                                "file": trace_file.name,
                                "line": line_num,
                                "error": str(e),
                                "message": f"Invalid JSON at line {line_num} in {trace_file.name}",
                                "remediation": "Fix the malformed JSON in the trace file."
                            })
        return events

    def audit_schema_compliance(self, events: List[Dict[str, Any]]) -> None:
        """Check if events comply with expected schema."""
        for event in events:
            event_type = event.get("event_type", "unknown")
            source_file = event.get("_source_file", "unknown")
            line_num = event.get("_line_num", 0)

            # Check for valid event type
            if event_type not in self.VALID_EVENT_TYPES:
                self.issues.append({
                    "type": "invalid_event_type",
                    "severity": "warning",
                    "event_type": event_type,
                    "file": source_file,
                    "line": line_num,
                    "message": f"Unknown event type: '{event_type}'",
                    "remediation": f"Use one of: {', '.join(self.VALID_EVENT_TYPES)}"
                })
                continue

            # Check required fields
            required = self.REQUIRED_FIELDS.get(event_type, [])
            missing = [f for f in required if f not in event]

            if missing:
                self.issues.append({
                    "type": "missing_required_fields",
                    "severity": "warning",
                    "event_type": event_type,
                    "missing_fields": missing,
                    "file": source_file,
                    "line": line_num,
                    "message": f"Event missing required fields: {missing}",
                    "remediation": f"Ensure all required fields are present: {required}"
                })

            # Check status value
            status = event.get("status")
            if status and status not in self.VALID_STATUSES:
                self.issues.append({
                    "type": "invalid_status_value",
                    "severity": "info",
                    "status": status,
                    "file": source_file,
                    "line": line_num,
                    "message": f"Non-standard status value: '{status}'",
                    "remediation": f"Use one of: {', '.join(self.VALID_STATUSES)}"
                })

    def audit_timestamp_format(self, events: List[Dict[str, Any]]) -> None:
        """Check timestamp format compliance (ISO8601)."""
        iso8601_pattern = re.compile(
            r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?$'
        )

        for event in events:
            timestamp = event.get("timestamp")
            if not timestamp:
                continue

            if not iso8601_pattern.match(timestamp):
                self.issues.append({
                    "type": "invalid_timestamp_format",
                    "severity": "info",
                    "timestamp": timestamp,
                    "file": event.get("_source_file"),
                    "line": event.get("_line_num"),
                    "message": f"Timestamp '{timestamp}' doesn't match ISO8601 format",
                    "remediation": "Use format: YYYY-MM-DDTHH:MM:SS.sssZ"
                })

    def audit_event_id_format(self, events: List[Dict[str, Any]]) -> None:
        """Check event_id format (should be UUID-like)."""
        uuid_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            re.IGNORECASE
        )

        seen_ids: Set[str] = set()

        for event in events:
            event_id = event.get("event_id")
            if not event_id:
                continue

            # Check format
            if self.strict and not uuid_pattern.match(event_id):
                self.issues.append({
                    "type": "non_uuid_event_id",
                    "severity": "info",
                    "event_id": event_id,
                    "file": event.get("_source_file"),
                    "message": f"Event ID '{event_id}' is not a standard UUID",
                    "remediation": "Use UUID format for event IDs."
                })

            # Check uniqueness
            if event_id in seen_ids:
                self.issues.append({
                    "type": "duplicate_event_id",
                    "severity": "warning",
                    "event_id": event_id,
                    "file": event.get("_source_file"),
                    "message": f"Duplicate event_id: '{event_id}'",
                    "remediation": "Ensure each event has a unique ID."
                })
            seen_ids.add(event_id)

    def audit_error_message_patterns(self, events: List[Dict[str, Any]]) -> None:
        """Check error message consistency and quality."""
        error_patterns = defaultdict(list)

        for event in events:
            if event.get("status") != "error":
                continue

            error_msg = event.get("error_message", "")

            # Check for empty error messages
            if not error_msg or error_msg.strip() == "":
                self.issues.append({
                    "type": "empty_error_message",
                    "severity": "warning",
                    "event_type": event.get("event_type"),
                    "tool": event.get("tool_name"),
                    "file": event.get("_source_file"),
                    "message": "Error event has no error_message",
                    "remediation": "Always include descriptive error messages."
                })
                continue

            # Check for generic error messages
            generic_patterns = [
                r'^error$',
                r'^unknown error$',
                r'^failed$',
                r'^exception$',
            ]

            for pattern in generic_patterns:
                if re.match(pattern, error_msg.lower()):
                    self.issues.append({
                        "type": "generic_error_message",
                        "severity": "info",
                        "error_message": error_msg,
                        "file": event.get("_source_file"),
                        "message": f"Generic error message: '{error_msg}'",
                        "remediation": "Use descriptive error messages with context."
                    })
                    break

            # Group similar errors
            error_key = error_msg[:50].lower()
            error_patterns[error_key].append(event)

        # Flag frequently occurring errors
        for error_key, occurrences in error_patterns.items():
            if len(occurrences) > 5:
                self.issues.append({
                    "type": "frequent_error",
                    "severity": "warning",
                    "error_pattern": error_key,
                    "occurrence_count": len(occurrences),
                    "message": f"Error pattern occurs {len(occurrences)} times: '{error_key}...'",
                    "remediation": "Investigate root cause of recurring error."
                })

    def audit_tool_name_consistency(self, events: List[Dict[str, Any]]) -> None:
        """Check tool name consistency and validity."""
        known_tools = {
            "Read", "Write", "Edit", "Bash", "Glob", "Grep",
            "Task", "WebFetch", "WebSearch", "TodoWrite", "AskUserQuestion",
            "NotebookEdit", "EnterPlanMode", "ExitPlanMode"
        }

        tool_names = defaultdict(int)

        for event in events:
            tool_name = event.get("tool_name")
            if tool_name:
                tool_names[tool_name] += 1

        for tool_name, count in tool_names.items():
            # Check for case inconsistencies
            if tool_name not in known_tools:
                # Check if it's a case variation of a known tool
                for known in known_tools:
                    if tool_name.lower() == known.lower() and tool_name != known:
                        self.issues.append({
                            "type": "tool_name_case_mismatch",
                            "severity": "info",
                            "found": tool_name,
                            "expected": known,
                            "count": count,
                            "message": f"Tool name '{tool_name}' should be '{known}'",
                            "remediation": "Use consistent tool name casing."
                        })
                        break

    def audit_sessions_index(self, traces_dir: Path) -> None:
        """Check sessions.json index compliance."""
        index_file = traces_dir / "sessions.json"

        if not index_file.exists():
            self.issues.append({
                "type": "missing_sessions_index",
                "severity": "warning",
                "file": "sessions.json",
                "message": "Sessions index file not found",
                "remediation": "Create sessions.json to track session metadata."
            })
            return

        try:
            content = index_file.read_text().strip()
            if not content:
                self.issues.append({
                    "type": "empty_sessions_index",
                    "severity": "warning",
                    "file": "sessions.json",
                    "message": "Sessions index file is empty",
                    "remediation": "Sessions will be indexed automatically on next event."
                })
                return
            index = json.loads(content)
        except json.JSONDecodeError as e:
            self.issues.append({
                "type": "invalid_sessions_index",
                "severity": "critical",
                "file": "sessions.json",
                "error": str(e),
                "message": "Sessions index is not valid JSON",
                "remediation": "Fix the sessions.json file format."
            })
            return

        # Check index structure
        if not isinstance(index, dict):
            self.issues.append({
                "type": "invalid_sessions_index_structure",
                "severity": "warning",
                "file": "sessions.json",
                "message": "Sessions index should be a JSON object",
                "remediation": "Use object format: {\"session_id\": {metadata}}"
            })
            return

        # Check each session entry
        for session_id, metadata in index.items():
            if not isinstance(metadata, dict):
                continue

            # Check for recommended fields
            recommended = ["started_at", "event_count"]
            missing = [f for f in recommended if f not in metadata]

            if missing and self.strict:
                self.issues.append({
                    "type": "incomplete_session_metadata",
                    "severity": "info",
                    "session_id": session_id,
                    "missing": missing,
                    "message": f"Session '{session_id}' missing metadata: {missing}",
                    "remediation": "Include started_at and event_count in session metadata."
                })

    def run_audit(self, traces_dir: Path) -> Dict[str, Any]:
        """Run all compliance audits."""
        events = self.load_traces(traces_dir)

        # Run all checks
        self.audit_schema_compliance(events)
        self.audit_timestamp_format(events)
        self.audit_event_id_format(events)
        self.audit_error_message_patterns(events)
        self.audit_tool_name_consistency(events)
        self.audit_sessions_index(traces_dir)

        # Categorize by severity
        critical = [i for i in self.issues if i.get("severity") == "critical"]
        warning = [i for i in self.issues if i.get("severity") == "warning"]
        info = [i for i in self.issues if i.get("severity") == "info"]

        return {
            "audit_type": "compliance",
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "strict_mode": self.strict,
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
    lines.append("COMPLIANCE AUDIT REPORT")
    lines.append("=" * 60)
    lines.append(f"\nStatus: {result.get('status')}")
    lines.append(f"Strict Mode: {result.get('strict_mode')}")
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
        if issue.get("file"):
            lines.append(f"  File: {issue.get('file')}")
        if issue.get("line"):
            lines.append(f"  Line: {issue.get('line')}")
        lines.append(f"  Remediation: {issue.get('remediation')}")

    lines.append("\n" + "=" * 60)
    return "\n".join(lines)


def format_markdown(result: Dict[str, Any]) -> str:
    """Format audit result as Markdown."""
    lines = []
    lines.append("# Compliance Audit Report\n")
    lines.append(f"**Status:** {result.get('status')}")
    lines.append(f"**Strict Mode:** {result.get('strict_mode')}")
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

        # Group by type
        by_type = defaultdict(list)
        for issue in result.get("issues", []):
            by_type[issue.get("type", "other")].append(issue)

        for issue_type, issues in by_type.items():
            severity = issues[0].get("severity", "info").upper()
            emoji = {"CRITICAL": "🔴", "WARNING": "🟡", "INFO": "🔵"}.get(severity, "⚪")
            lines.append(f"### {emoji} {issue_type} ({len(issues)} occurrences)\n")

            for issue in issues[:5]:  # Show first 5
                lines.append(f"- **{issue.get('message')}**")
                if issue.get("file"):
                    lines.append(f"  - File: `{issue.get('file')}`")
                if issue.get("remediation"):
                    lines.append(f"  - Fix: {issue.get('remediation')}")

            if len(issues) > 5:
                lines.append(f"- *...and {len(issues) - 5} more*\n")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Audit traces for format compliance")
    parser.add_argument("traces_dir", help="Path to traces directory")
    parser.add_argument("--format", choices=["json", "text", "md"], default="text")
    parser.add_argument("--strict", action="store_true",
                        help="Enable strict mode for additional checks")
    args = parser.parse_args()

    traces_dir = Path(args.traces_dir)
    if not traces_dir.exists():
        print(f"Error: Directory not found: {traces_dir}", file=sys.stderr)
        sys.exit(1)

    auditor = ComplianceAuditor(strict=args.strict)
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
