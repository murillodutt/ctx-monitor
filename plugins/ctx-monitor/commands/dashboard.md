---
description: Display rich visual dashboard with session metrics, stack analysis, and alerts
argument-hint: "[--page <name>] [--session <id>] [--no-color]"
allowed-tools:
  - Bash
  - Read
---

# Session Dashboard

Display a rich Unicode dashboard with multiple pages of information about the current monitoring session.

## Pages

- **overview** (default): Health score, events, token usage, tool activity, quick stats
- **stack**: Context engineering stack (rules, hooks, skills, agents) with detailed breakdown
- **tools**: Tool performance with bar charts, histograms, and detailed metrics
- **timeline**: Event flow and distribution over time
- **alerts**: Active alerts, severity distribution, recommendations

## Instructions

1. Parse arguments from the user input:
   - `--page <name>`: Page to display (overview, stack, tools, timeline, alerts)
   - `--session <id>`: Specific session ID (default: most recent)
   - `--no-color`: Disable ANSI color codes

2. Run the dashboard renderer:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/dashboard-renderer.py" "$(pwd)" --page overview
```

3. If a specific page was requested:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/dashboard-renderer.py" "$(pwd)" --page <page_name>
```

4. If a specific session was requested:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/dashboard-renderer.py" "$(pwd)" --session <session_id> --page <page_name>
```

5. Display the output directly to the user without any modifications.

6. If no monitoring data exists, inform the user to run `/ctx-monitor:start` first.

## Usage Examples

```bash
# View overview (default)
/ctx-monitor:dashboard

# View context engineering stack
/ctx-monitor:dashboard --page stack

# View tool performance
/ctx-monitor:dashboard --page tools

# View activity timeline
/ctx-monitor:dashboard --page timeline

# View alerts and recommendations
/ctx-monitor:dashboard --page alerts

# View specific session
/ctx-monitor:dashboard --session abc123 --page overview

# Disable colors (for logs)
/ctx-monitor:dashboard --no-color
```

## Output

The dashboard displays rich Unicode visualizations including:

- Sparklines using block characters: `▁▂▃▄▅▆▇█`
- Progress circles: `○◔◑◕●` (0%, 25%, 50%, 75%, 100%)
- Horizontal bar charts with `░▒▓█`
- Trend indicators: `↑↓↗↘→`
- Box drawing characters for layout
- Tree structures for hierarchical data

All visualizations work in standard terminal environments without requiring special fonts or color support.
