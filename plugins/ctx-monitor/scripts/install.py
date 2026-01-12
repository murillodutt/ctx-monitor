#!/usr/bin/env python3
"""
install.py - Installation, configuration, and doctor script for ctx-monitor

Handles plugin installation, verification, repair, and automatic problem fixing.

Usage:
    python install.py <project_dir> <action>

Actions:
    install - Full installation
    check   - Verify installation only
    repair  - Force reinstall/repair
    doctor  - Diagnose and fix problems automatically
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Minimum Python version
MIN_PYTHON = (3, 7)

# Claude directories
CLAUDE_HOME = Path.home() / ".claude"
PLUGINS_CACHE = CLAUDE_HOME / "plugins" / "cache"
INSTALLED_PLUGINS_FILE = CLAUDE_HOME / "plugins" / "installed_plugins.json"


class Colors:
    """ANSI color codes."""
    RESET = "\033[0m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    @classmethod
    def success(cls, text: str) -> str:
        return f"{cls.GREEN}✓{cls.RESET} {text}"

    @classmethod
    def error(cls, text: str) -> str:
        return f"{cls.RED}✗{cls.RESET} {text}"

    @classmethod
    def warning(cls, text: str) -> str:
        return f"{cls.YELLOW}⚠{cls.RESET} {text}"

    @classmethod
    def info(cls, text: str) -> str:
        return f"{cls.BLUE}ℹ{cls.RESET} {text}"

    @classmethod
    def step(cls, text: str) -> str:
        return f"{cls.CYAN}→{cls.RESET} {text}"


class InstallResult:
    """Result of an installation step."""

    def __init__(self):
        self.success = True
        self.messages: List[str] = []
        self.warnings: List[str] = []
        self.errors: List[str] = []

    def add_success(self, msg: str):
        self.messages.append(Colors.success(msg))

    def add_warning(self, msg: str):
        self.warnings.append(Colors.warning(msg))

    def add_error(self, msg: str):
        self.errors.append(Colors.error(msg))
        self.success = False

    def add_info(self, msg: str):
        self.messages.append(Colors.info(msg))


class Installer:
    """ctx-monitor installer."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.plugin_dir = self._find_plugin_dir()
        self.claude_dir = project_dir / ".claude"
        self.monitor_dir = self.claude_dir / "ctx-monitor"
        self.traces_dir = self.monitor_dir / "traces"
        self.config_file = self.claude_dir / "ctx-monitor.local.md"
        self.status_file = self.monitor_dir / ".installed"

    def _find_plugin_dir(self) -> Optional[Path]:
        """Find the ctx-monitor plugin directory."""
        # Check if we're running from within the plugin
        script_path = Path(__file__).resolve()
        if "ctx-monitor" in str(script_path):
            # Navigate up to plugin root
            for parent in script_path.parents:
                if (parent / ".claude-plugin").exists():
                    return parent

        # Check common locations
        candidates = [
            self.project_dir / "plugins" / "ctx-monitor",
            Path.home() / ".claude" / "plugins" / "cache" / "dutt-plugins-official" / "ctx-monitor",
        ]

        for path in candidates:
            if path.exists() and (path / ".claude-plugin").exists():
                return path

        return None

    def check_python_version(self, result: InstallResult) -> bool:
        """Check Python version meets minimum requirements."""
        current = sys.version_info[:2]

        if current >= MIN_PYTHON:
            result.add_success(f"Python {current[0]}.{current[1]} detected (>= {MIN_PYTHON[0]}.{MIN_PYTHON[1]} required)")
            return True
        else:
            result.add_error(f"Python {current[0]}.{current[1]} detected, but {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ required")
            return False

    def check_plugin_location(self, result: InstallResult) -> bool:
        """Verify plugin is accessible."""
        if self.plugin_dir and self.plugin_dir.exists():
            result.add_success(f"Plugin found at: {self.plugin_dir}")
            return True
        else:
            result.add_error("Plugin directory not found")
            result.add_info("Install via: /plugin install ctx-monitor@dutt-plugins-official")
            return False

    def create_directories(self, result: InstallResult) -> bool:
        """Create required directory structure."""
        try:
            # Create .claude directory
            self.claude_dir.mkdir(exist_ok=True)

            # Create ctx-monitor directory
            self.monitor_dir.mkdir(exist_ok=True)

            # Create traces directory
            self.traces_dir.mkdir(exist_ok=True)

            result.add_success("Directory structure created")
            result.add_info(f"  └─ {self.monitor_dir}")
            result.add_info(f"     └─ traces/")
            return True

        except PermissionError as e:
            result.add_error(f"Permission denied creating directories: {e}")
            return False
        except Exception as e:
            result.add_error(f"Failed to create directories: {e}")
            return False

    def create_config(self, result: InstallResult, force: bool = False) -> bool:
        """Create default configuration file."""
        if self.config_file.exists() and not force:
            result.add_info(f"Configuration already exists: {self.config_file.name}")
            return True

        default_config = """---
enabled: true
log_level: medium
retention_days: 30
anonymize_on_export: true
auto_start: false
---

# ctx-monitor Configuration

This file configures ctx-monitor behavior for this project.

## Settings

- **enabled**: Enable/disable monitoring (true/false)
- **log_level**: Detail level - low, medium, high
- **retention_days**: Days to keep trace files
- **anonymize_on_export**: Redact sensitive data in exports
- **auto_start**: Start monitoring automatically on session start

## Notes

- Traces are stored in `.claude/ctx-monitor/traces/`
- Use `/ctx-monitor:start` to begin monitoring
- Use `/ctx-monitor:dashboard` to view metrics
"""

        try:
            self.config_file.write_text(default_config)
            result.add_success(f"Configuration created: {self.config_file.name}")
            return True
        except Exception as e:
            result.add_error(f"Failed to create configuration: {e}")
            return False

    def validate_hooks(self, result: InstallResult) -> bool:
        """Validate hooks configuration."""
        if not self.plugin_dir:
            result.add_warning("Cannot validate hooks - plugin directory not found")
            return True  # Not a fatal error

        hooks_file = self.plugin_dir / "hooks" / "hooks.json"

        if not hooks_file.exists():
            result.add_error(f"Hooks configuration not found: {hooks_file}")
            return False

        try:
            with open(hooks_file) as f:
                hooks_data = json.load(f)

            hooks_config = hooks_data.get("hooks", {})
            expected_events = [
                "SessionStart", "SessionEnd", "PreToolUse", "PostToolUse",
                "UserPromptSubmit", "SubagentStop", "Stop", "PreCompact", "Notification"
            ]

            found_events = [e for e in expected_events if e in hooks_config]
            result.add_success(f"Hooks validated: {len(found_events)}/{len(expected_events)} events configured")

            return True

        except json.JSONDecodeError as e:
            result.add_error(f"Invalid hooks.json: {e}")
            return False
        except Exception as e:
            result.add_error(f"Failed to validate hooks: {e}")
            return False

    def validate_event_logger(self, result: InstallResult) -> bool:
        """Test the event logger script."""
        if not self.plugin_dir:
            result.add_warning("Cannot test event logger - plugin directory not found")
            return True

        logger_script = self.plugin_dir / "hooks" / "scripts" / "event-logger.sh"

        if not logger_script.exists():
            result.add_error(f"Event logger not found: {logger_script}")
            return False

        # Check if script is executable
        if not os.access(logger_script, os.X_OK):
            try:
                os.chmod(logger_script, 0o755)
                result.add_info("Made event-logger.sh executable")
            except Exception as e:
                result.add_warning(f"Could not make script executable: {e}")

        result.add_success("Event logger script validated")
        return True

    def create_status_file(self, result: InstallResult) -> bool:
        """Create installation status file."""
        try:
            status = {
                "installed_at": datetime.now().isoformat(),
                "version": "0.3.5",
                "plugin_dir": str(self.plugin_dir) if self.plugin_dir else None,
                "project_dir": str(self.project_dir)
            }

            self.status_file.write_text(json.dumps(status, indent=2))
            result.add_success("Installation status recorded")
            return True

        except Exception as e:
            result.add_warning(f"Could not create status file: {e}")
            return True  # Non-fatal

    def check_installation(self) -> Tuple[bool, InstallResult]:
        """Check if ctx-monitor is properly installed."""
        result = InstallResult()

        # Check directories
        if not self.monitor_dir.exists():
            result.add_error("ctx-monitor directory not found")
            result.add_info("Run /ctx-monitor:install to set up")
            return False, result

        if not self.traces_dir.exists():
            result.add_error("Traces directory not found")
            return False, result

        # Check status file
        if not self.status_file.exists():
            result.add_warning("Installation status file missing")
            result.add_info("Run /ctx-monitor:install --repair to fix")

        # Check config
        if not self.config_file.exists():
            result.add_warning("Configuration file missing")

        # Validate hooks
        self.validate_hooks(result)

        # Validate event logger
        self.validate_event_logger(result)

        if result.success:
            result.add_success("Installation verified")

        return result.success, result

    def install(self, force: bool = False) -> Tuple[bool, InstallResult]:
        """Perform full installation."""
        result = InstallResult()

        print()
        print("┌──────────────────────────────────────────────────────────────────────────────┐")
        print("│  CTX-MONITOR INSTALLATION                                                    │")
        print("└──────────────────────────────────────────────────────────────────────────────┘")
        print()

        # Step 1: Check Python
        print(Colors.step("Checking Python version..."))
        if not self.check_python_version(result):
            return False, result

        # Step 2: Check plugin location
        print(Colors.step("Locating plugin..."))
        self.check_plugin_location(result)

        # Step 3: Create directories
        print(Colors.step("Creating directory structure..."))
        if not self.create_directories(result):
            return False, result

        # Step 4: Create config
        print(Colors.step("Setting up configuration..."))
        if not self.create_config(result, force=force):
            return False, result

        # Step 5: Validate hooks
        print(Colors.step("Validating hooks..."))
        self.validate_hooks(result)

        # Step 6: Validate event logger
        print(Colors.step("Testing event logger..."))
        self.validate_event_logger(result)

        # Step 7: Create status file
        print(Colors.step("Recording installation status..."))
        self.create_status_file(result)

        return result.success, result

    def repair(self) -> Tuple[bool, InstallResult]:
        """Repair existing installation."""
        print()
        print("┌──────────────────────────────────────────────────────────────────────────────┐")
        print("│  CTX-MONITOR REPAIR                                                          │")
        print("└──────────────────────────────────────────────────────────────────────────────┘")
        print()

        return self.install(force=True)

    def doctor(self) -> Tuple[bool, InstallResult]:
        """Diagnose and fix problems automatically."""
        result = InstallResult()

        print()
        print("┌──────────────────────────────────────────────────────────────────────────────┐")
        print("│  CTX-MONITOR DOCTOR                                                          │")
        print("└──────────────────────────────────────────────────────────────────────────────┘")
        print()

        problems_found = 0
        problems_fixed = 0

        # Check 1: Orphaned cache references
        print(Colors.step("Checking for orphaned cache references..."))
        orphaned = self._find_orphaned_cache_refs()
        if orphaned:
            problems_found += len(orphaned)
            for ref in orphaned:
                result.add_warning(f"Orphaned cache: {ref}")

            # Fix: Remove orphaned references
            fixed = self._fix_orphaned_cache_refs(orphaned)
            if fixed:
                problems_fixed += len(orphaned)
                result.add_success(f"Cleaned {len(orphaned)} orphaned cache reference(s)")
        else:
            result.add_success("No orphaned cache references")

        # Check 2: Empty/corrupted cache directories
        print(Colors.step("Checking cache directories..."))
        empty_caches = self._find_empty_caches()
        if empty_caches:
            problems_found += len(empty_caches)
            for cache in empty_caches:
                result.add_warning(f"Empty cache directory: {cache}")

            # Fix: Remove empty cache directories
            for cache in empty_caches:
                try:
                    shutil.rmtree(cache)
                    problems_fixed += 1
                except Exception as e:
                    result.add_error(f"Could not remove {cache}: {e}")

            if problems_fixed:
                result.add_success(f"Removed {len(empty_caches)} empty cache directory(ies)")
        else:
            result.add_success("Cache directories OK")

        # Check 3: Broken symlinks
        print(Colors.step("Checking for broken symlinks..."))
        broken_links = self._find_broken_symlinks()
        if broken_links:
            problems_found += len(broken_links)
            for link in broken_links:
                result.add_warning(f"Broken symlink: {link}")
                try:
                    link.unlink()
                    problems_fixed += 1
                except Exception:
                    pass
            result.add_success(f"Removed {len(broken_links)} broken symlink(s)")
        else:
            result.add_success("No broken symlinks")

        # Check 4: Script permissions
        print(Colors.step("Checking script permissions..."))
        scripts_fixed = self._fix_script_permissions()
        if scripts_fixed:
            problems_found += scripts_fixed
            problems_fixed += scripts_fixed
            result.add_success(f"Fixed permissions on {scripts_fixed} script(s)")
        else:
            result.add_success("Script permissions OK")

        # Check 5: Local installation
        print(Colors.step("Checking local installation..."))
        if not self.monitor_dir.exists():
            problems_found += 1
            result.add_warning("ctx-monitor not installed locally")
            result.add_info("Run /ctx-monitor:install to set up")
        else:
            result.add_success("Local installation OK")

        # Check 6: Configuration file
        print(Colors.step("Checking configuration..."))
        if not self.config_file.exists():
            problems_found += 1
            self.create_config(result)
            problems_fixed += 1
        else:
            result.add_success("Configuration file OK")

        # Summary
        print()
        if problems_found == 0:
            result.add_success("No problems found!")
        elif problems_fixed == problems_found:
            result.add_success(f"All {problems_found} problem(s) fixed!")
        elif problems_fixed > 0:
            result.add_warning(f"Fixed {problems_fixed}/{problems_found} problems")
        else:
            result.add_error(f"Found {problems_found} problem(s), could not fix automatically")

        return result.success, result

    def _find_orphaned_cache_refs(self) -> List[str]:
        """Find references to plugins whose cache doesn't exist."""
        orphaned = []

        if not INSTALLED_PLUGINS_FILE.exists():
            return orphaned

        try:
            with open(INSTALLED_PLUGINS_FILE) as f:
                data = json.load(f)

            plugins = data.get("plugins", {})
            for plugin_id, installs in plugins.items():
                if "ctx-monitor" in plugin_id.lower() or "dutt" in plugin_id.lower():
                    for install in installs:
                        install_path = Path(install.get("installPath", ""))
                        if install_path and not install_path.exists():
                            orphaned.append(plugin_id)
                            break

        except Exception:
            pass

        return orphaned

    def _fix_orphaned_cache_refs(self, orphaned: List[str]) -> bool:
        """Remove orphaned plugin references from installed_plugins.json."""
        if not INSTALLED_PLUGINS_FILE.exists():
            return False

        try:
            with open(INSTALLED_PLUGINS_FILE) as f:
                data = json.load(f)

            plugins = data.get("plugins", {})
            modified = False

            for plugin_id in orphaned:
                if plugin_id in plugins:
                    del plugins[plugin_id]
                    modified = True

            if modified:
                with open(INSTALLED_PLUGINS_FILE, 'w') as f:
                    json.dump(data, f, indent=4)
                return True

        except Exception:
            pass

        return False

    def _find_empty_caches(self) -> List[Path]:
        """Find empty or corrupted cache directories."""
        empty = []

        if not PLUGINS_CACHE.exists():
            return empty

        for marketplace_dir in PLUGINS_CACHE.iterdir():
            if not marketplace_dir.is_dir():
                continue

            # Check each plugin cache
            for item in marketplace_dir.iterdir():
                if item.is_dir():
                    # Check if it's empty or only has .DS_Store
                    contents = list(item.iterdir())
                    real_contents = [c for c in contents if c.name != ".DS_Store"]
                    if not real_contents:
                        empty.append(item)

        return empty

    def _find_broken_symlinks(self) -> List[Path]:
        """Find broken symbolic links in the project."""
        broken = []

        if self.claude_dir.exists():
            for item in self.claude_dir.rglob("*"):
                if item.is_symlink() and not item.exists():
                    broken.append(item)

        return broken

    def _fix_script_permissions(self) -> int:
        """Fix permissions on shell scripts."""
        fixed = 0

        if not self.plugin_dir:
            return fixed

        scripts_dir = self.plugin_dir / "hooks" / "scripts"
        if scripts_dir.exists():
            for script in scripts_dir.glob("*.sh"):
                if not os.access(script, os.X_OK):
                    try:
                        os.chmod(script, 0o755)
                        fixed += 1
                    except Exception:
                        pass

        return fixed


def print_result(result: InstallResult):
    """Print installation result."""
    print()

    for msg in result.messages:
        print(f"  {msg}")

    for warn in result.warnings:
        print(f"  {warn}")

    for err in result.errors:
        print(f"  {err}")

    print()

    if result.success:
        print(f"  {Colors.GREEN}{Colors.BOLD}Installation complete!{Colors.RESET}")
        print()
        print(f"  {Colors.info('Next steps:')}")
        print(f"    1. Run {Colors.CYAN}/ctx-monitor:start{Colors.RESET} to begin monitoring")
        print(f"    2. Perform some operations")
        print(f"    3. Run {Colors.CYAN}/ctx-monitor:dashboard{Colors.RESET} to view metrics")
    else:
        print(f"  {Colors.RED}{Colors.BOLD}Installation failed!{Colors.RESET}")
        print()
        print(f"  {Colors.info('Please fix the errors above and try again.')}")

    print()


def main():
    parser = argparse.ArgumentParser(description="ctx-monitor installer and doctor")
    parser.add_argument("project_dir", help="Project directory path")
    parser.add_argument(
        "action",
        choices=["install", "check", "repair", "doctor"],
        default="install",
        nargs="?",
        help="Action to perform"
    )

    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()

    if not project_dir.exists():
        print(Colors.error(f"Project directory not found: {project_dir}"))
        sys.exit(1)

    installer = Installer(project_dir)

    if args.action == "check":
        print()
        print("┌──────────────────────────────────────────────────────────────────────────────┐")
        print("│  CTX-MONITOR STATUS CHECK                                                    │")
        print("└──────────────────────────────────────────────────────────────────────────────┘")

        success, result = installer.check_installation()
        print_result(result)
        sys.exit(0 if success else 1)

    elif args.action == "repair":
        success, result = installer.repair()
        print_result(result)
        sys.exit(0 if success else 1)

    elif args.action == "doctor":
        success, result = installer.doctor()
        print_result(result)
        sys.exit(0 if success else 1)

    else:  # install
        # Run doctor first to clean up any issues
        print(Colors.step("Running pre-install diagnostics..."))
        installer.doctor()
        print()

        # Then install
        success, result = installer.install()
        print_result(result)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
