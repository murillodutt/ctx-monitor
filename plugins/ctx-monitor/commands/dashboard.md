---
description: Launch interactive web dashboard with real-time metrics
argument-hint: "[--port <number>] [--no-open]"
allowed-tools:
  - Bash
  - Read
---

# Web Dashboard

Launch an interactive web dashboard in your browser.

## Instructions

1. Parse arguments: `--port <number>` (default: 3847), `--no-open` (don't open browser)

2. Launch the dashboard server:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/dashboard_server.py" "$(pwd)"
```

3. With custom port:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/dashboard_server.py" "$(pwd)" --port <port>
```

4. With `--no-open`:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/dashboard_server.py" "$(pwd)" --no-open
```

5. Server opens dashboard in browser automatically. Stop with Ctrl+C.

## Usage

```bash
/ctx-monitor:dashboard
/ctx-monitor:dashboard --port 4000
/ctx-monitor:dashboard --no-open
```
