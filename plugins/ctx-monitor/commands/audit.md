---
description: Run modular audits on execution traces
argument-hint: "[--type all|intermittency|conflicts|tokens|compliance] [--format text|json|md]"
allowed-tools:
  - Bash
  - Read
  - Glob
  - Grep
---

# Run Execution Audits

Perform modular audits on trace data to detect issues, inefficiencies, and compliance problems.

## Instructions

1. Parse the arguments:
   - `--type`: Audit type (default: `all`)
     - `all`: Run all audit types
     - `intermittency`: Check for intermittent failures
     - `conflicts`: Detect instruction conflicts
     - `tokens`: Analyze token efficiency
     - `compliance`: Check output format compliance
   - `--format`: Output format (default: `text`)
     - `text`: Plain text report
     - `json`: JSON output
     - `md`: Markdown report

2. Run the audit using the Python scripts:

```bash
# Run all audits
python ${CLAUDE_PLUGIN_ROOT}/scripts/audit-runner.py "$(pwd)" --type all --format md

# Run specific audit type
python ${CLAUDE_PLUGIN_ROOT}/scripts/audit-runner.py "$(pwd)" --type intermittency --format md
```

3. The audit scripts are located in `${CLAUDE_PLUGIN_ROOT}/scripts/`:
   - `audit-runner.py` - Orchestrator that runs multiple audits
   - `audit-intermittency.py` - Detects intermittent failures
   - `audit-conflicts.py` - Finds configuration conflicts
   - `audit-tokens.py` - Analyzes token efficiency
   - `audit-compliance.py` - Checks format compliance

## Audit Types

### Intermittency Audit
Detects unreliable execution patterns:
- Tools that succeed sometimes and fail others
- Hooks that didn't fire when expected (PreToolUse without PostToolUse)
- Partial executions and oscillating error patterns
- Session stability issues

### Conflicts Audit
Scans for configuration conflicts:
- Contradictory instructions in CLAUDE.md
- Duplicate section definitions
- Competing hook matchers across sources
- Permission conflicts in settings files
- Duplicate command/skill definitions

### Tokens Audit
Analyzes token efficiency:
- High token usage sessions
- Oversized tool inputs (>5000 tokens)
- Redundant file read patterns
- Inefficient tool usage (high tokens + high errors)
- Heavy context loading at session start

### Compliance Audit
Checks output format standards:
- Event schema compliance (required fields)
- Timestamp format (ISO8601)
- Event ID uniqueness
- Error message quality
- Tool name consistency
- Sessions index validation

## Severity Levels

| Level | Meaning |
|-------|---------|
| 🔴 Critical | Requires immediate attention (data corruption, invalid JSON) |
| 🟡 Warning | Should be addressed soon (intermittent failures, conflicts) |
| 🔵 Info | Optimization opportunity (efficiency improvements) |

## Usage Examples

```bash
# Run all audits with markdown output
/ctx-monitor:audit

# Check only for intermittent failures
/ctx-monitor:audit --type intermittency

# Check for instruction conflicts
/ctx-monitor:audit --type conflicts

# Analyze token efficiency
/ctx-monitor:audit --type tokens

# Check compliance with JSON output
/ctx-monitor:audit --type compliance --format json
```

## Exit Codes

- `0`: No critical issues found
- `1`: Critical issues detected (requires attention)

## Trace Requirements

Audits require trace data in `.claude/ctx-monitor/traces/`:
- Session files: `session_*.jsonl`
- Sessions index: `sessions.json`

If no traces exist, run `/ctx-monitor:start` to begin logging.
