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

1. **Check installation first**:
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/check-install.sh" "$(pwd)"
   ```
   If this returns an error, stop and show the message to the user. Do not proceed.

2. Parse the optional `--level` argument:
   - `minimal`: Only session events (SessionStart, SessionEnd, Stop)
   - `medium` (default): All events with truncated payloads (500 chars)
   - `full`: Complete event capture including full tool inputs/outputs

3. Create the traces directory if it doesn't exist:
   ```bash
   mkdir -p .claude/ctx-monitor/traces
   ```

4. Generate the timestamp using bash to ensure correct ISO 8601 format:
   ```bash
   date +"%Y-%m-%dT%H:%M:%S%z" | sed 's/\([+-][0-9][0-9]\)\([0-9][0-9]\)$/\1:\2/'
   ```
   Note: Use the actual command output, not a placeholder or approximation.

5. Create or update the session configuration file at `.claude/ctx-monitor/config.json`:
   ```json
   {
     "enabled": true,
     "level": "medium",
     "started_at": "<output_from_date_command>",
     "session_id": "<current_session_id>"
   }
   ```

6. Confirm to the user that monitoring has started with the selected level.

## Usage Examples

- `/ctx-monitor:start` - Start with default medium level
- `/ctx-monitor:start --level full` - Start with full logging
- `/ctx-monitor:start --level minimal` - Start with minimal logging

## Notes

- Monitoring persists across tool calls within the session
- Use `/ctx-monitor:stop` to stop monitoring
- Traces are stored in `.claude/ctx-monitor/traces/`
