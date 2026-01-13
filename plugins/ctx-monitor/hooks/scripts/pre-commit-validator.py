#!/usr/bin/env python3
"""
Pre-commit validation hook for ctx-monitor.

Validates code quality before allowing git commit/push operations:
- Runs ruff linter with auto-fix
- Checks for bare except clauses
- Validates Python syntax
- Checks JSON files

Exit codes:
- 0: Validation passed, allow operation
- 2: Validation failed, block operation (shows stderr to Claude)
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path


def get_project_root() -> Path:
    """Get project root from environment or input."""
    # Try environment variable first
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if project_dir:
        return Path(project_dir)

    # Fallback to cwd from input
    try:
        input_data = json.load(sys.stdin)
        return Path(input_data.get("cwd", os.getcwd()))
    except (json.JSONDecodeError, KeyError):
        return Path(os.getcwd())


def run_ruff_check(project_root: Path) -> tuple[bool, str]:
    """Run ruff linter with auto-fix."""
    scripts_dir = project_root / "plugins" / "ctx-monitor" / "scripts"

    if not scripts_dir.exists():
        return True, ""

    try:
        # First try to auto-fix
        subprocess.run(
            ["python3", "-m", "ruff", "check", str(scripts_dir), "--fix"],
            capture_output=True,
            text=True,
            timeout=30
        )

        # Then check for remaining issues
        result = subprocess.run(
            ["python3", "-m", "ruff", "check", str(scripts_dir)],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            return False, f"Ruff found issues:\n{result.stdout}"

        return True, ""
    except subprocess.TimeoutExpired:
        return False, "Ruff check timed out"
    except FileNotFoundError:
        # ruff not installed, skip check
        return True, ""


def check_bare_except(project_root: Path) -> tuple[bool, str]:
    """Check for bare except clauses."""
    scripts_dir = project_root / "plugins" / "ctx-monitor" / "scripts"

    if not scripts_dir.exists():
        return True, ""

    issues = []
    pattern = re.compile(r"^\s*except\s*:\s*$", re.MULTILINE)

    for py_file in scripts_dir.glob("*.py"):
        try:
            content = py_file.read_text()
            matches = pattern.findall(content)
            if matches:
                # Find line numbers
                for i, line in enumerate(content.split("\n"), 1):
                    if re.match(r"^\s*except\s*:\s*$", line):
                        issues.append(f"{py_file.name}:{i}: bare except clause")
        except (IOError, UnicodeDecodeError):
            continue

    # Also check shell scripts with embedded Python
    for sh_file in scripts_dir.glob("*.sh"):
        try:
            content = sh_file.read_text()
            matches = pattern.findall(content)
            if matches:
                for i, line in enumerate(content.split("\n"), 1):
                    if re.match(r"^\s*except\s*:\s*$", line):
                        issues.append(f"{sh_file.name}:{i}: bare except in heredoc")
        except (IOError, UnicodeDecodeError):
            continue

    if issues:
        return False, "Bare except clauses found:\n" + "\n".join(f"  - {i}" for i in issues)

    return True, ""


def validate_python_syntax(project_root: Path) -> tuple[bool, str]:
    """Validate Python syntax for all scripts."""
    scripts_dir = project_root / "plugins" / "ctx-monitor" / "scripts"

    if not scripts_dir.exists():
        return True, ""

    issues = []

    for py_file in scripts_dir.glob("*.py"):
        result = subprocess.run(
            ["python3", "-m", "py_compile", str(py_file)],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            issues.append(f"{py_file.name}: {result.stderr.strip()}")

    if issues:
        return False, "Python syntax errors:\n" + "\n".join(f"  - {i}" for i in issues)

    return True, ""


def validate_json_files(project_root: Path) -> tuple[bool, str]:
    """Validate JSON configuration files."""
    json_files = [
        project_root / "plugins" / "ctx-monitor" / ".claude-plugin" / "plugin.json",
        project_root / "plugins" / "ctx-monitor" / "hooks" / "hooks.json",
        project_root / ".claude-plugin" / "marketplace.json",
    ]

    issues = []

    for json_file in json_files:
        if json_file.exists():
            try:
                with open(json_file) as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                issues.append(f"{json_file.name}: {e}")

    if issues:
        return False, "JSON validation errors:\n" + "\n".join(f"  - {i}" for i in issues)

    return True, ""


def main() -> int:
    """Main validation entry point."""
    # Read input from stdin
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        # If no valid JSON, might be called directly
        input_data = {}

    # Check if this is a git commit or push command
    tool_input = input_data.get("tool_input", {})
    command = tool_input.get("command", "")

    # Only validate for git commit/push
    if not re.search(r"\bgit\s+(commit|push)\b", command):
        return 0  # Not a git operation, allow

    project_root = get_project_root()

    # Run all validations
    validations = [
        ("Ruff Lint", run_ruff_check),
        ("Bare Except", check_bare_except),
        ("Python Syntax", validate_python_syntax),
        ("JSON Files", validate_json_files),
    ]

    all_passed = True
    messages = []

    for name, validator in validations:
        passed, message = validator(project_root)
        if not passed:
            all_passed = False
            messages.append(f"[FAIL] {name}:\n{message}")
        else:
            messages.append(f"[OK] {name}")

    if not all_passed:
        print("Pre-commit validation failed!", file=sys.stderr)
        print("", file=sys.stderr)
        for msg in messages:
            if msg.startswith("[FAIL]"):
                print(msg, file=sys.stderr)
        print("", file=sys.stderr)
        print("Fix the issues above before committing.", file=sys.stderr)
        print("Run: python3 -m ruff check --fix plugins/ctx-monitor/scripts/", file=sys.stderr)
        return 2  # Block the operation

    # All validations passed
    return 0


if __name__ == "__main__":
    sys.exit(main())
