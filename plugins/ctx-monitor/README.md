# ctx-monitor Plugin

Observability and auditing plugin for Claude Code CLI context engineering.

## Overview

The ctx-monitor plugin provides comprehensive monitoring and tracing capabilities for Claude Code sessions. It helps you understand what happens during runtime by tracking agents, subagents, hooks, rules, and skills execution.

**Key features:**
- Event logging for end-to-end execution pipeline
- Detection of intermittent failures (hooks not firing, partial tool execution)
- Execution comparison (diff traces) for regression identification
- Shareable diagnostic bundles (anonymized logs, reports, config snapshots)
- Per-project activation with global plugin support

## Quick Start

### 1. Start Monitoring

```bash
/start
```

Begins capturing events for the current session.

### 2. Stop and Generate Report

```bash
/stop
```

Stops monitoring and saves the trace log.

### 3. View Report

```bash
/report
```

Generates a summary of the captured events.

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Start monitoring session |
| `/stop` | Stop monitoring and save trace |
| `/report` | Generate execution report |
| `/audit` | Run compliance audit on traces |
| `/diff` | Compare two execution traces |
| `/config` | Configure monitoring settings |
| `/export-bundle` | Export anonymized diagnostic bundle |

## Agents

### trace-analyzer

Specialized agent for analyzing execution traces and identifying patterns, failures, and anomalies.

```bash
# Invoke via Task tool or mention in conversation
"Analyze the trace for intermittent failures"
```

## Use Cases

### Debugging Hook Failures

When hooks don't fire as expected:
1. Start monitoring with `/start`
2. Reproduce the issue
3. Stop with `/stop`
4. Run `/report` to see which hooks were triggered

### Regression Detection

Compare execution between versions:
1. Capture baseline trace
2. Make changes
3. Capture new trace
4. Use `/diff` to compare

### Compliance Auditing

Verify execution meets requirements:
1. Run `/audit` after a session
2. Review compliance report
3. Export bundle for sharing

## Configuration

Configure via `/config` command or edit `.claude/ctx-monitor.local.md`:

```yaml
---
enabled: true
log_level: medium  # minimal | medium | full
anonymize_on_export: true
---
```

## Installation

This plugin is available via the dutt-plugins-official marketplace.

```bash
/plugin install ctx-monitor@dutt-plugins-official
```

## Requirements

- Python 3.7+
- Claude Code CLI v2.1+

## License

MIT License

## Author

Murillo Dutt - Dutt Yeshua Technology Ltd
