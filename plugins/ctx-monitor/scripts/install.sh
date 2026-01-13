#!/bin/bash
# ctx-monitor installation script
# Usage: curl -sSL https://raw.githubusercontent.com/murillodutt/ctx-monitor/main/scripts/install.sh | bash

set -e

REPO="murillodutt/ctx-monitor"
PLUGIN_NAME="ctx-monitor"
PLUGINS_DIR="$HOME/.claude/plugins"
PLUGIN_DIR="$PLUGINS_DIR/$PLUGIN_NAME"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# Check dependencies
command -v git >/dev/null 2>&1 || error "git is required but not installed"

info "Installing ctx-monitor plugin..."

# Create plugins directory
mkdir -p "$PLUGINS_DIR"

# Remove existing installation
if [ -d "$PLUGIN_DIR" ]; then
    warn "Existing installation found. Removing..."
    rm -rf "$PLUGIN_DIR"
fi

# Clone repository
info "Downloading from GitHub..."
git clone --depth 1 "https://github.com/$REPO.git" "$PLUGIN_DIR" 2>/dev/null

# Clean up git metadata
rm -rf "$PLUGIN_DIR/.git"

# Create marketplace registry if not exists
MARKETPLACE_FILE="$PLUGINS_DIR/.claude-plugin/marketplace.json"
mkdir -p "$PLUGINS_DIR/.claude-plugin"

if [ ! -f "$MARKETPLACE_FILE" ]; then
    info "Creating marketplace registry..."
    cat > "$MARKETPLACE_FILE" << 'EOF'
{
  "plugins": []
}
EOF
fi

# Add plugin to marketplace if not already present
if ! grep -q "\"$PLUGIN_NAME\"" "$MARKETPLACE_FILE" 2>/dev/null; then
    info "Registering plugin in marketplace..."
    # Use Python for JSON manipulation (more reliable)
    python3 << PYEOF
import json
import os

marketplace_file = "$MARKETPLACE_FILE"
plugin_entry = {
    "name": "$PLUGIN_NAME",
    "path": "$PLUGIN_NAME",
    "enabled": True,
    "source": {
        "source": "github",
        "repo": "$REPO"
    }
}

try:
    with open(marketplace_file, 'r') as f:
        data = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    data = {"plugins": []}

# Check if plugin already exists
exists = any(p.get("name") == "$PLUGIN_NAME" for p in data.get("plugins", []))
if not exists:
    data.setdefault("plugins", []).append(plugin_entry)
    with open(marketplace_file, 'w') as f:
        json.dump(data, f, indent=2)
PYEOF
fi

info "Installation complete!"
echo ""
echo -e "${GREEN}ctx-monitor${NC} installed successfully at: $PLUGIN_DIR"
echo ""
echo "Next steps:"
echo "  1. Start Claude Code: claude"
echo "  2. Begin monitoring:  /ctx-monitor:start"
echo "  3. View report:       /ctx-monitor:report"
echo ""
echo "To update later, run this script again or use:"
echo "  /plugin update ctx-monitor"
