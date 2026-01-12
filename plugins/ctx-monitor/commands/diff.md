---
description: Compare traces between sessions to identify regressions
argument-hint: "<session1> <session2> | --last <n>"
allowed-tools:
  - Bash
  - Read
  - Glob
---

# Compare Trace Sessions

Compare two trace sessions to identify differences, regressions, and changes in execution patterns.

## Instructions

1. Parse arguments:
   - `<session1> <session2>`: Two session IDs to compare
   - `--last <n>`: Compare the last N sessions (default: 2)
   - `--format text|json|md`: Output format (default: text)

2. Locate trace files:
   - If session IDs provided, find `session_<id>.jsonl`
   - If `--last`, find most recent trace files

3. Use the diff-engine script:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/diff-engine.py <file1> <file2> --format <format>
   ```

   Or with --last:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/diff-engine.py --traces-dir .claude/ctx-monitor/traces --last <n>
   ```

4. Present comparison results:
   - Added/removed tool calls
   - Changed tool call counts
   - New errors introduced
   - Resolved errors
   - Sequence changes

5. Highlight regressions:
   - New errors are marked prominently
   - Increased error rates flagged
   - Changed behavior patterns noted

## Usage Examples

- `/ctx-monitor:diff --last 2` - Compare two most recent sessions
- `/ctx-monitor:diff abc123 xyz789` - Compare specific sessions
- `/ctx-monitor:diff --last 3 --format md` - Compare 3 sessions with markdown output

## Diff Categories

1. **Added Tools**: Tools called in session2 but not session1
2. **Removed Tools**: Tools in session1 but not session2
3. **Changed Tools**: Different call counts or error rates
4. **Error Changes**: New errors or resolved errors
5. **Sequence Changes**: Different execution order
