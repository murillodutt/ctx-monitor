#!/usr/bin/env python3
"""
config-manager.py - Manage ctx-monitor per-project configuration

Handles reading, writing, and validating ctx-monitor configuration
from .claude/ctx-monitor.local.md files.

Usage:
    python config-manager.py <project_dir> <action> [options]

Actions:
    status    - Show current configuration status
    init      - Initialize configuration for project
    enable    - Enable ctx-monitor for project
    disable   - Disable ctx-monitor for project
    get       - Get a configuration value
    set       - Set a configuration value
    validate  - Validate configuration file
"""

import json
import sys
import re
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import yaml


class ConfigManager:
    """Manager for ctx-monitor per-project configuration."""

    CONFIG_FILENAME = "ctx-monitor.local.md"
    DEFAULT_CONFIG = {
        "enabled": True,
        "log_level": "medium",
        "events": [
            "SessionStart", "SessionEnd", "PreToolUse", "PostToolUse",
            "Stop", "SubagentStop", "UserPromptSubmit", "PreCompact", "Notification"
        ],
        "retention_days": 30,
        "max_sessions": 100,
        "anonymize_on_export": True,
        "redact_patterns": [
            r"api[_-]?key[=:].*",
            r"token[=:].*",
            r"password[=:].*",
            r"secret[=:].*",
            r"bearer\s+[a-zA-Z0-9._-]+"
        ],
        "tools_filter": [],
        "exclude_patterns": []
    }

    VALID_LOG_LEVELS = {"minimal", "medium", "full"}
    VALID_EVENTS = {
        "SessionStart", "SessionEnd", "PreToolUse", "PostToolUse",
        "Stop", "SubagentStop", "UserPromptSubmit", "PreCompact", "Notification"
    }

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.config_dir = project_dir / ".claude"
        self.config_file = self.config_dir / self.CONFIG_FILENAME
        self.runtime_config = self.config_dir / "ctx-monitor" / "config.json"

    def config_exists(self) -> bool:
        """Check if configuration file exists."""
        return self.config_file.exists()

    def load_config(self) -> Tuple[Dict[str, Any], str]:
        """Load configuration from markdown file with YAML frontmatter."""
        if not self.config_file.exists():
            return self.DEFAULT_CONFIG.copy(), ""

        content = self.config_file.read_text()

        # Parse YAML frontmatter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                try:
                    config = yaml.safe_load(parts[1]) or {}
                    markdown = parts[2].strip()
                    # Merge with defaults
                    merged = self.DEFAULT_CONFIG.copy()
                    merged.update(config)
                    return merged, markdown
                except yaml.YAMLError:
                    pass

        return self.DEFAULT_CONFIG.copy(), content

    def save_config(self, config: Dict[str, Any], markdown: str = "") -> None:
        """Save configuration to markdown file with YAML frontmatter."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Generate YAML frontmatter
        yaml_content = yaml.dump(config, default_flow_style=False, sort_keys=False)

        if not markdown:
            markdown = """# Project-specific ctx-monitor configuration

This file configures ctx-monitor behavior for this project.
Edit the YAML frontmatter above to customize settings.
"""

        content = f"---\n{yaml_content}---\n\n{markdown}"
        self.config_file.write_text(content)

    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []

        # Validate log_level
        if config.get("log_level") not in self.VALID_LOG_LEVELS:
            errors.append(f"Invalid log_level: {config.get('log_level')}. Valid: {self.VALID_LOG_LEVELS}")

        # Validate events
        events = config.get("events", [])
        invalid_events = set(events) - self.VALID_EVENTS
        if invalid_events:
            errors.append(f"Invalid events: {invalid_events}. Valid: {self.VALID_EVENTS}")

        # Validate retention_days
        retention = config.get("retention_days", 30)
        if not isinstance(retention, int) or retention < 1:
            errors.append(f"retention_days must be a positive integer, got: {retention}")

        # Validate max_sessions
        max_sessions = config.get("max_sessions", 100)
        if not isinstance(max_sessions, int) or max_sessions < 1:
            errors.append(f"max_sessions must be a positive integer, got: {max_sessions}")

        # Validate redact_patterns (check regex syntax)
        for pattern in config.get("redact_patterns", []):
            try:
                re.compile(pattern)
            except re.error as e:
                errors.append(f"Invalid regex in redact_patterns: {pattern} - {e}")

        # Validate exclude_patterns
        for pattern in config.get("exclude_patterns", []):
            try:
                re.compile(pattern)
            except re.error as e:
                errors.append(f"Invalid regex in exclude_patterns: {pattern} - {e}")

        return errors

    def get_status(self) -> Dict[str, Any]:
        """Get current configuration status."""
        config, _ = self.load_config()
        errors = self.validate_config(config)

        # Check runtime status
        runtime_active = False
        runtime_session = None
        if self.runtime_config.exists():
            try:
                runtime = json.loads(self.runtime_config.read_text())
                runtime_active = runtime.get("enabled", False)
                runtime_session = runtime.get("session_id")
            except json.JSONDecodeError:
                pass

        return {
            "config_exists": self.config_exists(),
            "config_path": str(self.config_file),
            "enabled": config.get("enabled", True),
            "log_level": config.get("log_level", "medium"),
            "events_count": len(config.get("events", [])),
            "runtime_active": runtime_active,
            "runtime_session": runtime_session,
            "validation_errors": errors,
            "is_valid": len(errors) == 0
        }

    def init_config(self, template_path: Optional[Path] = None) -> bool:
        """Initialize configuration for project."""
        if self.config_exists():
            return False

        if template_path and template_path.exists():
            # Copy from template
            content = template_path.read_text()
            self.config_dir.mkdir(parents=True, exist_ok=True)
            self.config_file.write_text(content)
        else:
            # Use defaults
            self.save_config(self.DEFAULT_CONFIG)

        return True

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable ctx-monitor for project."""
        config, markdown = self.load_config()
        config["enabled"] = enabled
        self.save_config(config, markdown)

    def get_value(self, key: str) -> Any:
        """Get a configuration value."""
        config, _ = self.load_config()
        return config.get(key)

    def set_value(self, key: str, value: Any) -> bool:
        """Set a configuration value."""
        config, markdown = self.load_config()

        # Type conversion for common fields
        if key == "enabled":
            value = str(value).lower() in ("true", "1", "yes")
        elif key in ("retention_days", "max_sessions"):
            value = int(value)
        elif key == "log_level":
            if value not in self.VALID_LOG_LEVELS:
                return False
        elif key == "events":
            if isinstance(value, str):
                value = [v.strip() for v in value.split(",")]

        config[key] = value
        errors = self.validate_config(config)

        if errors:
            return False

        self.save_config(config, markdown)
        return True

    def should_log_event(self, event_type: str, tool_name: Optional[str] = None) -> bool:
        """Check if an event should be logged based on configuration."""
        config, _ = self.load_config()

        # Check if enabled
        if not config.get("enabled", True):
            return False

        # Check event filter
        events = config.get("events", [])
        if events and event_type not in events:
            return False

        # Check tool filter
        tools_filter = config.get("tools_filter", [])
        if tools_filter and tool_name and tool_name not in tools_filter:
            return False

        return True

    def get_log_level_config(self) -> Dict[str, Any]:
        """Get logging configuration based on log level."""
        config, _ = self.load_config()
        level = config.get("log_level", "medium")

        if level == "minimal":
            return {
                "events": ["SessionStart", "SessionEnd", "Stop"],
                "truncate_preview": 100,
                "include_args": False
            }
        elif level == "full":
            return {
                "events": list(self.VALID_EVENTS),
                "truncate_preview": 0,  # No truncation
                "include_args": True
            }
        else:  # medium (default)
            return {
                "events": list(self.VALID_EVENTS),
                "truncate_preview": 500,
                "include_args": True
            }

    def clear_inactive_logs(self, keep_active: bool = True) -> Dict[str, Any]:
        """
        Clear inactive session logs.

        Args:
            keep_active: If True, keeps the currently active session (if any).

        Returns:
            Dict with cleared files count and freed space.
        """
        traces_dir = self.config_dir / "ctx-monitor" / "traces"
        if not traces_dir.exists():
            return {"cleared": 0, "freed_bytes": 0, "kept": 0, "files": []}

        # Get active session ID from runtime config
        active_session = None
        if keep_active and self.runtime_config.exists():
            try:
                runtime = json.loads(self.runtime_config.read_text())
                if runtime.get("enabled", False):
                    active_session = runtime.get("session_id")
            except json.JSONDecodeError:
                pass

        cleared_files = []
        kept_files = []
        freed_bytes = 0

        # Find all session files
        for trace_file in traces_dir.glob("session_*.jsonl"):
            session_id = trace_file.stem.replace("session_", "")

            # Skip active session
            if active_session and session_id == active_session:
                kept_files.append(trace_file.name)
                continue

            # Check if session has ended (has SessionEnd event)
            is_ended = False
            try:
                with open(trace_file, "r") as f:
                    for line in f:
                        try:
                            event = json.loads(line)
                            if event.get("event_type") == "SessionEnd":
                                is_ended = True
                                break
                        except json.JSONDecodeError:
                            continue
            except IOError:
                continue

            # Only clear ended sessions
            if is_ended:
                file_size = trace_file.stat().st_size
                trace_file.unlink()
                cleared_files.append(trace_file.name)
                freed_bytes += file_size
            else:
                kept_files.append(trace_file.name)

        # Update sessions.json index
        sessions_index = traces_dir / "sessions.json"
        if sessions_index.exists() and cleared_files:
            try:
                with open(sessions_index, "r") as f:
                    index_data = json.load(f)

                # Remove cleared sessions from index
                cleared_ids = {f.replace("session_", "").replace(".jsonl", "") for f in cleared_files}
                index_data["sessions"] = [
                    s for s in index_data.get("sessions", [])
                    if s.get("session_id") not in cleared_ids
                ]

                with open(sessions_index, "w") as f:
                    json.dump(index_data, f, indent=2)
            except (json.JSONDecodeError, IOError):
                pass

        return {
            "cleared": len(cleared_files),
            "freed_bytes": freed_bytes,
            "kept": len(kept_files),
            "files": cleared_files
        }


def format_status(status: Dict[str, Any]) -> str:
    """Format status as human-readable text."""
    lines = []
    lines.append("=" * 50)
    lines.append("CTX-MONITOR CONFIGURATION STATUS")
    lines.append("=" * 50)

    lines.append(f"\nConfig File: {status['config_path']}")
    lines.append(f"Config Exists: {'✓' if status['config_exists'] else '✗'}")
    lines.append(f"Enabled: {'✓' if status['enabled'] else '✗'}")
    lines.append(f"Log Level: {status['log_level']}")
    lines.append(f"Events Configured: {status['events_count']}")
    lines.append(f"Runtime Active: {'✓' if status['runtime_active'] else '✗'}")

    if status['runtime_session']:
        lines.append(f"Current Session: {status['runtime_session']}")

    if status['validation_errors']:
        lines.append("\n⚠️ Validation Errors:")
        for error in status['validation_errors']:
            lines.append(f"  - {error}")
    else:
        lines.append("\n✓ Configuration is valid")

    lines.append("\n" + "=" * 50)
    return "\n".join(lines)


def format_clear_result(result: Dict[str, Any]) -> str:
    """Format clear result as human-readable text."""
    lines = []
    lines.append("=" * 50)
    lines.append("CTX-MONITOR CLEAR INACTIVE LOGS")
    lines.append("=" * 50)

    if result["cleared"] == 0:
        lines.append("\nNo inactive sessions to clear.")
        lines.append(f"Sessions kept: {result['kept']}")
    else:
        freed_kb = result["freed_bytes"] / 1024
        freed_str = f"{freed_kb:.1f} KB" if freed_kb < 1024 else f"{freed_kb/1024:.2f} MB"

        lines.append(f"\n✓ Cleared {result['cleared']} inactive session(s)")
        lines.append(f"  Freed: {freed_str}")
        lines.append(f"  Kept: {result['kept']} session(s)")

        if result["files"]:
            lines.append("\nCleared files:")
            for f in result["files"][:10]:  # Show max 10
                lines.append(f"  - {f}")
            if len(result["files"]) > 10:
                lines.append(f"  ... and {len(result['files']) - 10} more")

    lines.append("\n" + "=" * 50)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Manage ctx-monitor per-project configuration")
    parser.add_argument("project_dir", help="Path to project directory")
    parser.add_argument("action", choices=["status", "init", "enable", "disable", "get", "set", "validate", "check-event", "clear"],
                        help="Action to perform")
    parser.add_argument("--key", help="Configuration key (for get/set)")
    parser.add_argument("--value", help="Configuration value (for set)")
    parser.add_argument("--template", help="Path to template file (for init)")
    parser.add_argument("--event", help="Event type to check (for check-event)")
    parser.add_argument("--tool", help="Tool name to check (for check-event)")
    parser.add_argument("--format", choices=["json", "text"], default="text")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    if not project_dir.exists():
        print(f"Error: Directory not found: {project_dir}", file=sys.stderr)
        sys.exit(1)

    manager = ConfigManager(project_dir)

    if args.action == "status":
        status = manager.get_status()
        if args.format == "json":
            print(json.dumps(status, indent=2))
        else:
            print(format_status(status))

    elif args.action == "init":
        template = Path(args.template) if args.template else None
        if manager.init_config(template):
            print(f"✓ Configuration initialized at: {manager.config_file}")
        else:
            print(f"Configuration already exists at: {manager.config_file}")
            sys.exit(1)

    elif args.action == "enable":
        manager.set_enabled(True)
        print("✓ ctx-monitor enabled for this project")

    elif args.action == "disable":
        manager.set_enabled(False)
        print("✓ ctx-monitor disabled for this project")

    elif args.action == "get":
        if not args.key:
            print("Error: --key required for get action", file=sys.stderr)
            sys.exit(1)
        value = manager.get_value(args.key)
        if args.format == "json":
            print(json.dumps({"key": args.key, "value": value}))
        else:
            print(f"{args.key}: {value}")

    elif args.action == "set":
        if not args.key or args.value is None:
            print("Error: --key and --value required for set action", file=sys.stderr)
            sys.exit(1)
        if manager.set_value(args.key, args.value):
            print(f"✓ Set {args.key} = {args.value}")
        else:
            print(f"✗ Failed to set {args.key}. Check value validity.", file=sys.stderr)
            sys.exit(1)

    elif args.action == "validate":
        config, _ = manager.load_config()
        errors = manager.validate_config(config)
        if errors:
            print("Validation errors:")
            for error in errors:
                print(f"  - {error}")
            sys.exit(1)
        else:
            print("✓ Configuration is valid")

    elif args.action == "check-event":
        if not args.event:
            print("Error: --event required for check-event action", file=sys.stderr)
            sys.exit(1)
        should_log = manager.should_log_event(args.event, args.tool)
        if args.format == "json":
            print(json.dumps({"event": args.event, "tool": args.tool, "should_log": should_log}))
        else:
            print(f"Log {args.event}: {'✓ Yes' if should_log else '✗ No'}")
        sys.exit(0 if should_log else 1)

    elif args.action == "clear":
        result = manager.clear_inactive_logs(keep_active=True)
        if args.format == "json":
            print(json.dumps(result, indent=2))
        else:
            print(format_clear_result(result))


if __name__ == "__main__":
    main()
