---
# ctx-monitor per-project configuration
# Copy this file to your project: .claude/ctx-monitor.local.md

enabled: true
log_level: medium  # minimal | medium | full

# Event filtering (capture only these events)
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

# Retention settings [PLANNED - not yet enforced]
retention_days: 30
max_sessions: 100

# Privacy settings
anonymize_on_export: true
redact_patterns:
  - "api[_-]?key[=:].*"
  - "token[=:].*"
  - "password[=:].*"
  - "secret[=:].*"
  - "bearer\\s+[a-zA-Z0-9._-]+"

# Tool filtering [PLANNED - not yet implemented]
# (only log these tools, empty = all)
tools_filter: []

# Exclude patterns [PLANNED - not yet implemented]
# (don't log events matching these)
exclude_patterns: []
---

# Project-specific ctx-monitor configuration

This file configures ctx-monitor behavior for this project.

## Log Levels

- **minimal**: Only session lifecycle events (SessionStart, SessionEnd, Stop)
- **medium**: All events with truncated payloads (500 chars) - Default
- **full**: Complete event capture with full tool inputs/outputs

## Enabling/Disabling

Set `enabled: false` to disable ctx-monitor for this project without uninstalling.

## Event Filtering

Remove events from the `events` list to stop capturing them.

## Tool Filtering

Add tool names to `tools_filter` to only log specific tools:
```yaml
tools_filter:
  - Bash
  - Write
  - Edit
```

## Exclude Patterns

Add regex patterns to skip logging certain events:
```yaml
exclude_patterns:
  - ".*test.*"
  - ".*tmp.*"
```
