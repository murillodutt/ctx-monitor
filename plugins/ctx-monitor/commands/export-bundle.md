---
description: Export diagnostic bundle for sharing or support
argument-hint: "[--anonymize] [--include-config] [--output <path>]"
allowed-tools:
  - Bash
  - Read
  - Write
---

# Export Diagnostic Bundle

Create a shareable diagnostic bundle containing traces, configuration, and environment information for support or issue reporting.

## Instructions

1. Parse arguments:
   - `--anonymize` (default: true): Redact sensitive data
   - `--no-anonymize`: Keep data unredacted
   - `--include-config` (default: true): Include config files
   - `--no-config`: Exclude configuration
   - `--output <path>`: Custom output path

2. Use the bundle-creator script:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/bundle-creator.py \
     --project-dir . \
     --anonymize \
     --include-config \
     --output <path>
   ```

3. The bundle includes:
   - `traces/` - Session trace files (JSONL)
   - `config.json` - Configuration snapshot (anonymized)
   - `environment.json` - System/tool versions
   - `report.md` - Summary report

4. Anonymization covers:
   - API keys and tokens
   - Passwords and secrets
   - File paths with usernames
   - Email addresses
   - Internal IP addresses

5. Report the bundle location and contents to user

## Usage Examples

- `/ctx-monitor:export-bundle` - Export with defaults (anonymized, with config)
- `/ctx-monitor:export-bundle --no-anonymize` - Export without redaction
- `/ctx-monitor:export-bundle --output ./diagnostics.zip` - Custom output path

## Bundle Contents

```
ctx-monitor-bundle.zip
├── traces/
│   ├── session_abc123.jsonl
│   └── sessions.json
├── config.json
├── environment.json
└── report.md
```

## Security Notes

- Always review bundle contents before sharing
- Anonymization removes common secret patterns
- Custom patterns can be added via config
- Never share bundles containing production credentials
