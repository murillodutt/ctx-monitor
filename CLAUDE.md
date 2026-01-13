# CLAUDE.md

## Project
**ctx-monitor** - Observability plugin for Claude Code CLI. Monitors agents, hooks, rules, skills execution.

## Owner
Murillo Dutt / Dutt Yeshua Technology Ltd / MIT

## Language
- Output: PT-BR | Docs: bilingual (`docs/en/`, `docs/pt-br/`) | Code comments: EN
- Style: professional, direct, no emojis, ASCII only

## Artifact Placement

**Before creating any artifact, ask: Is it core ctx-monitor functionality?**

### Plugin (`plugins/ctx-monitor/`) - Distributed
For ALL users: `commands/`, `agents/`, `skills/`, `hooks/`, `scripts/`
- Core functionality (event-logger, trace-analyzer, dashboard)
- No workflow preferences, no hardcoded paths

### Local (`.claude/`) - Development Only
For THIS project: `.claude/hooks/`, `.claude/agents/`, `.claude/rules/`
- Code quality tools (pre-commit-validator, python-reviewer)
- Project configs, runtime traces

### Quick Reference
- `event-logger` -> Plugin (core feature)
- `pre-commit-validator` -> .claude/ (dev workflow)
- `trace-analyzer` -> Plugin (user feature)
- `python-reviewer` -> .claude/ (code quality)
