---
description: Generate execution report from ctx-monitor traces
argument-hint: "[--session <id>] [--format text|json|md]"
allowed-tools:
  - Bash
  - Read
  - Glob
  - Grep
---

# Generate Trace Report

Analyze captured trace events and generate a comprehensive execution report.

## Instructions

1. Parse arguments:
   - `--session <id>`: Specific session ID (default: most recent)
   - `--format text|json|md`: Output format (default: text)

2. Locate trace files in `.claude/ctx-monitor/traces/`

3. If no session specified, find the most recent trace file

4. Use the log-parser script to analyze traces:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/log-parser.py <trace_file> --format <format>
   ```

5. Present the report to the user with:
   - Session summary (ID, duration, event count)
   - Tool call statistics (count, error rate per tool)
   - Error list with timestamps and messages
   - Timeline of key events

6. **IMPORTANT**: After presenting the report, proactively offer analysis suggestions:
   - Point out any anomalies (high error rates, unusual patterns)
   - Suggest using the trace-analyzer agent for deeper investigation
   - Recommend `/ctx-monitor:audit` if issues are detected

## Usage Examples

- `/ctx-monitor:report` - Report for most recent session
- `/ctx-monitor:report --session abc123` - Report for specific session
- `/ctx-monitor:report --format md` - Markdown formatted report

## Report Sections

1. **Summary**: Basic session metrics
2. **Event Types**: Breakdown by event type
3. **Tool Calls**: Statistics per tool
4. **Errors**: List of errors with context
5. **Recommendations**: Suggested next steps
