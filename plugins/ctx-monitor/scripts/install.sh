#!/bin/bash
# ctx-monitor installation script
# Usage: curl -sSL https://raw.githubusercontent.com/murillodutt/ctx-monitor/main/plugins/ctx-monitor/scripts/install.sh | bash

set -e

# Configuration
REPO="murillodutt/ctx-monitor"
PLUGIN_NAME="ctx-monitor"
MARKETPLACE_NAME="dutt-plugins-official"

# Paths
PLUGINS_DIR="$HOME/.claude/plugins"
MARKETPLACES_DIR="$PLUGINS_DIR/marketplaces"
MARKETPLACE_DIR="$MARKETPLACES_DIR/$MARKETPLACE_NAME"
MARKETPLACE_PLUGIN_DIR="$MARKETPLACE_DIR/.claude-plugin"
MARKETPLACE_FILE="$MARKETPLACE_PLUGIN_DIR/marketplace.json"
KNOWN_MARKETPLACES_FILE="$PLUGINS_DIR/known_marketplaces.json"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }
step() { echo -e "${BLUE}[STEP]${NC} $1"; }

# Check dependencies
command -v git >/dev/null 2>&1 || error "git is required but not installed"
command -v python3 >/dev/null 2>&1 || error "python3 is required but not installed"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ctx-monitor Plugin Installer${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Step 1: Create directory structure
step "Creating marketplace directory structure..."
mkdir -p "$MARKETPLACE_PLUGIN_DIR"
mkdir -p "$MARKETPLACE_DIR/plugins"

# Step 2: Clone/update repository
step "Downloading plugin from GitHub..."
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

git clone --depth 1 "https://github.com/$REPO.git" "$TEMP_DIR" 2>/dev/null || error "Failed to clone repository"

# Step 3: Copy plugin files to marketplace
PLUGIN_SOURCE="$TEMP_DIR/plugins/$PLUGIN_NAME"
PLUGIN_DEST="$MARKETPLACE_DIR/plugins/$PLUGIN_NAME"

if [ ! -d "$PLUGIN_SOURCE" ]; then
    error "Plugin source not found at $PLUGIN_SOURCE"
fi

# Remove existing plugin if present
if [ -d "$PLUGIN_DEST" ]; then
    warn "Existing plugin installation found. Replacing..."
    rm -rf "$PLUGIN_DEST"
fi

info "Copying plugin files..."
cp -r "$PLUGIN_SOURCE" "$PLUGIN_DEST"

# Step 4: Create marketplace.json
step "Creating marketplace manifest..."
cat > "$MARKETPLACE_FILE" << 'MARKETPLACE_EOF'
{
  "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
  "name": "dutt-plugins-official",
  "description": "Official Dutt Yeshua Technology plugins marketplace",
  "owner": {
    "name": "Murillo Dutt",
    "email": "murillo@duttyeshua.com"
  },
  "plugins": [
    {
      "name": "ctx-monitor",
      "description": "Observability and auditing plugin for Claude Code CLI Context Engineering",
      "version": "0.3.6",
      "author": {
        "name": "Murillo Dutt",
        "email": "murillo@duttyeshua.com"
      },
      "source": "./plugins/ctx-monitor",
      "category": "development",
      "homepage": "https://github.com/murillodutt/ctx-monitor"
    }
  ]
}
MARKETPLACE_EOF

# Step 5: Register marketplace in known_marketplaces.json
step "Registering marketplace..."
python3 << PYEOF
import json
import os
from datetime import datetime, timezone

known_file = "$KNOWN_MARKETPLACES_FILE"
marketplace_name = "$MARKETPLACE_NAME"
marketplace_dir = "$MARKETPLACE_DIR"
repo = "$REPO"

# Load existing or create new
try:
    with open(known_file, 'r') as f:
        data = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    data = {}

# Add/update marketplace entry
data[marketplace_name] = {
    "source": {
        "source": "github",
        "repo": repo
    },
    "installLocation": marketplace_dir,
    "lastUpdated": datetime.now(timezone.utc).isoformat()
}

# Ensure directory exists
os.makedirs(os.path.dirname(known_file), exist_ok=True)

with open(known_file, 'w') as f:
    json.dump(data, f, indent=2)

print(f"Marketplace '{marketplace_name}' registered successfully")
PYEOF

# Step 6: Clean up old incorrect installation if exists
OLD_INSTALL="$PLUGINS_DIR/$PLUGIN_NAME"
if [ -d "$OLD_INSTALL" ]; then
    warn "Found old installation at $OLD_INSTALL. Removing..."
    rm -rf "$OLD_INSTALL"
fi

OLD_MARKETPLACE="$PLUGINS_DIR/.claude-plugin"
if [ -d "$OLD_MARKETPLACE" ]; then
    warn "Found incorrect marketplace config at $OLD_MARKETPLACE. Removing..."
    rm -rf "$OLD_MARKETPLACE"
fi

info "Installation complete!"
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Installation Summary${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Marketplace: ${BLUE}$MARKETPLACE_NAME${NC}"
echo -e "Location:    ${BLUE}$MARKETPLACE_DIR${NC}"
echo -e "Plugin:      ${BLUE}$PLUGIN_NAME${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Install the plugin:"
echo -e "     ${GREEN}claude plugin install ctx-monitor@dutt-plugins-official${NC}"
echo ""
echo "  2. Start Claude Code and begin monitoring:"
echo -e "     ${GREEN}/ctx-monitor:start${NC}"
echo ""
echo "  3. View reports:"
echo -e "     ${GREEN}/ctx-monitor:report${NC}"
echo ""
echo -e "${YELLOW}To update later:${NC}"
echo "  Run this script again or use:"
echo -e "  ${GREEN}claude plugin update ctx-monitor@dutt-plugins-official${NC}"
echo ""
