# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**ctx-monitor-s** (Context Oracle) is an observability and auditing plugin for Claude Code CLI context engineering. It monitors agents, subagents, hooks, rules, and skills execution to provide traceability for what happens during runtime.

### Core Capabilities (planned)
- Event logging for end-to-end execution pipeline
- Detection of intermittent failures (hooks not firing, partial tool execution, unapplied rules/skills)
- Execution comparison (diff traces) for regression identification
- Shareable diagnostic bundles (anonymized logs, reports, config snapshots)
- Global plugin with per-project opt-in activation

## Knowledge
- **Always** seek up-to-date information in the Anthropic, Claude Code, and Claude Code CLI documentation before any task.

## Ownership

- Maintainer: Murillo Dutt
- Organization: Dutt Yeshua Technology Ltd
- License: Open Source Plugin

## Language Guidelines

- **Output/Communication**: (**Always** PT-BR) 
- **Documentation**: Always bilingual (PT-BR and English) in `docs/pt-br/` and `docs/en/`
- **Code comments**: English
- **Technical terms**: English
- **Hooks**: PT-BR

## Style
- **Tone**: professional, direct | **Structure**: headings + concise bullets
- **Ban**: emojis (code, docs, commits) | **Comments**: ASCII only

## Artifact Placement Rules

Before creating any artifact (hook, agent, skill, command, script), determine the correct location:

### Plugin (`plugins/ctx-monitor/`) - Distributed to Users

Use for artifacts that are **part of ctx-monitor functionality**:

| Type | Location | Example |
|------|----------|---------|
| Commands | `commands/` | `/start`, `/stop`, `/report`, `/audit` |
| Agents | `agents/` | trace-analyzer, quick-validator |
| Skills | `skills/` | trace-interpretation |
| Hooks | `hooks/` | event-logger (observability capture) |
| Scripts | `scripts/` | log-parser, audit-runner, dashboard |

**Criteria for plugin inclusion:**
- Provides ctx-monitor core functionality
- Useful for ALL users of the plugin
- Does not impose development workflow preferences
- Does not contain project-specific paths or settings

### Project Local (`.claude/`) - Development Only

Use for artifacts that are **specific to developing ctx-monitor**:

| Type | Location | Example |
|------|----------|---------|
| Dev Hooks | `.claude/hooks/` | pre-commit-validator |
| Dev Agents | `.claude/agents/` | python-reviewer, test-creator |
| Dev Rules | `.claude/rules/` | python-standards, naming-conventions |
| Settings | `.claude/settings.json` | project-specific hooks |
| Traces | `.claude/ctx-monitor/traces/` | runtime data |

**Criteria for local placement:**
- Enforces code quality/style for THIS project
- Development workflow tools (linting, testing)
- Project-specific configurations
- Runtime data (traces, logs)
- Would interfere with other teams' workflows if distributed

### Decision Flowchart

```
Is it core ctx-monitor functionality?
    YES -> Plugin
    NO  -> Is it for developing/maintaining ctx-monitor?
              YES -> .claude/ (local)
              NO  -> Probably doesn't belong here
```

### Examples

| Artifact | Correct Location | Reason |
|----------|------------------|--------|
| Event logging hook | Plugin | Core observability feature |
| Pre-commit linter hook | .claude/ | Development workflow |
| Trace analyzer agent | Plugin | Helps users analyze traces |
| Python reviewer agent | .claude/ | Maintains code quality |
| Dashboard command | Plugin | User-facing feature |
| Version sync command | .claude/ | Internal maintenance |

