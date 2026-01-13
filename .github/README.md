![Image](https://github.com/user-attachments/assets/aec1631d-94bf-45a6-934a-215113d327be)

# ctx-monitor (Context Oracle)

[![Version](https://img.shields.io/badge/version-0.3.6-green.svg)](https://github.com/murillodutt/ctx-monitor/releases)
[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](.github/LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Plugin-purple.svg)](https://claude.ai/code)

**Observability and auditing plugin for Claude Code CLI context engineering.**

**ctx-monitor** provides full traceability and diagnostic capabilities for Claude Code sessions. It monitors the execution of agents, subagents, hooks, rules, and skills to ensure transparency and facilitate debugging of complex automations.

## Key Features

- **Event Logging**: Captures the end-to-end execution pipeline in JSONL format.
- **Failure Detection**: Proactive identification of intermittent failures and hooks that didn't fire.
- **Execution Diff**: Comparison between traces for rapid regression identification.
- **Diagnostic Bundles**: Export anonymized logs for support and auditing purposes.
- **Local Privacy**: All traces are stored locally in your project's `.claude/` directory.

## Quick Start

### 1. Installation

#### Quick Install (curl)
```bash
curl -sSL https://raw.githubusercontent.com/murillodutt/ctx-monitor/main/plugins/ctx-monitor/scripts/install.sh | bash
```

#### Via Marketplace (Recommended)
```bash
/plugin add murillodutt/ctx-monitor
/plugin install ctx-monitor@dutt-plugins-official
```

*Note: Also available via [dutt-plugins-official marketplace](https://github.com/murillodutt/ctx-monitor).*

### 2. Initial Setup

After installation, run the doctor command to prepare the environment:

```bash
/ctx-monitor:doctor
```

### 3. Core Commands

| Command | Description |
|---------|-------------|
| `/start` | Starts monitoring the current session |
| `/stop` | Stops monitoring and saves the final trace |
| `/dashboard` | Opens the visual dashboard with metrics and stack analysis |
| `/report` | Generates a technical execution report |
| `/audit` | Runs compliance and token usage audits |
| `/diff` | Compares the current execution with previous sessions |

## Per-Project Configuration

Customize plugin behavior via `.claude/ctx-monitor.local.md`:

```yaml
---
enabled: true
log_level: medium
retention_days: 30
anonymize_on_export: true
---
```

## Community and Governance

This is an open-source project maintained by **Dutt Yeshua Technology Ltd**. We value transparency and technical collaboration.

- **[Roadmap](.github/ROADMAP.md)**: Future vision and planned features.
- **[Governance](.github/GOVERNANCE.md)**: How technical priorities are defined via demand and voting.
- **[Contributing](.github/CONTRIBUTING.md)**: Development guide and code standards.
- **[Security](.github/SECURITY.md)**: Secure vulnerability reporting policy.

## Requirements

- **Claude Code CLI**: v2.1 or higher.
- **Python**: 3.7+ (required for analysis and audit scripts).

## License

MIT - [Murillo Dutt](https://github.com/murillodutt/) / [Dutt Yeshua Technology Ltd](https://github.com/murillodutt)

---

**Found a problem?** [Open an Issue](https://github.com/murillodutt/ctx-monitor/issues)
