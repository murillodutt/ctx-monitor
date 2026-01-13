#!/usr/bin/env python3
"""
diff-engine.py - Compare traces between executions to identify regressions

Usage:
    python diff-engine.py <session1.jsonl> <session2.jsonl> [--format json|text|md]
    python diff-engine.py --traces-dir <dir> --last 2 [--format json|text|md]
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict


def load_trace(file_path: str) -> List[Dict[str, Any]]:
    """Load events from a JSONL trace file."""
    events = []
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return events


def get_tool_signature(event: Dict[str, Any]) -> str:
    """Generate a signature for a tool call."""
    tool_name = event.get("tool_name", "unknown")
    event_type = event.get("event_type", "unknown")
    return f"{event_type}:{tool_name}"


def analyze_trace(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze a trace and extract key metrics."""
    tool_calls = defaultdict(lambda: {"count": 0, "errors": 0, "statuses": []})
    event_sequence = []
    errors = []

    for event in events:
        event_type = event.get("event_type", "unknown")
        tool_name = event.get("tool_name")
        status = event.get("status")

        if tool_name:
            key = f"{event_type}:{tool_name}"
            tool_calls[key]["count"] += 1
            tool_calls[key]["statuses"].append(status)

            if status == "error":
                tool_calls[key]["errors"] += 1
                errors.append({
                    "tool": tool_name,
                    "error": event.get("error_message", "Unknown")
                })

        event_sequence.append({
            "type": event_type,
            "tool": tool_name,
            "status": status
        })

    return {
        "tool_calls": dict(tool_calls),
        "event_sequence": event_sequence,
        "total_events": len(events),
        "errors": errors,
        "error_count": len(errors)
    }


def compare_traces(trace1: Dict[str, Any], trace2: Dict[str, Any]) -> Dict[str, Any]:
    """Compare two analyzed traces and identify differences."""
    diff = {
        "added_tools": [],
        "removed_tools": [],
        "changed_tools": [],
        "error_changes": [],
        "sequence_changes": [],
        "summary": {}
    }

    tools1 = set(trace1.get("tool_calls", {}).keys())
    tools2 = set(trace2.get("tool_calls", {}).keys())

    # Added tools
    diff["added_tools"] = list(tools2 - tools1)

    # Removed tools
    diff["removed_tools"] = list(tools1 - tools2)

    # Changed tools (count or error rate)
    common_tools = tools1 & tools2
    for tool in common_tools:
        stats1 = trace1["tool_calls"][tool]
        stats2 = trace2["tool_calls"][tool]

        changes = {}
        if stats1["count"] != stats2["count"]:
            changes["count"] = {"from": stats1["count"], "to": stats2["count"]}

        if stats1["errors"] != stats2["errors"]:
            changes["errors"] = {"from": stats1["errors"], "to": stats2["errors"]}

        if changes:
            diff["changed_tools"].append({
                "tool": tool,
                "changes": changes
            })

    # Error changes
    errors1 = set(e["tool"] for e in trace1.get("errors", []))
    errors2 = set(e["tool"] for e in trace2.get("errors", []))

    new_errors = errors2 - errors1
    resolved_errors = errors1 - errors2

    if new_errors:
        diff["error_changes"].append({
            "type": "new_errors",
            "tools": list(new_errors)
        })

    if resolved_errors:
        diff["error_changes"].append({
            "type": "resolved_errors",
            "tools": list(resolved_errors)
        })

    # Sequence analysis (simplified)
    seq1 = [e["tool"] for e in trace1.get("event_sequence", []) if e["tool"]]
    seq2 = [e["tool"] for e in trace2.get("event_sequence", []) if e["tool"]]

    if seq1 != seq2:
        diff["sequence_changes"].append({
            "description": "Tool call sequence differs",
            "trace1_length": len(seq1),
            "trace2_length": len(seq2)
        })

    # Summary
    diff["summary"] = {
        "added_count": len(diff["added_tools"]),
        "removed_count": len(diff["removed_tools"]),
        "changed_count": len(diff["changed_tools"]),
        "new_errors_count": len(new_errors),
        "resolved_errors_count": len(resolved_errors),
        "has_regressions": len(new_errors) > 0 or any(
            c.get("changes", {}).get("errors", {}).get("to", 0) >
            c.get("changes", {}).get("errors", {}).get("from", 0)
            for c in diff["changed_tools"]
        )
    }

    return diff


def format_diff_text(diff: Dict[str, Any], session1_id: str, session2_id: str) -> str:
    """Format diff as plain text."""
    lines = []
    lines.append("=" * 60)
    lines.append("CTX-MONITOR TRACE DIFF")
    lines.append("=" * 60)
    lines.append(f"\nComparing: {session1_id} -> {session2_id}")

    summary = diff.get("summary", {})
    lines.append("\nSummary:")
    lines.append(f"  - Added tools: {summary.get('added_count', 0)}")
    lines.append(f"  - Removed tools: {summary.get('removed_count', 0)}")
    lines.append(f"  - Changed tools: {summary.get('changed_count', 0)}")
    lines.append(f"  - New errors: {summary.get('new_errors_count', 0)}")
    lines.append(f"  - Resolved errors: {summary.get('resolved_errors_count', 0)}")

    if summary.get("has_regressions"):
        lines.append("\n  ⚠️  REGRESSIONS DETECTED")

    if diff.get("added_tools"):
        lines.append("\n+ Added Tools:")
        for tool in diff["added_tools"]:
            lines.append(f"    + {tool}")

    if diff.get("removed_tools"):
        lines.append("\n- Removed Tools:")
        for tool in diff["removed_tools"]:
            lines.append(f"    - {tool}")

    if diff.get("changed_tools"):
        lines.append("\n~ Changed Tools:")
        for change in diff["changed_tools"]:
            tool = change["tool"]
            changes = change["changes"]
            lines.append(f"    ~ {tool}:")
            for key, val in changes.items():
                lines.append(f"        {key}: {val['from']} -> {val['to']}")

    if diff.get("error_changes"):
        lines.append("\n! Error Changes:")
        for ec in diff["error_changes"]:
            if ec["type"] == "new_errors":
                lines.append(f"    NEW ERRORS: {', '.join(ec['tools'])}")
            else:
                lines.append(f"    RESOLVED: {', '.join(ec['tools'])}")

    lines.append("\n" + "=" * 60)
    return "\n".join(lines)


def format_diff_markdown(diff: Dict[str, Any], session1_id: str, session2_id: str) -> str:
    """Format diff as Markdown."""
    lines = []
    lines.append("# CTX-Monitor Trace Diff\n")
    lines.append(f"**Comparing:** `{session1_id}` → `{session2_id}`\n")

    summary = diff.get("summary", {})

    if summary.get("has_regressions"):
        lines.append("> ⚠️ **REGRESSIONS DETECTED**\n")

    lines.append("## Summary\n")
    lines.append("| Metric | Count |")
    lines.append("|--------|-------|")
    lines.append(f"| Added tools | {summary.get('added_count', 0)} |")
    lines.append(f"| Removed tools | {summary.get('removed_count', 0)} |")
    lines.append(f"| Changed tools | {summary.get('changed_count', 0)} |")
    lines.append(f"| New errors | {summary.get('new_errors_count', 0)} |")
    lines.append(f"| Resolved errors | {summary.get('resolved_errors_count', 0)} |")

    if diff.get("added_tools"):
        lines.append("\n## Added Tools\n")
        for tool in diff["added_tools"]:
            lines.append(f"- ➕ `{tool}`")

    if diff.get("removed_tools"):
        lines.append("\n## Removed Tools\n")
        for tool in diff["removed_tools"]:
            lines.append(f"- ➖ `{tool}`")

    if diff.get("changed_tools"):
        lines.append("\n## Changed Tools\n")
        for change in diff["changed_tools"]:
            lines.append(f"\n### `{change['tool']}`")
            for key, val in change["changes"].items():
                lines.append(f"- **{key}:** {val['from']} → {val['to']}")

    if diff.get("error_changes"):
        lines.append("\n## Error Changes\n")
        for ec in diff["error_changes"]:
            if ec["type"] == "new_errors":
                lines.append(f"- 🔴 **New errors:** {', '.join(ec['tools'])}")
            else:
                lines.append(f"- 🟢 **Resolved:** {', '.join(ec['tools'])}")

    return "\n".join(lines)


def find_recent_traces(traces_dir: str, n: int = 2) -> List[Path]:
    """Find the N most recent trace files."""
    trace_path = Path(traces_dir)
    if not trace_path.exists():
        return []

    trace_files = list(trace_path.glob("session_*.jsonl"))
    trace_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    return trace_files[:n]


def main():
    parser = argparse.ArgumentParser(description="Compare ctx-monitor traces")
    parser.add_argument("session1", nargs="?", help="First session trace file")
    parser.add_argument("session2", nargs="?", help="Second session trace file")
    parser.add_argument("--traces-dir", help="Directory containing traces")
    parser.add_argument("--last", type=int, default=2, help="Compare last N traces")
    parser.add_argument("--format", choices=["json", "text", "md"], default="text")
    args = parser.parse_args()

    # Determine trace files
    if args.session1 and args.session2:
        file1 = args.session1
        file2 = args.session2
    elif args.traces_dir:
        traces = find_recent_traces(args.traces_dir, args.last)
        if len(traces) < 2:
            print("Error: Not enough traces found for comparison", file=sys.stderr)
            sys.exit(1)
        file1, file2 = traces[1], traces[0]  # Older first
    else:
        print("Error: Provide either two trace files or --traces-dir", file=sys.stderr)
        sys.exit(1)

    for f in [file1, file2]:
        if not Path(f).exists():
            print(f"Error: File not found: {f}", file=sys.stderr)
            sys.exit(1)

    # Load and analyze traces
    events1 = load_trace(str(file1))
    events2 = load_trace(str(file2))

    trace1 = analyze_trace(events1)
    trace2 = analyze_trace(events2)

    # Compare
    diff = compare_traces(trace1, trace2)

    # Get session IDs for display
    session1_id = events1[0].get("session_id", Path(file1).stem) if events1 else Path(file1).stem
    session2_id = events2[0].get("session_id", Path(file2).stem) if events2 else Path(file2).stem

    # Output
    if args.format == "json":
        print(json.dumps(diff, indent=2))
    elif args.format == "md":
        print(format_diff_markdown(diff, session1_id, session2_id))
    else:
        print(format_diff_text(diff, session1_id, session2_id))


if __name__ == "__main__":
    main()
