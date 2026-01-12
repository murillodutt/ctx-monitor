# Event Types Reference

Complete documentation of all ctx-monitor event types.

## PreToolUse

Captured immediately before a tool executes.

### Schema
```json
{
  "event_id": "string",
  "session_id": "string",
  "timestamp": "ISO8601",
  "event_type": "PreToolUse",
  "tool_name": "string",
  "args_preview": "string (max 500 chars)",
  "status": "pending"
}
```

### Common Tools
- `Read` - File reading
- `Write` - File creation
- `Edit` - File modification
- `Bash` - Shell commands
- `Glob` - File pattern matching
- `Grep` - Content search
- `Task` - Subagent delegation
- `WebFetch` - URL fetching
- `WebSearch` - Web searches

## PostToolUse

Captured immediately after a tool completes.

### Schema
```json
{
  "event_id": "string",
  "session_id": "string",
  "timestamp": "ISO8601",
  "event_type": "PostToolUse",
  "tool_name": "string",
  "args_preview": "string",
  "result_preview": "string (max 500 chars)",
  "status": "success|error",
  "duration_ms": "number",
  "error_message": "string (if error)"
}
```

### Status Values
- `success` - Tool completed without errors
- `error` - Tool failed with an error

## SessionStart

Marks the beginning of a Claude Code session.

### Schema
```json
{
  "event_id": "string",
  "session_id": "string",
  "timestamp": "ISO8601",
  "event_type": "SessionStart",
  "cwd": "string",
  "status": "started"
}
```

## SessionEnd

Marks the end of a Claude Code session.

### Schema
```json
{
  "event_id": "string",
  "session_id": "string",
  "timestamp": "ISO8601",
  "event_type": "SessionEnd",
  "status": "ended"
}
```

## Stop

Captured when the main Claude Code agent stops.

### Schema
```json
{
  "event_id": "string",
  "session_id": "string",
  "timestamp": "ISO8601",
  "event_type": "Stop",
  "reason": "string",
  "status": "completed"
}
```

### Reason Values
- `completed` - Task finished successfully
- `user_interrupt` - User interrupted execution
- `error` - Stopped due to error
- `context_limit` - Context window exhausted

## SubagentStop

Captured when a subagent (Task tool) finishes.

### Schema
```json
{
  "event_id": "string",
  "session_id": "string",
  "timestamp": "ISO8601",
  "event_type": "SubagentStop",
  "reason": "string",
  "status": "completed"
}
```

## UserPromptSubmit

Captured when the user submits a prompt to Claude Code.

### Schema
```json
{
  "event_id": "string",
  "session_id": "string",
  "timestamp": "ISO8601",
  "event_type": "UserPromptSubmit",
  "prompt_preview": "string (max 500 chars)",
  "prompt_length": "number",
  "status": "submitted"
}
```

### Use Cases
- Track user interaction patterns
- Analyze prompt complexity
- Audit conversation flow

## PreCompact

Captured before context compaction occurs (when context window is being summarized).

### Schema
```json
{
  "event_id": "string",
  "session_id": "string",
  "timestamp": "ISO8601",
  "event_type": "PreCompact",
  "transcript_path": "string",
  "status": "compacting"
}
```

### Use Cases
- Monitor context window usage
- Track compaction frequency
- Identify sessions with heavy context

## Notification

Captured when Claude Code generates a notification to the user.

### Schema
```json
{
  "event_id": "string",
  "session_id": "string",
  "timestamp": "ISO8601",
  "event_type": "Notification",
  "notification_type": "string",
  "notification_message": "string (max 300 chars)",
  "status": "notified"
}
```

### Notification Types
- `info` - Informational messages
- `warning` - Warning alerts
- `error` - Error notifications
- `success` - Success confirmations
- `permission` - Permission requests

## Event Relationships

```
SessionStart
    │
    ├── UserPromptSubmit
    │
    ├── PreToolUse (Read)
    │       └── PostToolUse (Read, success)
    │
    ├── PreToolUse (Task)
    │       ├── PreToolUse (Grep)
    │       │       └── PostToolUse (Grep, success)
    │       ├── SubagentStop
    │       └── PostToolUse (Task, success)
    │
    ├── Notification (permission)
    │
    ├── PreToolUse (Write)
    │       └── PostToolUse (Write, error)
    │
    ├── PreCompact (if context limit reached)
    │
    └── Stop
           └── SessionEnd
```

## All Events Summary

| Event | Status Values | Key Fields |
|-------|---------------|------------|
| SessionStart | started | cwd |
| SessionEnd | ended | - |
| PreToolUse | pending | tool_name, args_preview |
| PostToolUse | success, error | tool_name, result_preview, error_message |
| Stop | completed | reason |
| SubagentStop | completed | reason |
| UserPromptSubmit | submitted | prompt_preview, prompt_length |
| PreCompact | compacting | transcript_path |
| Notification | notified | notification_type, notification_message |
