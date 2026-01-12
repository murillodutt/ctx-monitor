---
name: trace-interpretation
description: |
  This skill should be used when the user asks about "interpreting ctx-monitor traces", "understanding execution logs", "reading trace files", "what do ctx-monitor events mean", "debugging trace output", or needs guidance on trace file formats, event types, common failure patterns, or troubleshooting ctx-monitor output.
version: 0.3.5
---

# Trace Interpretation Guide

## Overview

ctx-monitor traces are JSONL files stored in `.claude/ctx-monitor/traces/` containing structured event records. Each line is a complete JSON object representing a single execution event.

## Event Structure

Every trace event contains these core fields:

```json
{
  "event_id": "unique-uuid",
  "session_id": "session-uuid",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "event_type": "PreToolUse|PostToolUse|SessionStart|...",
  "status": "pending|success|error",
  "tool_name": "Write|Edit|Bash|...",
  "args_preview": "truncated arguments (max 500 chars)",
  "error_message": "error details if status is error"
}
```

## Event Types

### SessionStart
Marks beginning of a Claude Code session.
- **Fields**: `session_id`, `cwd`, `timestamp`
- **Status**: `started`

### SessionEnd
Marks end of a session.
- **Fields**: `session_id`, `timestamp`
- **Status**: `ended`

### PreToolUse
Captured before a tool executes.
- **Fields**: `tool_name`, `args_preview`, `tool_use_id`
- **Status**: `pending`
- **Use**: Identify which tools were called and with what arguments

### PostToolUse
Captured after a tool completes.
- **Fields**: `tool_name`, `args_preview`, `result_preview`, `duration_ms`
- **Status**: `success` or `error`
- **Use**: Identify failures, performance issues, success rates

### SubagentStop
Captured when a subagent (Task tool) finishes.
- **Fields**: `reason`
- **Status**: `completed`
- **Use**: Track subagent lifecycle and completion reasons

### Stop
Captured when the main agent stops.
- **Fields**: `reason`
- **Status**: `completed`
- **Use**: Understand why the agent stopped (completion, error, user interrupt)

## Reading Trace Files

### File Naming
```
session_{session_id}_{timestamp}.jsonl
```

### Sessions Index
`.claude/ctx-monitor/traces/sessions.json` contains metadata:
```json
{
  "sessions": [
    {
      "session_id": "abc123",
      "started_at": "2024-01-15T10:00:00Z",
      "cwd": "/project/path",
      "event_count": 150
    }
  ]
}
```

### Parsing JSONL
```bash
# View all events
cat session_abc123.jsonl | jq .

# Filter by event type
cat session_abc123.jsonl | jq 'select(.event_type == "PostToolUse")'

# Filter errors only
cat session_abc123.jsonl | jq 'select(.status == "error")'

# Count by event type
cat session_abc123.jsonl | jq -s 'group_by(.event_type) | map({type: .[0].event_type, count: length})'
```

## Common Failure Patterns

### Intermittent Failures
**Pattern**: Same tool succeeds sometimes and fails others.
**Indicators**:
- Tool appears with both `success` and `error` status
- No clear pattern in arguments
**Causes**: Network issues, race conditions, resource contention
**Solution**: Check timing, add retries, verify external dependencies

### Hook Not Firing
**Pattern**: Expected event missing from trace.
**Indicators**:
- PreToolUse present but no PostToolUse
- SessionStart without expected hook context
**Causes**: Hook configuration error, matcher not matching, timeout
**Solution**: Verify `hooks.json`, check matcher patterns, increase timeout

### Cascade Failures
**Pattern**: One error leads to multiple subsequent errors.
**Indicators**:
- First error followed by many related errors
- Error messages reference same resource
**Causes**: Missing dependency, broken state, insufficient error handling
**Solution**: Fix root cause, add error boundaries

### Performance Degradation
**Pattern**: Increasing `duration_ms` over time.
**Indicators**:
- Same tool takes longer in later events
- Memory-related errors appear
**Causes**: Memory leak, resource exhaustion, large context
**Solution**: Profile execution, optimize tool usage, compact context

### Missing Events
**Pattern**: Gaps in event sequence.
**Indicators**:
- PreToolUse without matching PostToolUse
- SessionStart without SessionEnd
**Causes**: Crash, unhandled exception, force quit
**Solution**: Check for crashes, add error handling

## Troubleshooting Checklist

1. **Verify monitoring is active**
   - Check `.claude/ctx-monitor/config.json` has `"enabled": true`
   - Confirm hooks are loaded with `/hooks` command

2. **Check trace file exists**
   - List files in `.claude/ctx-monitor/traces/`
   - Verify session_id matches current session

3. **Analyze error distribution**
   - Count errors per tool
   - Calculate error rate percentage
   - Identify error clustering

4. **Review timeline**
   - Sort events by timestamp
   - Look for gaps or anomalies
   - Correlate with external events

5. **Compare with baseline**
   - Use `/ctx-monitor:diff` against known-good session
   - Identify what changed

## Using Analysis Tools

### Generate Report
```
/ctx-monitor:report --format md
```

### Compare Sessions
```
/ctx-monitor:diff --last 2
```

### Run Audits
```
/ctx-monitor:audit --type all
```

### Export for Support
```
/ctx-monitor:export-bundle --anonymize
```

## References

For detailed patterns and advanced techniques, see:
- `references/event-types.md` - Complete event type documentation
- `references/common-failures.md` - Expanded failure pattern catalog
