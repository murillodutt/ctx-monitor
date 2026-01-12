# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned
- Real-time monitoring dashboard
- Integration with external observability platforms
- Custom audit rule definitions
- Performance benchmarking tools

---

## [0.3.0] - 2026-01-12

### Added

**Core Plugin**
- Complete plugin structure following claude-plugins-official patterns
- Seven slash commands: start, stop, report, audit, diff, config, export-bundle
- trace-analyzer agent for deep execution analysis
- trace-interpretation skill with comprehensive documentation

**Commands**
- `/ctx-monitor:start` - Start event logging with configurable levels (minimal, medium, full)
- `/ctx-monitor:stop` - Stop monitoring and preserve traces
- `/ctx-monitor:report` - Generate execution reports in text, JSON, or markdown
- `/ctx-monitor:audit` - Modular audits (intermittency, conflicts, tokens, compliance)
- `/ctx-monitor:diff` - Compare traces between sessions for regression detection
- `/ctx-monitor:config` - Manage per-project configuration
- `/ctx-monitor:export-bundle` - Create anonymized diagnostic bundles

**Event Capture**
- Full event logging via hooks system
- Nine event types: SessionStart, SessionEnd, PreToolUse, PostToolUse, Stop, SubagentStop, UserPromptSubmit, PreCompact, Notification
- JSONL storage format for efficient parsing
- Session indexing for quick lookups

**Analysis Scripts**
- log-parser.py - Parse and analyze trace files
- audit-runner.py - Orchestrate multiple audit types
- audit-intermittency.py - Detect unreliable execution patterns
- audit-conflicts.py - Find configuration conflicts
- audit-tokens.py - Analyze token efficiency
- audit-compliance.py - Verify format compliance
- diff-engine.py - Compare execution traces
- bundle-creator.py - Create diagnostic packages
- anonymizer.py - Redact sensitive data
- config-manager.py - Manage project settings

**Documentation**
- Plugin Development Guide (docs/plugin-development-guide.md)
- ctx-monitor User Manual in Portuguese (docs/guide-ctx-monitor-pt_br.md)
- Skill references for event types and common failures
- README with installation instructions

**Marketplace Integration**
- dutt-plugins-official marketplace structure
- curl installation script
- Compatible with Claude Code plugin discovery

### Technical Details
- Hooks capture all events with 5s timeout
- Traces stored in .claude/ctx-monitor/traces/
- Configuration via .claude/ctx-monitor.local.md
- Python 3.7+ required for analysis scripts

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 0.3.0 | 2026-01-12 | Initial public release |

---

## Versioning Policy

This project follows Semantic Versioning:

- **MAJOR** (1.0.0+): Stable API, breaking changes increment major
- **MINOR** (0.x.0): New features, backwards compatible
- **PATCH** (0.0.x): Bug fixes, backwards compatible

While in 0.x.x (pre-release), the API may change between minor versions.

---

## Links

- [Repository](https://github.com/murillodutt/ctx-monitor)
- [Issues](https://github.com/murillodutt/ctx-monitor/issues)
- [Claude Code Documentation](https://docs.claude.com/en/docs/claude-code)

---

**Maintained by:** Murillo Dutt - Dutt Yeshua Technology Ltd
