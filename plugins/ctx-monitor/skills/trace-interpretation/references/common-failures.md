# Common Failure Patterns

Detailed catalog of failure patterns and remediation strategies.

## Intermittent Failures

### Description
The same tool call succeeds sometimes and fails others with no apparent pattern.

### Detection
```bash
# Find tools with mixed success/error status
cat session.jsonl | jq -s '
  group_by(.tool_name) |
  map({
    tool: .[0].tool_name,
    success: [.[] | select(.status == "success")] | length,
    error: [.[] | select(.status == "error")] | length
  }) |
  .[] | select(.success > 0 and .error > 0)
'
```

### Common Causes
1. **Network instability** - API calls timing out randomly
2. **Race conditions** - Concurrent file access
3. **Resource contention** - Memory/CPU pressure
4. **External dependencies** - Third-party service issues

### Remediation
- Add retry logic with exponential backoff
- Implement proper error handling
- Check external service status
- Monitor resource usage

---

## Hook Not Firing

### Description
A configured hook doesn't execute when expected.

### Detection
- PreToolUse event exists but expected hook output missing
- SessionStart without hook-injected context
- No hook debug output in `claude --debug`

### Common Causes
1. **Matcher mismatch** - Pattern doesn't match tool name
2. **Configuration error** - Invalid hooks.json syntax
3. **Plugin not loaded** - Plugin not in plugin path
4. **Timeout** - Hook exceeded timeout limit
5. **Exit code** - Hook script failing silently

### Remediation
```bash
# Verify hooks are loaded
/hooks

# Check hook configuration
cat .claude/ctx-monitor/hooks/hooks.json | jq .

# Test hook script directly
echo '{"tool_name": "Write"}' | bash hooks/scripts/event-logger.sh
```

---

## Cascade Failures

### Description
One error triggers a chain of subsequent errors.

### Detection
```bash
# Find error clusters (multiple errors within 5 seconds)
cat session.jsonl | jq -s '
  [.[] | select(.status == "error")] |
  sort_by(.timestamp)
'
```

### Common Causes
1. **Missing dependency** - File/resource not created
2. **Broken state** - Previous operation left bad state
3. **Insufficient error handling** - Errors not caught
4. **Shared resource corruption** - Database/file corruption

### Remediation
- Fix the root cause (first error in chain)
- Add error boundaries between operations
- Implement rollback mechanisms
- Add health checks between steps

---

## Performance Degradation

### Description
Tool execution times increase over the session.

### Detection
```bash
# Calculate average duration per tool over time
cat session.jsonl | jq -s '
  [.[] | select(.event_type == "PostToolUse" and .duration_ms != null)] |
  group_by(.tool_name) |
  map({
    tool: .[0].tool_name,
    avg_duration: ([.[].duration_ms] | add / length),
    max_duration: ([.[].duration_ms] | max)
  })
'
```

### Common Causes
1. **Memory leak** - Growing memory usage
2. **Large context** - Token count increasing
3. **File system bloat** - Many temporary files
4. **External service degradation** - API rate limiting

### Remediation
- Run `/compact` to reduce context
- Clean up temporary files
- Monitor memory usage
- Check API rate limits

---

## Missing Events

### Description
Expected events are missing from the trace.

### Detection
- PreToolUse without matching PostToolUse
- SessionStart without SessionEnd
- Gaps in timestamp sequence

### Common Causes
1. **Crash** - Unhandled exception
2. **Force quit** - User killed process
3. **Hook timeout** - Event logger didn't complete
4. **File corruption** - Write failure

### Remediation
- Check for crash logs
- Verify hook timeouts are sufficient
- Monitor disk space
- Add flush after writes

---

## Orphaned Tool Calls

### Description
Tool calls appear without parent context.

### Detection
```bash
# Find PostToolUse without PreToolUse
# (Requires correlating by tool_use_id)
```

### Common Causes
1. **Late hook registration** - Hook started mid-session
2. **Selective capture** - Different capture levels
3. **Trace truncation** - Old events pruned

### Remediation
- Ensure consistent hook configuration
- Use same capture level throughout
- Check retention settings

---

## High Error Rates

### Description
Tool error rate exceeds acceptable threshold (>10%).

### Detection
```bash
# Calculate error rate per tool
cat session.jsonl | jq -s '
  [.[] | select(.event_type == "PostToolUse")] |
  group_by(.tool_name) |
  map({
    tool: .[0].tool_name,
    total: length,
    errors: [.[] | select(.status == "error")] | length,
    error_rate: (([.[] | select(.status == "error")] | length) / length * 100)
  }) |
  sort_by(-.error_rate)
'
```

### Common Causes
1. **Invalid arguments** - Bad input data
2. **Permission issues** - Access denied
3. **Resource not found** - Missing files/endpoints
4. **Validation failures** - Schema mismatches

### Remediation
- Review error messages for patterns
- Fix argument generation
- Check file/resource existence
- Validate inputs before tool calls
