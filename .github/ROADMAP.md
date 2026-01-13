# ctx-monitor Roadmap

This document outlines the current state and future vision for ctx-monitor.

**Current Version**: 0.3.6
**Last Updated**: January 2026

---

## Phase 1: Foundation (Completed)

Core infrastructure for event capture, storage, and basic analysis.

- [x] **Event Ingestion via Hooks**: 9 event types (SessionStart, SessionEnd, PreToolUse, PostToolUse, Stop, SubagentStop, UserPromptSubmit, PreCompact, Notification)
- [x] **JSONL Storage**: Append-only trace files with session indexing
- [x] **Core Commands**: `/start`, `/stop`, `/report`, `/config`
- [x] **Modular Audits**: 4 audit types (tokens, intermittency, conflicts, compliance)
- [x] **Session Comparison**: `/diff` command for regression detection
- [x] **Diagnostic Tools**: `/doctor` for auto-repair, `/export-bundle` for support

---

## Phase 2: User Experience (In Progress)

Enhanced visualization and user-facing features.

- [x] **Dashboard Web UI**: React 18 SPA with 5 pages (Overview, Stack, Tools, Timeline, Alerts)
- [x] **Real-time Updates**: File watcher with live event streaming
- [x] **Dark/Light Theme**: Full theme support with design system
- [x] **Terminal Renderer**: Rich terminal output with sparklines, charts, and colors
- [ ] **Call Tree Visualization**: Hierarchy of agents and subagents *(structure exists, needs frontend integration)*
- [ ] **Advanced Filters**: Search by time, tool, or error type *(partial implementation)*

---

## Phase 3: Automation & AI (Planned)

Intelligent analysis and automation capabilities.

- [x] **AI Agents**: trace-analyzer (deep analysis) and quick-validator (fast checks with Haiku)
- [x] **Interpretation Skill**: Comprehensive guide for trace understanding
- [ ] **trace-analyzer v2**: Proactive prompt optimization suggestions
- [ ] **Real-time Alerting**: Push notifications when thresholds are exceeded *(alert detection exists, needs webhook/push)*
- [ ] **CI/CD Integration**: GitHub Actions for performance validation *(ci-verify.sh exists, needs documentation)*

---

## Phase 4: Ecosystem (Planned)

Community and external integrations.

- [x] **Plugin Marketplace**: Full compliance with Claude Code marketplace
- [ ] **SDK for Custom Audits**: Templates and documentation for community audit rules
- [ ] **External Platform Integration**: Export to Datadog, New Relic, Grafana
- [ ] **Benchmarking Tools**: Comparative prompt performance analysis

---

## Phase 5: Enterprise Features (Future)

Advanced features for larger deployments.

- [ ] **Multi-project Aggregation**: Unified dashboard across projects
- [ ] **Team Analytics**: Shared metrics and collaborative debugging
- [ ] **Retention Policies**: Automatic trace cleanup based on age/size
- [ ] **Custom Event Types**: User-defined events for domain-specific tracking
- [ ] **Export Formats**: CSV, Parquet, OpenTelemetry compatibility

---

## Configuration Roadmap

Settings currently available vs planned:

| Setting | Status | Description |
|---------|--------|-------------|
| `enabled` | Available | Enable/disable logging |
| `log_level` | Available | minimal, medium, full |
| `events` | Available | Select which events to capture |
| `anonymize_on_export` | Available | Auto-redact sensitive data |
| `retention_days` | Planned | Auto-cleanup after N days |
| `max_sessions` | Planned | Limit stored sessions |
| `tools_filter` | Planned | Capture only specific tools |
| `exclude_patterns` | Planned | Skip matching events |

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Priority areas for contribution:**
1. Advanced filter implementation in React dashboard
2. Call tree visualization component
3. External platform integrations (Datadog, New Relic)
4. Additional audit modules
