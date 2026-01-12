---
description: Diagnose and fix ctx-monitor installation problems
argument-hint: "[--check] [--repair]"
allowed-tools:
  - Bash
  - Read
  - Write
---

# ctx-monitor Doctor

Diagnose, install, and automatically fix ctx-monitor configuration problems.

## Instructions

1. Parse arguments from user input:
   - No args: Full diagnosis + auto-fix + install if needed
   - `--check`: Only verify installation, don't modify anything
   - `--repair`: Force reinstall/repair existing installation

2. Run the doctor script (default):

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/install.py" "$(pwd)" doctor
```

3. For check-only mode:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/install.py" "$(pwd)" check
```

4. For repair mode:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/install.py" "$(pwd)" repair
```

5. Display the output directly to the user.

## What It Does

The doctor command performs the following diagnostics and fixes:

### 1. Cache Cleanup
- Detects orphaned plugin cache references
- Removes corrupted/empty cache directories
- Cleans up `installed_plugins.json`

### 2. Dependency Check
- Verifies Python 3.7+ is available
- Checks for required Python modules

### 3. Directory Setup
- Creates `.claude/ctx-monitor/` directory structure
- Creates `traces/` subdirectory for session logs

### 4. Configuration
- Creates default `ctx-monitor.local.md` if not exists
- Sets up initial configuration with sensible defaults

### 5. Validation
- Verifies hooks are correctly configured
- Tests event logger script permissions
- Confirms all paths are accessible
- Finds and removes broken symlinks

### 6. Status Report
- Shows diagnosis summary
- Lists problems found and fixed
- Provides next steps

## Usage Examples

```bash
# Full diagnosis + install (recommended first run)
/ctx-monitor:doctor

# Check status only (no modifications)
/ctx-monitor:doctor --check

# Force repair/reinstall
/ctx-monitor:doctor --repair
```

## Output Example

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  CTX-MONITOR DOCTOR                                                          │
└──────────────────────────────────────────────────────────────────────────────┘

→ Checking for orphaned cache references...
  ✓ Cleaned 1 orphaned cache reference(s)

→ Checking cache directories...
  ✓ Removed 1 empty cache directory(ies)

→ Checking for broken symlinks...
  ✓ No broken symlinks

→ Checking script permissions...
  ✓ Script permissions OK

→ Checking local installation...
  ✓ Local installation OK

→ Checking configuration...
  ✓ Configuration file OK

  ✓ All 2 problem(s) fixed!

  Next steps:
    1. Run /ctx-monitor:start to begin monitoring
    2. Perform some operations
    3. Run /ctx-monitor:dashboard to view metrics
```

## Common Issues Fixed

| Problem | Automatic Fix |
|---------|---------------|
| Orphaned cache references | Removes from installed_plugins.json |
| Empty/corrupted cache dirs | Deletes empty directories |
| Broken symlinks | Removes broken links |
| Missing script permissions | chmod +x on .sh files |
| Missing directories | Creates required structure |
| Missing config file | Creates default config |
