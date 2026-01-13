#!/usr/bin/env python3
"""
audit-conflicts.py - Detect configuration conflicts in Claude Code projects

Checks for:
- Conflicting instructions in CLAUDE.md
- Duplicate rule definitions
- Competing hook matchers
- Skill/command overlap issues
- Permission conflicts

Usage:
    python audit-conflicts.py <project_dir> [--format json|text|md]
"""

import json
import sys
import re
import argparse
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any, Optional, Set


class ConflictsAuditor:
    """Auditor for detecting configuration conflicts."""

    def __init__(self):
        self.issues: List[Dict[str, Any]] = []

    def load_claude_md(self, project_dir: Path) -> Optional[str]:
        """Load CLAUDE.md content if exists."""
        claude_md = project_dir / "CLAUDE.md"
        if claude_md.exists():
            return claude_md.read_text()
        return None

    def load_hooks_json(self, project_dir: Path) -> Dict[str, Any]:
        """Load hooks configuration from various locations."""
        hooks = {}

        # Check plugin hooks
        plugin_hooks = project_dir / "plugin" / "hooks" / "hooks.json"
        if plugin_hooks.exists():
            try:
                with open(plugin_hooks, 'r') as f:
                    data = json.load(f)
                    hooks['plugin'] = data.get('hooks', data)
            except json.JSONDecodeError:
                pass

        # Check .claude directory hooks
        claude_hooks = project_dir / ".claude" / "hooks.json"
        if claude_hooks.exists():
            try:
                with open(claude_hooks, 'r') as f:
                    hooks['local'] = json.load(f)
            except json.JSONDecodeError:
                pass

        return hooks

    def load_settings(self, project_dir: Path) -> Dict[str, Any]:
        """Load settings from various locations."""
        settings = {}

        locations = [
            ("global", Path.home() / ".claude" / "settings.json"),
            ("project", project_dir / ".claude" / "settings.json"),
            ("local", project_dir / ".claude" / "settings.local.json"),
        ]

        for name, path in locations:
            if path.exists():
                try:
                    with open(path, 'r') as f:
                        settings[name] = json.load(f)
                except json.JSONDecodeError:
                    pass

        return settings

    def audit_claude_md_conflicts(self, content: str) -> None:
        """Check for conflicting instructions in CLAUDE.md."""
        if not content:
            return

        lines = content.split('\n')

        # Check for contradictory instructions
        contradictions = [
            (r'\b(always|must)\b.*\b(never|don\'t|do not)\b', "Contradictory always/never pattern"),
            (r'\b(never)\b.*\b(always)\b', "Contradictory never/always pattern"),
        ]

        for i, line in enumerate(lines, 1):
            line_lower = line.lower()
            for pattern, desc in contradictions:
                if re.search(pattern, line_lower):
                    self.issues.append({
                        "type": "claude_md_contradiction",
                        "severity": "warning",
                        "file": "CLAUDE.md",
                        "line": i,
                        "content": line[:100],
                        "message": f"Potential contradictory instruction: {desc}",
                        "remediation": "Review and clarify the instruction to avoid ambiguity."
                    })

        # Check for duplicate headers/sections
        headers = defaultdict(list)
        for i, line in enumerate(lines, 1):
            if line.startswith('#'):
                header = line.strip('#').strip().lower()
                headers[header].append(i)

        for header, line_nums in headers.items():
            if len(line_nums) > 1:
                self.issues.append({
                    "type": "duplicate_section",
                    "severity": "info",
                    "file": "CLAUDE.md",
                    "lines": line_nums,
                    "section": header,
                    "message": f"Duplicate section '{header}' found at lines {line_nums}",
                    "remediation": "Consolidate duplicate sections to avoid confusion."
                })

    def audit_hook_conflicts(self, hooks: Dict[str, Any]) -> None:
        """Check for competing hook matchers."""
        all_matchers: Dict[str, List[Dict]] = defaultdict(list)

        for source, hook_config in hooks.items():
            if isinstance(hook_config, dict):
                for event_type, event_hooks in hook_config.items():
                    if isinstance(event_hooks, list):
                        for hook in event_hooks:
                            matcher = hook.get('matcher', '*')
                            all_matchers[(event_type, matcher)].append({
                                "source": source,
                                "hook": hook
                            })

        # Check for duplicate matchers across sources
        for (event_type, matcher), sources in all_matchers.items():
            if len(sources) > 1:
                source_names = [s['source'] for s in sources]
                self.issues.append({
                    "type": "competing_hooks",
                    "severity": "warning",
                    "event_type": event_type,
                    "matcher": matcher,
                    "sources": source_names,
                    "message": f"Multiple hooks with same matcher '{matcher}' for {event_type}",
                    "remediation": "Ensure hooks from different sources don't conflict or duplicate logic."
                })

        # Check for overly broad matchers
        for (event_type, matcher), sources in all_matchers.items():
            if matcher == "*":
                # Check if there are also specific matchers for this event
                specific_matchers = [
                    m for (et, m), _ in all_matchers.items()
                    if et == event_type and m != "*"
                ]
                if specific_matchers:
                    self.issues.append({
                        "type": "broad_matcher_override",
                        "severity": "info",
                        "event_type": event_type,
                        "specific_matchers": specific_matchers,
                        "message": f"Wildcard matcher '*' may override specific matchers for {event_type}",
                        "remediation": "Review hook execution order and ensure wildcard doesn't interfere."
                    })

    def audit_permission_conflicts(self, settings: Dict[str, Any]) -> None:
        """Check for conflicting permission settings."""
        allow_sets: Dict[str, Set[str]] = {}
        deny_sets: Dict[str, Set[str]] = {}

        for source, config in settings.items():
            permissions = config.get('permissions', {})
            allow = permissions.get('allow', [])
            deny = permissions.get('deny', [])

            allow_sets[source] = set(allow) if isinstance(allow, list) else set()
            deny_sets[source] = set(deny) if isinstance(deny, list) else set()

        # Check for same permission in both allow and deny
        for source, allows in allow_sets.items():
            denies = deny_sets.get(source, set())
            conflicts = allows & denies
            if conflicts:
                self.issues.append({
                    "type": "permission_conflict",
                    "severity": "critical",
                    "source": source,
                    "conflicts": list(conflicts),
                    "message": f"Same permissions in both allow and deny: {conflicts}",
                    "remediation": "Remove conflicting permissions from either allow or deny list."
                })

        # Check for cross-source conflicts
        if 'project' in allow_sets and 'global' in deny_sets:
            project_allows = allow_sets['project']
            global_denies = deny_sets['global']
            overrides = project_allows & global_denies
            if overrides:
                self.issues.append({
                    "type": "permission_override",
                    "severity": "info",
                    "overrides": list(overrides),
                    "message": f"Project settings override global denies: {overrides}",
                    "remediation": "Ensure this override is intentional."
                })

    def audit_command_overlaps(self, project_dir: Path) -> None:
        """Check for overlapping command definitions."""
        commands: Dict[str, List[Path]] = defaultdict(list)

        # Search for command files
        for commands_dir in project_dir.rglob("commands"):
            if commands_dir.is_dir():
                for cmd_file in commands_dir.glob("*.md"):
                    cmd_name = cmd_file.stem
                    commands[cmd_name].append(cmd_file)

        for cmd_name, paths in commands.items():
            if len(paths) > 1:
                self.issues.append({
                    "type": "duplicate_command",
                    "severity": "warning",
                    "command": cmd_name,
                    "locations": [str(p) for p in paths],
                    "message": f"Command '{cmd_name}' defined in multiple locations",
                    "remediation": "Remove duplicate command definitions or rename to avoid conflicts."
                })

    def audit_skill_overlaps(self, project_dir: Path) -> None:
        """Check for overlapping skill definitions."""
        skills: Dict[str, List[Path]] = defaultdict(list)

        # Search for skill directories
        for skills_dir in project_dir.rglob("skills"):
            if skills_dir.is_dir():
                for skill_dir in skills_dir.iterdir():
                    if skill_dir.is_dir():
                        skill_md = skill_dir / "SKILL.md"
                        if skill_md.exists():
                            skill_name = skill_dir.name
                            skills[skill_name].append(skill_dir)

        for skill_name, paths in skills.items():
            if len(paths) > 1:
                self.issues.append({
                    "type": "duplicate_skill",
                    "severity": "warning",
                    "skill": skill_name,
                    "locations": [str(p) for p in paths],
                    "message": f"Skill '{skill_name}' defined in multiple locations",
                    "remediation": "Remove duplicate skill definitions or rename to avoid conflicts."
                })

    def run_audit(self, project_dir: Path) -> Dict[str, Any]:
        """Run all conflict audits."""
        # Load configurations
        claude_md = self.load_claude_md(project_dir)
        hooks = self.load_hooks_json(project_dir)
        settings = self.load_settings(project_dir)

        # Run all checks
        if claude_md:
            self.audit_claude_md_conflicts(claude_md)
        self.audit_hook_conflicts(hooks)
        self.audit_permission_conflicts(settings)
        self.audit_command_overlaps(project_dir)
        self.audit_skill_overlaps(project_dir)

        # Categorize by severity
        critical = [i for i in self.issues if i.get("severity") == "critical"]
        warning = [i for i in self.issues if i.get("severity") == "warning"]
        info = [i for i in self.issues if i.get("severity") == "info"]

        return {
            "audit_type": "conflicts",
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "project_dir": str(project_dir),
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
    lines.append("CONFLICTS AUDIT REPORT")
    lines.append("=" * 60)
    lines.append(f"\nProject: {result.get('project_dir')}")
    lines.append(f"Status: {result.get('status')}")

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
    lines.append("# Conflicts Audit Report\n")
    lines.append(f"**Project:** `{result.get('project_dir')}`")
    lines.append(f"**Status:** {result.get('status')}")
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
            if issue.get("file"):
                lines.append(f"**File:** `{issue.get('file')}`")
            if issue.get("line"):
                lines.append(f"**Line:** {issue.get('line')}")
            if issue.get("locations"):
                lines.append("**Locations:**")
                for loc in issue.get("locations", []):
                    lines.append(f"- `{loc}`")
            lines.append(f"\n**Remediation:** {issue.get('remediation')}\n")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Audit project for configuration conflicts")
    parser.add_argument("project_dir", help="Path to project directory")
    parser.add_argument("--format", choices=["json", "text", "md"], default="text")
    args = parser.parse_args()

    project_dir = Path(args.project_dir)
    if not project_dir.exists():
        print(f"Error: Directory not found: {project_dir}", file=sys.stderr)
        sys.exit(1)

    auditor = ConflictsAuditor()
    result = auditor.run_audit(project_dir)

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
