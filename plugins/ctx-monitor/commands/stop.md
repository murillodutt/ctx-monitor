---
description: Stop ctx-monitor event logging
argument-hint: "[--keep-logs]"
allowed-tools:
  - Bash
  - Read
  - Write
---

# Stop Context Monitor

Stop event logging for the current session. Optionally preserve or clean up logs.

## Instructions

1. **Check installation first**:
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/check-install.sh" "$(pwd)"
   ```
   If this returns an error, stop and show the message to the user. Do not proceed.

2. Parse the optional `--keep-logs` flag:
   - If present: Keep all trace files
   - If absent: Keep logs by default (never auto-delete)

3. Read the current configuration from `.claude/ctx-monitor/config.json`

4. Generate the timestamp using bash to ensure correct ISO 8601 format:
   ```bash
   date +"%Y-%m-%dT%H:%M:%S%z" | sed 's/\([+-][0-9][0-9]\)\([0-9][0-9]\)$/\1:\2/'
   ```
   Note: Use the actual command output, not a placeholder or approximation.

5. Update the configuration to disable monitoring:
   ```json
   {
     "enabled": false,
     "log_level": "<previous_log_level>",
     "stopped_at": "<output_from_date_command>",
     "session_id": "<session_id>"
   }
   ```

6. Report summary to user:
   - Session duration
   - Number of events captured
   - Path to trace files

## Usage Examples

- `/ctx-monitor:stop` - Stop monitoring, keep logs
- `/ctx-monitor:stop --keep-logs` - Explicitly preserve logs

## Notes

- Logs are always preserved by default for later analysis
- Use `/ctx-monitor:report` to analyze captured events
