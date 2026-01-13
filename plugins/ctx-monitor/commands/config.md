---
description: Manage ctx-monitor per-project configuration
argument-hint: "[init|status|enable|disable|set <key> <value>|clear]"
allowed-tools:
  - Bash
  - Read
  - Write
---

# Manage ctx-monitor Configuration

Configure ctx-monitor behavior for the current project.

## Instructions

1. Parse the action argument:
   - `status` (default): Show current configuration status
   - `init`: Initialize configuration for this project
   - `enable`: Enable ctx-monitor for this project
   - `disable`: Disable ctx-monitor for this project
   - `set <key> <value>`: Set a configuration value
   - `clear`: Delete all inactive session logs (keeps active session)

2. Run the config-manager script:

```bash
# Show status
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/config-manager.py "$(pwd)" status

# Initialize config
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/config-manager.py "$(pwd)" init --template ${CLAUDE_PLUGIN_ROOT}/templates/ctx-monitor.local.md

# Enable/disable
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/config-manager.py "$(pwd)" enable
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/config-manager.py "$(pwd)" disable

# Set value
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/config-manager.py "$(pwd)" set --key log_level --value minimal

# Clear inactive logs
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/config-manager.py "$(pwd)" clear
```

## Configuration File

Configuration is stored in `.claude/ctx-monitor.local.md` with YAML frontmatter:

```yaml
---
enabled: true
log_level: medium  # minimal | medium | full
events:
  - SessionStart
  - SessionEnd
  - PreToolUse
  - PostToolUse
  - Stop
  - SubagentStop
  - UserPromptSubmit
  - PreCompact
  - Notification
retention_days: 30
max_sessions: 100
anonymize_on_export: true
---
```

## Available Settings

| Key | Type | Default | Description | Status |
|-----|------|---------|-------------|--------|
| `enabled` | boolean | true | Enable/disable logging for project | Active |
| `log_level` | string | medium | Logging detail level | Active |
| `events` | array | all | Events to capture | Active |
| `retention_days` | integer | 30 | Days to keep traces | Planned |
| `max_sessions` | integer | 100 | Maximum sessions to retain | Planned |
| `anonymize_on_export` | boolean | true | Auto-anonymize exports | Active |
| `tools_filter` | array | [] | Only log these tools | Planned |
| `exclude_patterns` | array | [] | Skip events matching patterns | Planned |

## Log Levels

| Level | Events Captured | Payload Size |
|-------|-----------------|--------------|
| `minimal` | SessionStart, SessionEnd, Stop | 100 chars |
| `medium` | All events | 500 chars |
| `full` | All events | Unlimited |

## Usage Examples

```bash
# Check current status
/ctx-monitor:config status

# Initialize config for new project
/ctx-monitor:config init

# Disable logging temporarily
/ctx-monitor:config disable

# Re-enable logging
/ctx-monitor:config enable

# Change log level
/ctx-monitor:config set log_level minimal

# Set retention period
/ctx-monitor:config set retention_days 7

# Clear inactive session logs
/ctx-monitor:config clear
```

## File Location

The configuration file is created at:
```
.claude/ctx-monitor.local.md
```

This file should be added to `.gitignore` as it contains local settings.
