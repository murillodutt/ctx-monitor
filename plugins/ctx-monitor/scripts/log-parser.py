#!/usr/bin/env python3
"""
log-parser.py - Parse and analyze ctx-monitor trace logs

Usage:
    python log-parser.py <session_file.jsonl> [--format json|text|md] [--summary]
"""

import json
import sys
import argparse
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any


def load_trace(file_path: str) -> List[Dict[str, Any]]:
    """Load events from a JSONL trace file."""
    events = []
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"Warning: Skipping malformed line: {e}", file=sys.stderr)
    return events


def analyze_events(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze events and generate statistics."""
    if not events:
        return {"error": "No events found"}

    # Basic stats
    event_types = defaultdict(int)
    tool_calls = defaultdict(lambda: {"count": 0, "errors": 0, "total_duration": 0})
    errors = []
    timeline = []

    for event in events:
        event_type = event.get("event_type", "unknown")
        event_types[event_type] += 1

        # Track tool calls
        if event_type in ["PreToolUse", "PostToolUse"]:
            tool_name = event.get("tool_name", "unknown")
            tool_calls[tool_name]["count"] += 1

            if event.get("status") == "error":
                tool_calls[tool_name]["errors"] += 1
                errors.append({
                    "timestamp": event.get("timestamp"),
                    "tool": tool_name,
                    "error": event.get("error_message", "Unknown error")
                })

            if "duration_ms" in event:
                tool_calls[tool_name]["total_duration"] += event["duration_ms"]

        # Build timeline
        timeline.append({
            "timestamp": event.get("timestamp"),
            "type": event_type,
            "tool": event.get("tool_name"),
            "status": event.get("status")
        })

    # Calculate session duration
    timestamps = [e.get("timestamp") for e in events if e.get("timestamp")]
    if len(timestamps) >= 2:
        try:
            start = datetime.fromisoformat(timestamps[0].replace('Z', '+00:00'))
            end = datetime.fromisoformat(timestamps[-1].replace('Z', '+00:00'))
            duration_seconds = (end - start).total_seconds()
        except (ValueError, TypeError):
            duration_seconds = None
    else:
        duration_seconds = None

    return {
        "session_id": events[0].get("session_id") if events else None,
        "total_events": len(events),
        "event_types": dict(event_types),
        "tool_calls": dict(tool_calls),
        "errors": errors,
        "error_count": len(errors),
        "duration_seconds": duration_seconds,
        "timeline": timeline
    }


def format_text(analysis: Dict[str, Any]) -> str:
    """Format analysis as plain text."""
    lines = []
    lines.append("=" * 60)
    lines.append("CTX-MONITOR TRACE ANALYSIS")
    lines.append("=" * 60)
    lines.append(f"\nSession ID: {analysis.get('session_id', 'Unknown')}")
    lines.append(f"Total Events: {analysis.get('total_events', 0)}")

    if analysis.get('duration_seconds'):
        lines.append(f"Duration: {analysis['duration_seconds']:.2f} seconds")

    lines.append("\nEvent Types:")
    for event_type, count in analysis.get('event_types', {}).items():
        lines.append(f"  - {event_type}: {count}")

    lines.append("\nTool Calls:")
    for tool, stats in analysis.get('tool_calls', {}).items():
        error_rate = (stats['errors'] / stats['count'] * 100) if stats['count'] > 0 else 0
        lines.append(f"  - {tool}: {stats['count']} calls ({error_rate:.1f}% errors)")

    if analysis.get('errors'):
        lines.append(f"\nErrors ({analysis.get('error_count', 0)}):")
        for error in analysis['errors'][:10]:  # Limit to 10
            lines.append(f"  [{error.get('timestamp', '?')}] {error.get('tool', '?')}: {error.get('error', '?')}")

    lines.append("\n" + "=" * 60)
    return "\n".join(lines)


def format_markdown(analysis: Dict[str, Any]) -> str:
    """Format analysis as Markdown."""
    lines = []
    lines.append("# CTX-Monitor Trace Analysis\n")
    lines.append(f"**Session ID:** `{analysis.get('session_id', 'Unknown')}`\n")
    lines.append(f"**Total Events:** {analysis.get('total_events', 0)}\n")

    if analysis.get('duration_seconds'):
        lines.append(f"**Duration:** {analysis['duration_seconds']:.2f} seconds\n")

    lines.append("## Event Types\n")
    lines.append("| Event Type | Count |")
    lines.append("|------------|-------|")
    for event_type, count in analysis.get('event_types', {}).items():
        lines.append(f"| {event_type} | {count} |")

    lines.append("\n## Tool Calls\n")
    lines.append("| Tool | Calls | Errors | Error Rate |")
    lines.append("|------|-------|--------|------------|")
    for tool, stats in analysis.get('tool_calls', {}).items():
        error_rate = (stats['errors'] / stats['count'] * 100) if stats['count'] > 0 else 0
        lines.append(f"| {tool} | {stats['count']} | {stats['errors']} | {error_rate:.1f}% |")

    if analysis.get('errors'):
        lines.append(f"\n## Errors ({analysis.get('error_count', 0)})\n")
        for error in analysis['errors'][:10]:
            lines.append(f"- **{error.get('tool', '?')}** at `{error.get('timestamp', '?')}`: {error.get('error', '?')}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Parse and analyze ctx-monitor trace logs")
    parser.add_argument("file", help="Path to JSONL trace file")
    parser.add_argument("--format", choices=["json", "text", "md"], default="text", help="Output format")
    parser.add_argument("--summary", action="store_true", help="Show only summary stats")
    args = parser.parse_args()

    if not Path(args.file).exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    events = load_trace(args.file)
    analysis = analyze_events(events)

    if args.summary:
        # Minimal summary
        summary = {
            "session_id": analysis.get("session_id"),
            "total_events": analysis.get("total_events"),
            "error_count": analysis.get("error_count"),
            "duration_seconds": analysis.get("duration_seconds")
        }
        if args.format == "json":
            print(json.dumps(summary, indent=2))
        else:
            print(f"Session: {summary['session_id']}, Events: {summary['total_events']}, Errors: {summary['error_count']}")
    else:
        if args.format == "json":
            print(json.dumps(analysis, indent=2))
        elif args.format == "md":
            print(format_markdown(analysis))
        else:
            print(format_text(analysis))


if __name__ == "__main__":
    main()
