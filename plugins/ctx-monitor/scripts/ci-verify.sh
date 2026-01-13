#!/bin/bash
# ci-verify.sh - Standalone integrity verification for CI/CD pipelines
# Verifies plugin structure, script permissions, and configuration schema

set -euo pipefail

echo "===================================================="
echo "CTX-MONITOR CI VERIFICATION"
echo "===================================================="

PLUGIN_DIR="plugins/ctx-monitor"

# 1. Check Directory Structure
echo "[1/4] Checking directory structure..."
REQUIRED_DIRS="agents commands hooks scripts skills"
for dir in $REQUIRED_DIRS; do
  if [ ! -d "$PLUGIN_DIR/$dir" ]; then
    echo "Error: Missing required directory: $PLUGIN_DIR/$dir"
    exit 1
  fi
done
echo "OK: Structure is valid."

# 2. Check Script Permissions
echo "[2/4] Checking script permissions..."
SCRIPTS=$(find "$PLUGIN_DIR/scripts" -name "*.sh" -o -name "*.py")
for script in $SCRIPTS; do
  if [ ! -x "$script" ]; then
    echo "Warning: Script not executable: $script"
    echo "Fixing: chmod +x $script"
    chmod +x "$script"
  fi
done
echo "OK: Permissions verified."

# 3. Check Manifest Integrity
echo "[3/4] Checking plugin manifest..."
MANIFEST="$PLUGIN_DIR/.claude-plugin/plugin.json"
if [ ! -f "$MANIFEST" ]; then
  echo "Error: Plugin manifest missing: $MANIFEST"
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "Skipping JSON validation: jq not installed."
else
  if ! jq empty "$MANIFEST" 2>/dev/null; then
    echo "Error: Invalid JSON in manifest: $MANIFEST"
    exit 1
  fi
  echo "OK: Manifest is valid JSON."
fi

# 4. Check Root Cleanliness (Same logic as CI workflow)
echo "[4/4] Verifying root cleanliness..."
ALLOWED_FILES="LICENSE .git .ruff_cache .gitignore CLAUDE.md plugins docs .github .claude-plugin .cursor"
ROOT_FILES=$(ls -A)

for file in $ROOT_FILES; do
  is_allowed=false
  for allowed in $ALLOWED_FILES; do
    if [ "$file" == "$allowed" ]; then
      is_allowed=true
      break
    fi
  done
  
  if [ "$is_allowed" == "false" ]; then
    echo "Error: File '$file' is not allowed in the repository root."
    exit 1
  fi
done
echo "OK: Repository root is clean."

echo "===================================================="
echo "SUCCESS: CTX-MONITOR INTEGRITY VERIFIED"
echo "===================================================="
