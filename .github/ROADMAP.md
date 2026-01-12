# ctx-monitor Roadmap

This document outlines the future vision and planned features for the project.

## Phase 1: Foundation (Completed)
- [x] Event ingestion via Hooks.
- [x] Efficient JSONL storage.
- [x] Core commands: `/start`, `/stop`, `/report`.
- [x] Basic modular audits (Tokens, Intermittency).

## Phase 2: User Experience (In Progress)
- [ ] **Dashboard Web UI**: Rich trace visualization in the browser.
- [ ] **Call Tree Visualization**: View the hierarchy of agents and subagents.
- [ ] **Advanced Filters**: Search by time, specific tool, or error.

## Phase 3: Automation & AI
- [ ] **trace-analyzer v2**: Proactive prompt optimization suggestions based on traces.
- [ ] **Real-time Alerting**: Notifications when cost or error limits are reached.
- [ ] **CI/CD Integration**: Actions to validate prompt performance on every push.

## Phase 4: Ecosystem
- [ ] **Plugin Store Ready**: Full compliance with the official marketplace.
- [ ] **SDK for Custom Audits**: Facilitate the creation of new audit rules by the community.
- [ ] **External Platform Integration**: Export to Datadog, New Relic, etc.
- [ ] **Benchmarking Tools**: Comparative prompt performance analysis.
