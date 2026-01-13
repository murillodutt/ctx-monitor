#!/usr/bin/env python3
"""
audit-runner.py - Orchestrator for running modular audits

Runs one or more audit types and combines results into a unified report.

Usage:
    python audit-runner.py <project_dir> [--type all|intermittency|conflicts|tokens|compliance] [--format json|text|md]
"""

import json
import sys
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


class AuditRunner:
    """Orchestrator for running modular audits."""

    AUDIT_TYPES = ["intermittency", "conflicts", "tokens", "compliance"]

    def __init__(self, project_dir: Path, scripts_dir: Path):
        self.project_dir = project_dir
        self.scripts_dir = scripts_dir
        self.traces_dir = project_dir / ".claude" / "ctx-monitor" / "traces"

    def run_audit(self, audit_type: str) -> Dict[str, Any]:
        """Run a single audit type and return results."""
        script_name = f"audit-{audit_type}.py"
        script_path = self.scripts_dir / script_name

        if not script_path.exists():
            return {
                "audit_type": audit_type,
                "status": "error",
                "message": f"Audit script not found: {script_name}"
            }

        # Determine the correct argument based on audit type
        if audit_type == "conflicts":
            target_path = str(self.project_dir)
        else:
            target_path = str(self.traces_dir)

        try:
            result = subprocess.run(
                [sys.executable, str(script_path), target_path, "--format", "json"],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode in [0, 1]:  # 0 = success, 1 = issues found
                return json.loads(result.stdout)
            else:
                return {
                    "audit_type": audit_type,
                    "status": "error",
                    "message": result.stderr or "Unknown error",
                    "exit_code": result.returncode
                }

        except subprocess.TimeoutExpired:
            return {
                "audit_type": audit_type,
                "status": "error",
                "message": "Audit timed out after 60 seconds"
            }
        except json.JSONDecodeError as e:
            return {
                "audit_type": audit_type,
                "status": "error",
                "message": f"Invalid JSON output: {e}"
            }
        except Exception as e:
            return {
                "audit_type": audit_type,
                "status": "error",
                "message": str(e)
            }

    def run_all(self, types: List[str]) -> Dict[str, Any]:
        """Run multiple audits and combine results."""
        results = {}
        total_summary = {
            "total_issues": 0,
            "critical": 0,
            "warning": 0,
            "info": 0
        }

        for audit_type in types:
            result = self.run_audit(audit_type)
            results[audit_type] = result

            # Aggregate summary
            if result.get("status") == "completed":
                summary = result.get("summary", {})
                total_summary["total_issues"] += summary.get("total_issues", 0)
                total_summary["critical"] += summary.get("critical", 0)
                total_summary["warning"] += summary.get("warning", 0)
                total_summary["info"] += summary.get("info", 0)

        return {
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "project_dir": str(self.project_dir),
            "audits_run": types,
            "combined_summary": total_summary,
            "results": results
        }


def format_text(report: Dict[str, Any]) -> str:
    """Format combined report as plain text."""
    lines = []
    lines.append("=" * 70)
    lines.append("CTX-MONITOR AUDIT REPORT")
    lines.append("=" * 70)
    lines.append(f"\nProject: {report.get('project_dir')}")
    lines.append(f"Timestamp: {report.get('timestamp')}")
    lines.append(f"Audits Run: {', '.join(report.get('audits_run', []))}")

    summary = report.get("combined_summary", {})
    lines.append(f"\n{'─' * 70}")
    lines.append("COMBINED SUMMARY")
    lines.append(f"{'─' * 70}")
    lines.append(f"Total Issues: {summary.get('total_issues', 0)}")
    lines.append(f"  🔴 Critical: {summary.get('critical', 0)}")
    lines.append(f"  🟡 Warning:  {summary.get('warning', 0)}")
    lines.append(f"  🔵 Info:     {summary.get('info', 0)}")

    for audit_type, result in report.get("results", {}).items():
        lines.append(f"\n{'─' * 70}")
        lines.append(f"{audit_type.upper()} AUDIT")
        lines.append(f"{'─' * 70}")

        if result.get("status") == "error":
            lines.append(f"  ❌ Error: {result.get('message')}")
            continue

        audit_summary = result.get("summary", {})
        lines.append(f"  Status: {result.get('status')}")
        lines.append(f"  Issues: {audit_summary.get('total_issues', 0)}")

        for issue in result.get("issues", [])[:5]:  # First 5
            severity = issue.get("severity", "info").upper()
            lines.append(f"\n  [{severity}] {issue.get('type')}")
            lines.append(f"    {issue.get('message')}")

        if len(result.get("issues", [])) > 5:
            lines.append(f"\n  ... and {len(result.get('issues', [])) - 5} more issues")

    lines.append(f"\n{'=' * 70}")
    return "\n".join(lines)


def format_markdown(report: Dict[str, Any]) -> str:
    """Format combined report as Markdown."""
    lines = []
    lines.append("# CTX-Monitor Audit Report\n")
    lines.append(f"**Project:** `{report.get('project_dir')}`")
    lines.append(f"**Timestamp:** {report.get('timestamp')}")
    lines.append(f"**Audits Run:** {', '.join(report.get('audits_run', []))}\n")

    summary = report.get("combined_summary", {})
    lines.append("## Combined Summary\n")
    lines.append("| Severity | Count |")
    lines.append("|----------|-------|")
    lines.append(f"| 🔴 Critical | {summary.get('critical', 0)} |")
    lines.append(f"| 🟡 Warning | {summary.get('warning', 0)} |")
    lines.append(f"| 🔵 Info | {summary.get('info', 0)} |")
    lines.append(f"| **Total** | **{summary.get('total_issues', 0)}** |")

    for audit_type, result in report.get("results", {}).items():
        lines.append(f"\n## {audit_type.title()} Audit\n")

        if result.get("status") == "error":
            lines.append(f"❌ **Error:** {result.get('message')}\n")
            continue

        audit_summary = result.get("summary", {})
        lines.append(f"**Status:** {result.get('status')}")
        lines.append(f"**Issues Found:** {audit_summary.get('total_issues', 0)}\n")

        if result.get("issues"):
            lines.append("### Issues\n")
            for issue in result.get("issues", [])[:10]:  # First 10
                severity = issue.get("severity", "info").upper()
                emoji = {"CRITICAL": "🔴", "WARNING": "🟡", "INFO": "🔵"}.get(severity, "⚪")
                lines.append(f"- {emoji} **[{severity}]** {issue.get('type')}: {issue.get('message')}")

            if len(result.get("issues", [])) > 10:
                lines.append(f"\n*...and {len(result.get('issues', [])) - 10} more issues*")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Run modular audits on ctx-monitor traces")
    parser.add_argument("project_dir", help="Path to project directory")
    parser.add_argument("--type", choices=["all"] + AuditRunner.AUDIT_TYPES,
                        default="all", help="Audit type to run")
    parser.add_argument("--format", choices=["json", "text", "md"], default="text")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    if not project_dir.exists():
        print(f"Error: Directory not found: {project_dir}", file=sys.stderr)
        sys.exit(1)

    # Determine scripts directory (same as this script)
    scripts_dir = Path(__file__).parent

    runner = AuditRunner(project_dir, scripts_dir)

    # Determine which audits to run
    if args.type == "all":
        audit_types = AuditRunner.AUDIT_TYPES
    else:
        audit_types = [args.type]

    report = runner.run_all(audit_types)

    if args.format == "json":
        print(json.dumps(report, indent=2))
    elif args.format == "md":
        print(format_markdown(report))
    else:
        print(format_text(report))

    # Exit with error code if critical issues found
    if report.get("combined_summary", {}).get("critical", 0) > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
