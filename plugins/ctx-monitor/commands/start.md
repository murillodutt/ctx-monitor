---
description: Start ctx-monitor event logging for current session
argument-hint: "[--level minimal|medium|full]"
allowed-tools:
  - Bash
  - Read
  - Write
---

# Start Context Monitor

Start event logging for the current Claude Code session. Creates trace directory and enables hooks.

## Instructions

1. Parse the optional `--level` argument:
   - `minimal`: Only session events (SessionStart, SessionEnd, Stop)
   - `medium` (default): All events with truncated payloads (500 chars)
   - `full`: Complete event capture including full tool inputs/outputs

2. Create the traces directory if it doesn't exist:
   ```bash
   mkdir -p .claude/ctx-monitor/traces
   ```

3. Create or update the session configuration file at `.claude/ctx-monitor/config.json`:
   ```json
   {
     "enabled": true,
     "level": "medium",
     "started_at": "<timestamp>",
     "session_id": "<current_session_id>"
   }
   ```

4. Confirm to the user that monitoring has started with the selected level.

## Usage Examples

- `/ctx-monitor:start` - Start with default medium level
- `/ctx-monitor:start --level full` - Start with full logging
- `/ctx-monitor:start --level minimal` - Start with minimal logging

## Notes

- Monitoring persists across tool calls within the session
- Use `/ctx-monitor:stop` to stop monitoring
- Traces are stored in `.claude/ctx-monitor/traces/`
