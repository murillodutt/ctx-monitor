# ctx-monitor Plugin Complete Manual

**Context Oracle - Observability and Auditing for Claude Code CLI**

---

## Document Information

| Field | Value |
|-------|-------|
| Version | 0.3.5 |
| Date | 2026-01-12 |
| Author | Murillo Dutt |
| Organization | Dutt Yeshua Technology Ltd |
| License | MIT |

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Core Concepts](#2-core-concepts)
3. [Plugin Architecture](#3-plugin-architecture)
4. [Installation and Configuration](#4-installation-and-configuration)
5. [Available Commands](#5-available-commands)
6. [Event System](#6-event-system)
7. [Trace Analysis](#7-trace-analysis)
8. [Modular Audits](#8-modular-audits)
9. [Execution Comparison](#9-execution-comparison)
10. [Diagnostic Export](#10-diagnostic-export)
11. [trace-analyzer Agent](#11-trace-analyzer-agent)
12. [trace-interpretation Skill](#12-trace-interpretation-skill)
13. [Common Failure Patterns](#13-common-failure-patterns)
14. [Practical Use Cases](#14-practical-use-cases)
15. [Troubleshooting](#15-troubleshooting)
16. [Technical Reference](#16-technical-reference)

---

## 1. Introduction

### 1.1 What is ctx-monitor?

ctx-monitor (Context Oracle) is an observability and auditing plugin developed specifically for Claude Code CLI. Its fundamental purpose is to provide complete visibility into what happens during Claude Code session execution, enabling developers and context engineering teams to understand, debug, and optimize their implementations.

In an environment where AI agents execute multiple tools, delegate tasks to subagents, trigger hooks, and apply skills, the ability to track every event becomes essential. ctx-monitor fills this gap by capturing, storing, and analyzing every event in the execution pipeline.

### 1.2 Why Use ctx-monitor?

The complexity of Claude Code-based systems grows exponentially when we combine:

- **Multiple plugins** with their own commands, agents, and skills
- **Event-driven hooks** that intercept and modify behaviors
- **Autonomous subagents** that execute delegated tasks
- **Per-project configurations** with specific rules

Without proper observability tooling, identifying the root cause of unexpected behaviors becomes a frustrating and time-consuming task. ctx-monitor solves this problem by offering:

1. **End-to-End Traceability**: Every tool called, every hook triggered, every subagent created and terminated is recorded with precise timestamps.

2. **Intermittent Failure Detection**: Hooks that don't fire consistently, tools that fail sporadically, and error patterns that emerge only under certain conditions are automatically identified.

3. **Regression Comparison**: By capturing traces from sessions at different times, it's possible to compare behaviors and identify when and where regressions were introduced.

4. **Compliance Auditing**: Verify that executions follow expected patterns, that output formats are correct, and that there are no configuration conflicts.

5. **Diagnostic Bundles**: Create anonymized packages containing traces, configurations, and metadata for sharing with support teams or for issue documentation.

### 1.3 Target Audience

This manual is intended for:

- **Context Engineers**: Professionals who design and optimize prompts, hooks, and Claude Code configurations
- **Plugin Developers**: Extension creators who need to debug complex behaviors
- **Support Teams**: Technicians who analyze problems reported by users
- **Quality Auditors**: Those responsible for ensuring AI systems operate as specified

---

## 2. Core Concepts

### 2.1 Trace

A trace is the complete chronological record of all events that occurred during a Claude Code session. It is stored in JSONL (JSON Lines) format, where each line represents an individual event.

```
Claude Code Session
     |
     v
[SessionStart] -> [UserPromptSubmit] -> [PreToolUse] -> [PostToolUse] -> ... -> [Stop] -> [SessionEnd]
     |                    |                  |                |                    |           |
     v                    v                  v                v                    v           v
  Trace Line 1      Trace Line 2       Trace Line 3     Trace Line 4         Trace Line N   Trace Line N+1
```

Each trace line contains:
- Unique event identifier
- Session identifier
- Timestamp in ISO8601 format
- Event type
- Operation status
- Event-type specific data

### 2.2 Session

A session represents a complete instance of interaction with Claude Code, from its initialization to its termination. Each session has a unique identifier (UUID) that correlates all events belonging to it.

### 2.3 Event

An event is an atomic tracking unit. ctx-monitor captures nine distinct event types, each representing a specific moment in the execution lifecycle:

| Event | Capture Moment |
|-------|----------------|
| SessionStart | Start of Claude Code session |
| SessionEnd | End of session |
| PreToolUse | Before a tool executes |
| PostToolUse | After a tool completes |
| Stop | When the main agent stops |
| SubagentStop | When a subagent terminates |
| UserPromptSubmit | When the user sends a prompt |
| PreCompact | Before context compaction |
| Notification | When a notification is generated |

### 2.4 Log Level

ctx-monitor offers three detail levels for event capture:

| Level | Events Captured | Payload Size |
|-------|-----------------|--------------|
| minimal | SessionStart, SessionEnd, Stop | 100 characters |
| medium | All events | 500 characters |
| full | All events | Unlimited |

The level choice directly impacts the volume of data stored and the granularity of possible analysis.

---

## 3. Plugin Architecture

### 3.1 Directory Structure

```
ctx-monitor/
├── .claude-plugin/
│   └── plugin.json              # Plugin manifest
├── commands/                     # Available slash commands
│   ├── start.md                 # /ctx-monitor:start
│   ├── stop.md                  # /ctx-monitor:stop
│   ├── report.md                # /ctx-monitor:report
│   ├── audit.md                 # /ctx-monitor:audit
│   ├── diff.md                  # /ctx-monitor:diff
│   ├── config.md                # /ctx-monitor:config
│   └── export-bundle.md         # /ctx-monitor:export-bundle
├── agents/
│   └── trace-analyzer.md        # Specialized analysis agent
├── skills/
│   └── trace-interpretation/
│       ├── SKILL.md             # Trace interpretation skill
│       └── references/
│           ├── event-types.md   # Event types documentation
│           └── common-failures.md # Failure patterns catalog
├── hooks/
│   ├── hooks.json               # Capture hooks configuration
│   └── scripts/
│       └── event-logger.sh      # Event logging script
├── scripts/                      # Python analysis scripts
│   ├── log-parser.py            # Log parser
│   ├── audit-runner.py          # Audit orchestrator
│   ├── audit-intermittency.py   # Intermittency audit
│   ├── audit-conflicts.py       # Conflicts audit
│   ├── audit-tokens.py          # Tokens audit
│   ├── audit-compliance.py      # Compliance audit
│   ├── diff-engine.py           # Comparison engine
│   ├── bundle-creator.py        # Bundle creator
│   ├── anonymizer.py            # Data anonymizer
│   └── config-manager.py        # Configuration manager
├── templates/
│   └── ctx-monitor.local.md     # Configuration template
└── README.md                     # Summary documentation
```

### 3.2 Data Storage

ctx-monitor data is stored in each project, in the directory:

```
.claude/ctx-monitor/
├── config.json                   # Active configuration
├── traces/
│   ├── sessions.json            # Sessions index
│   ├── session_<uuid>.jsonl     # Session trace
│   └── ...
└── ctx-monitor.local.md         # Project configuration
```

This approach ensures that each project maintains its own execution history, enabling contextualized analysis and comparisons within the correct scope.

### 3.3 Data Flow

```
Claude Code Event
        |
        v
   Hook Capture
   (event-logger.sh)
        |
        v
   Write JSONL
   (traces/session_*.jsonl)
        |
        v
   Index Session
   (traces/sessions.json)
        |
        v
   Available for Analysis
   (report, audit, diff)
```

### 3.4 Hooks System

ctx-monitor uses Claude Code's hooks system to intercept events. All nine event types are captured through a centralized hook:

```json
{
  "description": "Context Oracle event logging hooks",
  "hooks": {
    "SessionStart": [{ "matcher": "*", "hooks": [{"type": "command", "command": "bash ${CLAUDE_PLUGIN_ROOT}/hooks/scripts/event-logger.sh"}] }],
    "SessionEnd": [{ "matcher": "*", "hooks": [...] }],
    "PreToolUse": [{ "matcher": "*", "hooks": [...] }],
    "PostToolUse": [{ "matcher": "*", "hooks": [...] }],
    "SubagentStop": [{ "matcher": "*", "hooks": [...] }],
    "Stop": [{ "matcher": "*", "hooks": [...] }],
    "UserPromptSubmit": [{ "matcher": "*", "hooks": [...] }],
    "PreCompact": [{ "matcher": "*", "hooks": [...] }],
    "Notification": [{ "matcher": "*", "hooks": [...] }]
  }
}
```

The `"*"` matcher ensures that all events of each type are captured, regardless of tool or context.

---

## 4. Installation and Configuration

### 4.1 Prerequisites

Before installing ctx-monitor, ensure your environment meets the following requirements:

- Claude Code CLI version 2.1 or higher
- Python 3.7 or higher (for analysis scripts)
- Write access to the project directory

### 4.2 Installation via Marketplace

The recommended installation method is through the official marketplace:

```bash
/plugin install ctx-monitor@dutt-plugins-official
```

After installation, restart Claude Code for hooks to be loaded.

### 4.3 Installation via curl

For quick installation in a new environment:

```bash
curl -sSL https://raw.githubusercontent.com/murillodutt/ctx-monitor/main/install.sh | bash
```

### 4.4 Initial Configuration

After installation, initialize the configuration for your project:

```bash
/ctx-monitor:config init
```

This command creates the `.claude/ctx-monitor.local.md` file with default settings.

### 4.5 Configuration File

Configuration is stored in YAML frontmatter format:

```yaml
---
enabled: true
log_level: medium
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

### 4.6 Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| enabled | boolean | true | Enable or disable logging |
| log_level | string | medium | Detail level (minimal, medium, full) |
| events | array | all | List of events to capture |
| retention_days | integer | 30 | Days to keep traces |
| max_sessions | integer | 100 | Maximum number of retained sessions |
| anonymize_on_export | boolean | true | Automatically anonymize on export |
| tools_filter | array | [] | Filter only specific tools |
| exclude_patterns | array | [] | Patterns to ignore |

### 4.7 Gitignore

Add the following entries to your project's `.gitignore`:

```
.claude/ctx-monitor/traces/
.claude/ctx-monitor.local.md
```

This prevents local traces and specific configurations from being committed to the repository.

---

## 5. Available Commands

ctx-monitor provides seven slash commands, all prefixed with the plugin namespace.

### 5.1 /ctx-monitor:start

**Purpose**: Start event monitoring for the current session.

**Syntax**:
```bash
/ctx-monitor:start [--level minimal|medium|full]
```

**Parameters**:
- `--level`: Sets the capture detail level

**Behavior**:
1. Creates the traces directory if it doesn't exist
2. Generates a new session_id
3. Updates the configuration file with `enabled: true`
4. Confirms to the user that monitoring has started

**Example**:
```bash
# Start with default level (medium)
/ctx-monitor:start

# Start with full capture
/ctx-monitor:start --level full

# Start with minimal capture (session only)
/ctx-monitor:start --level minimal
```

### 5.2 /ctx-monitor:stop

**Purpose**: Stop monitoring and preserve logs.

**Syntax**:
```bash
/ctx-monitor:stop [--keep-logs]
```

**Parameters**:
- `--keep-logs`: Ensures explicit log preservation (default: logs always preserved)

**Behavior**:
1. Updates configuration with `enabled: false`
2. Records stop timestamp
3. Reports session summary to user

**Example**:
```bash
/ctx-monitor:stop
```

### 5.3 /ctx-monitor:report

**Purpose**: Generate analytical report of captured events.

**Syntax**:
```bash
/ctx-monitor:report [--session <id>] [--format text|json|md]
```

**Parameters**:
- `--session`: Specific session ID (default: most recent)
- `--format`: Output format (default: text)

**Behavior**:
1. Locates trace files
2. Executes the log-parser.py script
3. Presents structured summary containing:
   - Session metrics
   - Statistics per tool
   - Error list
   - Key events timeline

**Example**:
```bash
# Report for most recent session
/ctx-monitor:report

# Report for specific session in markdown
/ctx-monitor:report --session abc123 --format md
```

### 5.4 /ctx-monitor:audit

**Purpose**: Execute modular audits on traces.

**Syntax**:
```bash
/ctx-monitor:audit [--type all|intermittency|conflicts|tokens|compliance] [--format text|json|md]
```

**Parameters**:
- `--type`: Audit type (default: all)
- `--format`: Output format (default: text)

**Audit Types**:

| Type | Description |
|------|-------------|
| intermittency | Detects intermittent failures and unstable patterns |
| conflicts | Identifies configuration conflicts |
| tokens | Analyzes token usage efficiency |
| compliance | Verifies format compliance |
| all | Runs all audits |

**Example**:
```bash
# Complete audit
/ctx-monitor:audit

# Only check intermittencies
/ctx-monitor:audit --type intermittency

# Compliance audit in JSON
/ctx-monitor:audit --type compliance --format json
```

### 5.5 /ctx-monitor:diff

**Purpose**: Compare traces between sessions to identify regressions.

**Syntax**:
```bash
/ctx-monitor:diff <session1> <session2>
/ctx-monitor:diff --last <n>
```

**Parameters**:
- `<session1> <session2>`: IDs of two sessions to compare
- `--last <n>`: Compare the last N sessions

**Behavior**:
1. Locates specified traces
2. Executes the diff-engine.py script
3. Presents categorized differences:
   - Added/removed tools
   - Error rate changes
   - Sequence changes

**Example**:
```bash
# Compare two specific sessions
/ctx-monitor:diff abc123 xyz789

# Compare the two most recent sessions
/ctx-monitor:diff --last 2
```

### 5.6 /ctx-monitor:config

**Purpose**: Manage ctx-monitor configuration.

**Syntax**:
```bash
/ctx-monitor:config [init|status|enable|disable|set <key> <value>]
```

**Actions**:
- `status`: Shows current configuration (default)
- `init`: Initializes configuration for the project
- `enable`: Enables monitoring
- `disable`: Disables monitoring
- `set <key> <value>`: Sets a configuration value

**Example**:
```bash
# Check status
/ctx-monitor:config status

# Initialize for new project
/ctx-monitor:config init

# Change log level
/ctx-monitor:config set log_level minimal

# Set retention
/ctx-monitor:config set retention_days 7
```

### 5.7 /ctx-monitor:export-bundle

**Purpose**: Create diagnostic package for sharing.

**Syntax**:
```bash
/ctx-monitor:export-bundle [--anonymize] [--include-config] [--output <path>]
```

**Parameters**:
- `--anonymize`: Anonymize sensitive data (default: true)
- `--no-anonymize`: Keep data without anonymization
- `--include-config`: Include configuration files (default: true)
- `--output`: Custom path for the bundle

**Bundle Contents**:
```
ctx-monitor-bundle.zip
├── traces/              # JSONL trace files
│   ├── session_*.jsonl
│   └── sessions.json
├── config.json          # Configuration snapshot
├── environment.json     # System/tool versions
└── report.md            # Summary report
```

**Anonymization**:
The anonymization process removes:
- API keys and tokens
- Passwords and secrets
- Paths with usernames
- Email addresses
- Internal IP addresses

**Example**:
```bash
# Default bundle (anonymized, with config)
/ctx-monitor:export-bundle

# Bundle without anonymization
/ctx-monitor:export-bundle --no-anonymize

# Bundle at custom location
/ctx-monitor:export-bundle --output ./diagnostics/issue-123.zip
```

---

## 6. Event System

### 6.1 SessionStart

Captured when a new Claude Code session starts.

**Schema**:
```json
{
  "event_id": "uuid",
  "session_id": "uuid",
  "timestamp": "2024-01-15T10:00:00.000Z",
  "event_type": "SessionStart",
  "cwd": "/path/to/project",
  "status": "started"
}
```

**Utility**: Identify session starts, correlate with working environment.

### 6.2 SessionEnd

Captured when the session ends.

**Schema**:
```json
{
  "event_id": "uuid",
  "session_id": "uuid",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "event_type": "SessionEnd",
  "status": "ended"
}
```

**Utility**: Calculate session duration, identify abrupt terminations.

### 6.3 PreToolUse

Captured immediately before a tool executes.

**Schema**:
```json
{
  "event_id": "uuid",
  "session_id": "uuid",
  "timestamp": "2024-01-15T10:05:00.000Z",
  "event_type": "PreToolUse",
  "tool_name": "Write",
  "args_preview": "file_path: /src/main.py, content: ...",
  "status": "pending"
}
```

**Common Tracked Tools**:
- Read - File reading
- Write - File creation
- Edit - File modification
- Bash - Shell commands
- Glob - File pattern matching
- Grep - Content search
- Task - Subagent delegation
- WebFetch - URL fetching
- WebSearch - Web searches

**Utility**: Know which tools were invoked and with what arguments.

### 6.4 PostToolUse

Captured after a tool completes.

**Schema**:
```json
{
  "event_id": "uuid",
  "session_id": "uuid",
  "timestamp": "2024-01-15T10:05:01.000Z",
  "event_type": "PostToolUse",
  "tool_name": "Write",
  "args_preview": "file_path: /src/main.py",
  "result_preview": "File written successfully",
  "status": "success",
  "duration_ms": 150,
  "error_message": null
}
```

**Possible Status Values**:
- `success`: Tool completed without errors
- `error`: Tool failed

**Utility**: Identify failures, measure performance, calculate error rates.

### 6.5 Stop

Captured when the main agent decides to stop.

**Schema**:
```json
{
  "event_id": "uuid",
  "session_id": "uuid",
  "timestamp": "2024-01-15T10:25:00.000Z",
  "event_type": "Stop",
  "reason": "completed",
  "status": "completed"
}
```

**Stop Reasons**:
- `completed`: Task finished successfully
- `user_interrupt`: User interrupted
- `error`: Stopped due to error
- `context_limit`: Context window exhausted

**Utility**: Understand why the agent ended execution.

### 6.6 SubagentStop

Captured when a subagent (Task tool) terminates.

**Schema**:
```json
{
  "event_id": "uuid",
  "session_id": "uuid",
  "timestamp": "2024-01-15T10:15:00.000Z",
  "event_type": "SubagentStop",
  "reason": "task_completed",
  "status": "completed"
}
```

**Utility**: Track subagent lifecycle, correlate with delegated tasks.

### 6.7 UserPromptSubmit

Captured when the user sends a prompt.

**Schema**:
```json
{
  "event_id": "uuid",
  "session_id": "uuid",
  "timestamp": "2024-01-15T10:00:30.000Z",
  "event_type": "UserPromptSubmit",
  "prompt_preview": "Create a configuration file...",
  "prompt_length": 150,
  "status": "submitted"
}
```

**Utility**: Analyze interaction patterns, correlate prompts with results.

### 6.8 PreCompact

Captured before context compaction.

**Schema**:
```json
{
  "event_id": "uuid",
  "session_id": "uuid",
  "timestamp": "2024-01-15T10:20:00.000Z",
  "event_type": "PreCompact",
  "transcript_path": "/path/to/transcript",
  "status": "compacting"
}
```

**Utility**: Monitor context usage, identify sessions with heavy context.

### 6.9 Notification

Captured when a notification is generated.

**Schema**:
```json
{
  "event_id": "uuid",
  "session_id": "uuid",
  "timestamp": "2024-01-15T10:10:00.000Z",
  "event_type": "Notification",
  "notification_type": "warning",
  "notification_message": "Large file detected...",
  "status": "notified"
}
```

**Notification Types**:
- `info`: Informational messages
- `warning`: Alerts
- `error`: Error notifications
- `success`: Success confirmations
- `permission`: Permission requests

**Utility**: Track user communication, identify alert situations.

### 6.10 Event Relationships

```
SessionStart
    |
    +-- UserPromptSubmit
    |
    +-- PreToolUse (Read)
    |       +-- PostToolUse (Read, success)
    |
    +-- PreToolUse (Task)
    |       +-- PreToolUse (Grep)
    |       |       +-- PostToolUse (Grep, success)
    |       +-- SubagentStop
    |       +-- PostToolUse (Task, success)
    |
    +-- Notification (permission)
    |
    +-- PreToolUse (Write)
    |       +-- PostToolUse (Write, error)
    |
    +-- PreCompact (if context exhausted)
    |
    +-- Stop
            +-- SessionEnd
```

---

## 7. Trace Analysis

### 7.1 Trace Location

Trace files are stored at:

```
.claude/ctx-monitor/traces/
├── sessions.json              # Index of all sessions
├── session_<uuid>.jsonl       # Individual trace
└── ...
```

### 7.2 JSONL Format

Each line in the trace file is an independent JSON object:

```jsonl
{"event_id":"e1","session_id":"s1","timestamp":"...","event_type":"SessionStart","cwd":"/project","status":"started"}
{"event_id":"e2","session_id":"s1","timestamp":"...","event_type":"PreToolUse","tool_name":"Read","status":"pending"}
{"event_id":"e3","session_id":"s1","timestamp":"...","event_type":"PostToolUse","tool_name":"Read","status":"success"}
```

### 7.3 Manual Analysis Commands

For quick command-line analysis:

```bash
# View all events
cat session_abc123.jsonl | jq .

# Filter by event type
cat session_abc123.jsonl | jq 'select(.event_type == "PostToolUse")'

# Errors only
cat session_abc123.jsonl | jq 'select(.status == "error")'

# Count events by type
cat session_abc123.jsonl | jq -s 'group_by(.event_type) | map({type: .[0].event_type, count: length})'

# Calculate error rate per tool
cat session_abc123.jsonl | jq -s '
  [.[] | select(.event_type == "PostToolUse")] |
  group_by(.tool_name) |
  map({
    tool: .[0].tool_name,
    total: length,
    errors: [.[] | select(.status == "error")] | length,
    error_rate: (([.[] | select(.status == "error")] | length) / length * 100)
  }) |
  sort_by(-.error_rate)
'
```

### 7.4 Sessions Index

The `sessions.json` file contains metadata for all sessions:

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

---

## 8. Modular Audits

The ctx-monitor audit system is composed of four independent modules, each focused on a specific category of problems.

### 8.1 Intermittency Audit

**Objective**: Detect unstable execution patterns.

**What it identifies**:
- Tools that sometimes work, sometimes fail
- Hooks that don't fire consistently
- Partial executions
- Oscillating error patterns
- Session stability issues

**Script**: `audit-intermittency.py`

**Problem Indicators**:
- Success rate < 90% for the same tool
- PreToolUse without corresponding PostToolUse
- Multiple short sequential sessions

### 8.2 Conflicts Audit

**Objective**: Identify contradictory configurations.

**What it identifies**:
- Contradictory instructions in CLAUDE.md
- Duplicate sections
- Competing hook matchers
- Permission conflicts in settings
- Duplicate commands/skills

**Script**: `audit-conflicts.py`

**Analyzed Files**:
- `.claude/settings.json`
- `.claude/settings.local.json`
- `CLAUDE.md`
- Hook files from all plugins

### 8.3 Tokens Audit

**Objective**: Analyze token usage efficiency.

**What it identifies**:
- Sessions with excessive token usage
- Very large tool inputs (>5000 tokens)
- Redundant file read patterns
- Inefficient usage (high tokens + high error)
- Heavy context loading at start

**Script**: `audit-tokens.py`

**Metrics**:
- Tokens per tool
- Tokens per session
- Token density (tokens/event)

### 8.4 Compliance Audit

**Objective**: Verify format and pattern compliance.

**What it identifies**:
- Events outside expected schema
- Incorrect timestamp formats
- Duplicate event IDs
- Low-quality error messages
- Tool name inconsistency
- Sessions index validation

**Script**: `audit-compliance.py`

**Verified Patterns**:
- ISO8601 for timestamps
- UUID for identifiers
- Valid JSON structure
- Required fields present

### 8.5 Severity Levels

Audit results are classified into three levels:

| Level | Meaning | Examples |
|-------|---------|----------|
| Critical | Immediate attention needed | Data corruption, invalid JSON |
| Warning | Should be addressed soon | Intermittent failures, conflicts |
| Info | Optimization opportunity | Efficiency improvements |

---

## 9. Execution Comparison

### 9.1 Purpose

Trace comparison allows identifying differences between executions, being essential for:

- Regression detection after changes
- Correction validation
- Update impact analysis
- Baseline establishment

### 9.2 Difference Categories

| Category | Description |
|----------|-------------|
| Added Tools | Tools called in session2 but not in session1 |
| Removed Tools | Tools in session1 but not in session2 |
| Changed Tools | Differences in count or error rate |
| Error Changes | New errors or resolved errors |
| Sequence Changes | Changes in execution order |

### 9.3 Results Interpretation

**Added Tools**:
- New functionality was implemented
- Behavior changed to include additional steps

**Removed Tools**:
- Functionality was simplified
- Possible regression if removal was unexpected

**Error Rate Changes**:
- Increase indicates possible regression
- Decrease indicates improvement

**Sequence Changes**:
- May indicate flow optimization
- May indicate unexpected behavior

---

## 10. Diagnostic Export

### 10.1 Bundle Purpose

The diagnostic bundle is a compressed package containing all information needed to analyze problems outside the original environment. It's useful for:

- Sharing with support teams
- Documenting issues in repositories
- Archiving sessions for future reference
- Analysis in isolated environment

### 10.2 Bundle Contents

```
ctx-monitor-bundle.zip
├── traces/
│   ├── session_abc123.jsonl    # JSONL traces
│   └── sessions.json           # Index
├── config.json                  # Configuration snapshot
├── environment.json             # System information
└── report.md                    # Summary report
```

### 10.3 Anonymization Process

Anonymization is applied automatically (default) and removes:

| Data Type | Detection Pattern | Replacement |
|-----------|-------------------|-------------|
| API Keys | `key`, `token`, `secret` | `[REDACTED_KEY]` |
| Passwords | `password`, `pwd` | `[REDACTED_PASSWORD]` |
| Emails | `*@*.*` | `[REDACTED_EMAIL]` |
| User Paths | `/Users/name/`, `/home/name/` | `/Users/[USER]/` |
| Internal IPs | `10.*`, `192.168.*`, `172.16-31.*` | `[REDACTED_IP]` |

### 10.4 Export Best Practices

1. **Always review the bundle before sharing**: Even with anonymization, verify there's no sensitive data.

2. **Use anonymization by default**: Only disable for internal analysis.

3. **Include configuration when relevant**: Helps with problem reproduction.

4. **Name bundles meaningfully**: Use conventions like `issue-123-bundle.zip`.

---

## 11. trace-analyzer Agent

### 11.1 Purpose

The trace-analyzer is a specialized agent for deep trace analysis. It's automatically activated when the user requests execution analysis or after running `/ctx-monitor:report`.

### 11.2 Activation

The agent is activated by phrases like:
- "analyze traces"
- "find issues in execution"
- "why are there so many errors in traces?"
- "debug ctx-monitor logs"

### 11.3 Analysis Process

1. **Trace Location**: Searches for files in `.claude/ctx-monitor/traces/`

2. **Parse and Extraction**: Reads events and extracts relevant fields

3. **Pattern Detection**:
   - Error rates > 10%
   - Intermittent failures (consistency < 90%)
   - Performance (duration > 5000ms)
   - Abnormal sequences

4. **Evidence Collection**: For each problem, records event_id, timestamp, error message

5. **Recommendation Generation**: Suggests specific corrective actions

### 11.4 Output Format

```markdown
## Trace Analysis Report

### Summary
- **Session ID**: [identifier]
- **Time Range**: [start] to [end]
- **Total Events**: [count]
- **Error Rate**: [percentage]

### Issues Found

#### [CRITICAL/HIGH/MEDIUM/LOW] Issue Title
**Pattern**: [pattern type]
**Occurrences**: [count]
**Affected Components**: [list]

**Evidence**:
- Event ID: [id] at [timestamp]

**Root Cause Analysis**:
[Explanation]

**Remediation**:
1. [Action]
2. [Action]

---

### Tool Statistics
| Tool | Calls | Errors | Error Rate | Avg Duration |
|------|-------|--------|------------|--------------|

### Recommendations Summary
1. **Immediate**: [urgent]
2. **Short-term**: [improvements]
3. **Long-term**: [architectural]
```

### 11.5 Severity Classification

| Level | Criteria |
|-------|----------|
| CRITICAL | System-breaking problems, data loss, security |
| HIGH | Significant failures in core functionality |
| MEDIUM | Intermittent issues, performance degradation |
| LOW | Minor anomalies, optimization opportunities |

---

## 12. trace-interpretation Skill

### 12.1 Purpose

The trace-interpretation skill provides specialized knowledge for interpreting ctx-monitor traces. It's activated when the user needs to understand the meaning of captured data.

### 12.2 Activation

Phrases that activate the skill:
- "interpret ctx-monitor traces"
- "understand execution logs"
- "what do ctx-monitor events mean"
- "debugging trace output"

### 12.3 Skill Contents

The skill includes:
- Documentation of all event types
- Common failure patterns catalog
- jq commands for manual analysis
- Troubleshooting checklist

### 12.4 Bundled References

```
skills/trace-interpretation/
├── SKILL.md                    # Main document
└── references/
    ├── event-types.md          # Complete event documentation
    └── common-failures.md      # Failure patterns catalog
```

---

## 13. Common Failure Patterns

### 13.1 Intermittent Failures

**Description**: The same tool call sometimes works, sometimes fails.

**Indicators**:
- Tool appears with both `success` and `error` status
- No clear pattern in arguments

**Common Causes**:
- Network instability
- Race conditions
- Resource contention
- Unstable external dependencies

**Remediation**:
- Add retry logic with exponential backoff
- Implement proper error handling
- Check external service status
- Monitor resource usage

### 13.2 Hook Not Firing

**Description**: A configured hook doesn't execute when expected.

**Indicators**:
- PreToolUse present but no hook output
- SessionStart without expected hook context
- No hook debug output in `claude --debug`

**Common Causes**:
- Matcher doesn't match tool name
- Syntax error in hooks.json
- Plugin not loaded
- Timeout exceeded
- Hook script failing silently

**Remediation**:
```bash
# Verify hooks are loaded
/hooks

# Validate configuration
cat hooks/hooks.json | jq .

# Test script directly
echo '{"tool_name": "Write"}' | bash hooks/scripts/event-logger.sh
```

### 13.3 Cascade Failures

**Description**: An initial error triggers multiple subsequent errors.

**Indicators**:
- First error followed by several related errors
- Error messages reference the same resource

**Common Causes**:
- Missing dependency (file/resource not created)
- Corrupted state from previous operation
- Insufficient error handling
- Shared resource corruption

**Remediation**:
- Fix root cause (first error in chain)
- Add error boundaries between operations
- Implement rollback mechanisms
- Add health checks between steps

### 13.4 Performance Degradation

**Description**: Execution times increase throughout the session.

**Indicators**:
- Same tool takes longer in later events
- Memory-related errors appear

**Common Causes**:
- Memory leak
- Resource exhaustion
- Very large context
- External service rate limiting

**Remediation**:
- Run `/compact` to reduce context
- Clean up temporary files
- Monitor memory usage
- Check API limits

### 13.5 Missing Events

**Description**: Expected events don't appear in the trace.

**Indicators**:
- PreToolUse without corresponding PostToolUse
- SessionStart without SessionEnd
- Gaps in timestamp sequence

**Common Causes**:
- Unhandled crash
- User force quit
- Logging hook timeout
- Disk write failure

**Remediation**:
- Check crash logs
- Ensure sufficient hook timeouts
- Monitor disk space
- Add flush after writes

### 13.6 High Error Rates

**Description**: Tool error rate exceeds 10%.

**Indicators**:
- Many events with `error` status
- Repetitive error messages

**Common Causes**:
- Invalid arguments
- Permission issues
- Resource not found
- Validation failures

**Remediation**:
- Review error messages for patterns
- Fix argument generation
- Check file/resource existence
- Validate inputs before tool calls

---

## 14. Practical Use Cases

### 14.1 Debugging Non-Firing Hooks

**Scenario**: You configured a PreToolUse hook to validate writes, but it doesn't seem to be working.

**Procedure**:

1. Start monitoring:
```bash
/ctx-monitor:start --level full
```

2. Execute the action that should trigger the hook

3. Stop monitoring:
```bash
/ctx-monitor:stop
```

4. Generate the report:
```bash
/ctx-monitor:report
```

5. Check if PreToolUse for Write appears in the trace

6. If it appears, the problem might be in the hook itself. Run audit:
```bash
/ctx-monitor:audit --type conflicts
```

### 14.2 Regression Identification

**Scenario**: After updating a plugin, users report different behavior.

**Procedure**:

1. Capture trace with old version (if available in history)

2. Update the plugin

3. Capture new trace executing the same task:
```bash
/ctx-monitor:start
# Execute the task
/ctx-monitor:stop
```

4. Compare the sessions:
```bash
/ctx-monitor:diff --last 2
```

5. Analyze differences in:
   - Added/removed tools
   - Error rate changes
   - Sequence changes

### 14.3 Compliance Auditing

**Scenario**: You need to ensure executions follow established patterns.

**Procedure**:

1. Run session normally with monitoring:
```bash
/ctx-monitor:start
# Work normally
/ctx-monitor:stop
```

2. Run complete audit:
```bash
/ctx-monitor:audit --type all --format md
```

3. Review each category:
   - Compliance: Formats and schemas
   - Conflicts: Contradictory configurations
   - Tokens: Usage efficiency
   - Intermittency: Stability

4. Export bundle for documentation:
```bash
/ctx-monitor:export-bundle --output ./audit-2024-01.zip
```

### 14.4 Performance Investigation

**Scenario**: Sessions are taking longer than expected.

**Procedure**:

1. Start monitoring with full level:
```bash
/ctx-monitor:start --level full
```

2. Execute problematic task

3. Stop and analyze:
```bash
/ctx-monitor:stop
/ctx-monitor:audit --type tokens
```

4. Identify:
   - Tools with highest duration
   - Redundant read patterns
   - Heavy context

5. Use the agent for deep analysis:
```
Analyze traces for performance issues
```

### 14.5 Sharing with Support

**Scenario**: You found a bug and need to report to the support team.

**Procedure**:

1. Reproduce the problem with active monitoring:
```bash
/ctx-monitor:start --level full
# Reproduce the bug
/ctx-monitor:stop
```

2. Generate report for your reference:
```bash
/ctx-monitor:report --format md
```

3. Export anonymized bundle:
```bash
/ctx-monitor:export-bundle --output ./issue-bug-report.zip
```

4. Review the bundle contents before sending

5. Attach the bundle to the support ticket along with:
   - Problem description
   - Steps to reproduce
   - Expected vs observed behavior

---

## 15. Troubleshooting

### 15.1 Monitoring Doesn't Start

**Symptoms**:
- `/ctx-monitor:start` command has no effect
- No trace is created

**Checks**:

1. Confirm the plugin is installed:
```bash
/plugins
```

2. Verify hooks are loaded:
```bash
/hooks
```

3. Check if the traces directory exists:
```bash
ls -la .claude/ctx-monitor/traces/
```

4. Restart Claude Code to reload hooks

### 15.2 Empty or Incomplete Traces

**Symptoms**:
- Trace file exists but is empty
- Missing events in trace

**Checks**:

1. Confirm log level:
```bash
/ctx-monitor:config status
```

2. Check if events are configured:
```bash
cat .claude/ctx-monitor.local.md
```

3. Test hook directly:
```bash
echo '{"event_type":"test"}' | bash plugins/ctx-monitor/hooks/scripts/event-logger.sh
```

4. Check write permissions in directory

### 15.3 Python Script Errors

**Symptoms**:
- report, audit, diff commands fail
- Import or syntax errors

**Checks**:

1. Confirm Python version:
```bash
python3 --version
```

2. Verify installed dependencies

3. Test script in isolation:
```bash
python3 scripts/log-parser.py --help
```

### 15.4 Bundle Won't Export

**Symptoms**:
- export-bundle command fails
- Generated bundle is incomplete

**Checks**:

1. Check disk space

2. Confirm write permissions at destination

3. Check if traces exist to export:
```bash
ls .claude/ctx-monitor/traces/
```

### 15.5 Audit Returns False Positives

**Symptoms**:
- Audit reports problems that don't exist
- Many unnecessary warnings

**Actions**:

1. Review exclude_patterns configuration

2. Adjust thresholds if available

3. Filter results by relevant severity

---

## 16. Technical Reference

### 16.1 Environment Variables

| Variable | Description |
|----------|-------------|
| CLAUDE_PLUGIN_ROOT | Plugin absolute path |
| CLAUDE_PROJECT_DIR | Project root directory |
| CLAUDE_ENV_FILE | File to persist env vars (SessionStart) |

### 16.2 Script Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success, no critical problems |
| 1 | Critical problems detected |
| 2 | Script execution error |

### 16.3 Output Formats

| Format | Extension | Use |
|--------|-----------|-----|
| text | .txt | Quick viewing |
| json | .json | Programmatic integration |
| md | .md | Documentation, sharing |

### 16.4 Limits and Restrictions

| Parameter | Limit | Note |
|-----------|-------|------|
| Maximum event size | 1MB | Larger events are truncated |
| Hook timeout | 5s | Configurable in hooks.json |
| Default retention | 30 days | Configurable |
| Maximum sessions | 100 | Configurable |

### 16.5 Dependencies

| Dependency | Minimum Version | Purpose |
|------------|-----------------|---------|
| Python | 3.7 | Analysis scripts |
| jq | 1.6 | Manual JSON analysis |
| bash | 4.0 | Hook scripts |

---

## Glossary

| Term | Definition |
|------|------------|
| Agent | Autonomous subprocess that executes complex tasks |
| Bundle | Compressed diagnostic package |
| Context | Information window available to the model |
| Hook | Script that intercepts Claude Code events |
| JSONL | JSON Lines - one JSON line per record format |
| Matcher | Pattern that determines when a hook fires |
| Session | Complete Claude Code interaction instance |
| Skill | Specialized knowledge module |
| Subagent | Agent delegated via Task tool |
| Trace | Chronological record of session events |

---

## Support and Contribution

**Report Issues**:
- GitHub Issues: https://github.com/murillodutt/ctx-monitor/issues

**Contribute**:
- Pull Requests are welcome
- Follow the contribution guidelines in the repository

**Contact**:
- Author: Murillo Dutt
- Email: murillo@duttyeshua.com
- Organization: Dutt Yeshua Technology Ltd

---

**End of Manual**

Version 0.3.5 - 2026-01-12
