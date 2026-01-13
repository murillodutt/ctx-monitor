#!/bin/bash
# check-install.sh - Quick installation check for ctx-monitor
#
# Usage: check-install.sh <project_dir>
# Returns: 0 if installed, 1 if not installed
# Output: Error message if not installed

PROJECT_DIR="${1:-.}"
MONITOR_DIR="${PROJECT_DIR}/.claude/ctx-monitor"

# Check if ctx-monitor directory exists
if [ ! -d "$MONITOR_DIR" ]; then
    echo "⚠️  ctx-monitor is not installed."
    echo ""
    echo "Run the following command to set up:"
    echo "  /ctx-monitor:doctor"
    echo ""
    exit 1
fi

# Check if traces directory exists
if [ ! -d "${MONITOR_DIR}/traces" ]; then
    echo "⚠️  ctx-monitor installation is incomplete."
    echo ""
    echo "Run the following command to repair:"
    echo "  /ctx-monitor:doctor --repair"
    echo ""
    exit 1
fi

# Installation is OK
exit 0
