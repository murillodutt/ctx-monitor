# dutt-plugins-official

[![Version](https://img.shields.io/badge/version-0.3.1-green.svg)](CHANGELOG.md)
[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Marketplace-purple.svg)](https://claude.ai/code)

**Official plugins marketplace by Dutt Yeshua Technology Ltd.**

## Available Plugins

### ctx-monitor

Observability and auditing plugin for Claude Code CLI context engineering.

**Key features:**
- Event logging for end-to-end execution pipeline
- Detection of intermittent failures (hooks not firing, partial tool execution)
- Execution comparison (diff traces) for regression identification
- Shareable diagnostic bundles (anonymized logs, reports, config snapshots)

## Installation

### Quick Install (curl)

```bash
curl -sSL https://raw.githubusercontent.com/murillodutt/ctx-monitor/main/plugins/ctx-monitor/scripts/install.sh | bash
```

### Via Marketplace

```bash
# In Claude Code CLI
/plugin
# Go to Marketplaces > Add Marketplace
# Enter: murillodutt/ctx-monitor
```

Then install the plugin:

```bash
/plugin install ctx-monitor@dutt-plugins-official
```

## ctx-monitor Commands

| Command | Description |
|---------|-------------|
| `/doctor` | **First run**: Diagnose, install, and fix problems automatically |
| `/start` | Start monitoring session |
| `/stop` | Stop monitoring and save trace |
| `/dashboard` | Display visual dashboard with metrics and stack analysis |
| `/report` | Generate execution report |
| `/audit` | Run compliance audit on traces |
| `/diff` | Compare two execution traces |
| `/config` | Configure monitoring settings |
| `/export-bundle` | Export anonymized diagnostic bundle |

### First Time Setup

After installing, run the doctor command to set up ctx-monitor:

```bash
/ctx-monitor:doctor
```

This will automatically:
- Check dependencies
- Create required directories
- Fix any cache or configuration issues
- Set up default configuration

## Configuration

Per-project configuration via `.claude/ctx-monitor.local.md`:

```yaml
---
enabled: true
log_level: medium
retention_days: 30
anonymize_on_export: true
---
```

## Repository Structure

```
dutt-plugins-official/
├── .claude-plugin/
│   └── marketplace.json
├── plugins/
│   └── ctx-monitor/
│       ├── .claude-plugin/
│       │   └── plugin.json
│       ├── agents/
│       ├── commands/
│       ├── hooks/
│       ├── scripts/
│       ├── skills/
│       └── README.md
├── LICENSE
└── README.md
```

## Privacy

All traces are stored locally. Export bundles automatically redact sensitive data.

## Requirements

- Claude Code CLI v2.1+
- Python 3.7+

## License

MIT - [Murillo Dutt](https://github.com/murillodutt/) / Dutt Yeshua Technology Ltd

---

**Issues?** [Open an issue](https://github.com/murillodutt/ctx-monitor/issues)
