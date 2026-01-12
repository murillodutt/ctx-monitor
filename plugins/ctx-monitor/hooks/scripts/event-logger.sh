#!/bin/bash
# event-logger.sh - Main event logging script for ctx-monitor
# Logs events to JSONL format in .claude/ctx-monitor/traces/
# Supports per-project configuration via .claude/ctx-monitor.local.md

set -euo pipefail

# Read input from stdin
input=$(cat)

# Extract common fields
session_id=$(echo "$input" | jq -r '.session_id // "unknown"')
hook_event=$(echo "$input" | jq -r '.hook_event_name // "unknown"')
cwd=$(echo "$input" | jq -r '.cwd // "."')

# ============================================
# Per-project configuration check
# ============================================
config_file="${cwd}/.claude/ctx-monitor.local.md"

# Function to extract YAML value from frontmatter
get_config_value() {
  local key="$1"
  local default="$2"
  if [ -f "$config_file" ]; then
    # Extract value from YAML frontmatter
    value=$(sed -n '/^---$/,/^---$/p' "$config_file" | grep "^${key}:" | head -1 | sed "s/^${key}:[[:space:]]*//" | tr -d '"' | tr -d "'")
    if [ -n "$value" ]; then
      echo "$value"
      return
    fi
  fi
  echo "$default"
}

# Check if ctx-monitor is enabled for this project
enabled=$(get_config_value "enabled" "true")
if [ "$enabled" = "false" ]; then
  # ctx-monitor is disabled for this project, exit silently
  exit 0
fi

# Get log level configuration
log_level=$(get_config_value "log_level" "medium")

# Check if this event type should be logged based on log_level
case "$log_level" in
  "minimal")
    # Only log session lifecycle events
    case "$hook_event" in
      "SessionStart"|"SessionEnd"|"Stop")
        # Continue logging
        ;;
      *)
        # Skip this event
        exit 0
        ;;
    esac
    ;;
  "full"|"medium")
    # Log all events (medium is default)
    ;;
esac

# Check events filter from config (if specified)
if [ -f "$config_file" ]; then
  # Check if events list is specified and if current event is in it
  events_section=$(sed -n '/^events:/,/^[a-z]/p' "$config_file" | grep -E "^\s*-\s*" | sed 's/.*-\s*//' | tr -d ' ')
  if [ -n "$events_section" ]; then
    if ! echo "$events_section" | grep -q "^${hook_event}$"; then
      # Event not in the allowed list, skip
      exit 0
    fi
  fi
fi

# ============================================
# Continue with event logging
# ============================================
# Generate ISO8601 timestamp with milliseconds (cross-platform)
# BSD date (macOS) doesn't support %N, so we detect and use appropriate method
generate_timestamp() {
  if command -v gdate >/dev/null 2>&1; then
    # GNU date available (e.g., via coreutils on macOS)
    gdate -u +"%Y-%m-%dT%H:%M:%S.%3NZ"
  elif date --version >/dev/null 2>&1; then
    # GNU date (Linux)
    date -u +"%Y-%m-%dT%H:%M:%S.%3NZ"
  else
    # BSD date (macOS) - use perl for milliseconds
    perl -MTime::HiRes=gettimeofday -MPOSIX=strftime -e '
      my ($sec, $usec) = gettimeofday();
      my $ms = int($usec / 1000);
      print strftime("%Y-%m-%dT%H:%M:%S", gmtime($sec)) . sprintf(".%03dZ", $ms);
    ' 2>/dev/null || date -u +"%Y-%m-%dT%H:%M:%S.000Z"
  fi
}
timestamp=$(generate_timestamp)

# Determine trace directory (project-local)
trace_dir="${cwd}/.claude/ctx-monitor/traces"
mkdir -p "$trace_dir"

# Session file
session_file="${trace_dir}/session_${session_id}.jsonl"

# Generate event ID
event_id=$(uuidgen 2>/dev/null || cat /proc/sys/kernel/random/uuid 2>/dev/null || echo "evt_$(date +%s%N)")

# Build base event
base_event=$(jq -n \
  --arg event_id "$event_id" \
  --arg session_id "$session_id" \
  --arg timestamp "$timestamp" \
  --arg event_type "$hook_event" \
  '{
    event_id: $event_id,
    session_id: $session_id,
    timestamp: $timestamp,
    event_type: $event_type
  }')

# Add event-specific fields based on hook type
case "$hook_event" in
  "PreToolUse"|"PostToolUse")
    tool_name=$(echo "$input" | jq -r '.tool_name // "unknown"')
    tool_input=$(echo "$input" | jq -c '.tool_input // {}')

    # Truncate args_preview to 500 chars
    args_preview=$(echo "$tool_input" | head -c 500)

    # For PostToolUse, capture result info
    if [ "$hook_event" = "PostToolUse" ]; then
      tool_result=$(echo "$input" | jq -c '.tool_result // null')
      result_preview=$(echo "$tool_result" | head -c 500)

      # Determine status from result
      has_error=$(echo "$tool_result" | jq -r 'if type == "object" then (.error // .is_error // false) else false end')
      if [ "$has_error" = "true" ]; then
        status="error"
        error_msg=$(echo "$tool_result" | jq -r '.error // .message // "Unknown error"' | head -c 200)
      else
        status="success"
        error_msg=""
      fi

      base_event=$(echo "$base_event" | jq \
        --arg tool_name "$tool_name" \
        --arg args_preview "$args_preview" \
        --arg status "$status" \
        --arg error_message "$error_msg" \
        --arg result_preview "$result_preview" \
        '. + {
          tool_name: $tool_name,
          args_preview: $args_preview,
          status: $status,
          error_message: $error_message,
          result_preview: $result_preview
        }')
    else
      # PreToolUse - pending status
      base_event=$(echo "$base_event" | jq \
        --arg tool_name "$tool_name" \
        --arg args_preview "$args_preview" \
        '. + {
          tool_name: $tool_name,
          args_preview: $args_preview,
          status: "pending"
        }')
    fi
    ;;

  "SubagentStop"|"Stop")
    reason=$(echo "$input" | jq -r '.reason // "completed"')
    base_event=$(echo "$base_event" | jq \
      --arg reason "$reason" \
      '. + {reason: $reason, status: "completed"}')
    ;;

  "SessionStart")
    base_event=$(echo "$base_event" | jq \
      --arg cwd "$cwd" \
      '. + {cwd: $cwd, status: "started"}')
    ;;

  "SessionEnd")
    base_event=$(echo "$base_event" | jq '. + {status: "ended"}')
    ;;

  "UserPromptSubmit")
    # Capture user prompt for analysis
    user_prompt=$(echo "$input" | jq -r '.user_prompt // ""')
    prompt_preview=$(echo "$user_prompt" | head -c 500)
    prompt_length=${#user_prompt}
    base_event=$(echo "$base_event" | jq \
      --arg prompt_preview "$prompt_preview" \
      --argjson prompt_length "$prompt_length" \
      '. + {
        prompt_preview: $prompt_preview,
        prompt_length: $prompt_length,
        status: "submitted"
      }')
    ;;

  "PreCompact")
    # Capture context before compaction
    transcript_path=$(echo "$input" | jq -r '.transcript_path // ""')
    base_event=$(echo "$base_event" | jq \
      --arg transcript_path "$transcript_path" \
      '. + {
        transcript_path: $transcript_path,
        status: "compacting"
      }')
    ;;

  "Notification")
    # Capture notification details
    notification_type=$(echo "$input" | jq -r '.type // "unknown"')
    notification_message=$(echo "$input" | jq -r '.message // ""' | head -c 300)
    base_event=$(echo "$base_event" | jq \
      --arg notification_type "$notification_type" \
      --arg notification_message "$notification_message" \
      '. + {
        notification_type: $notification_type,
        notification_message: $notification_message,
        status: "notified"
      }')
    ;;

  *)
    # Unknown event type - log with minimal info
    base_event=$(echo "$base_event" | jq '. + {status: "unknown"}')
    ;;
esac

# Append to session trace file (compact JSON, one line per event)
echo "$base_event" | jq -c '.' >> "$session_file"

# Update sessions index
sessions_index="${trace_dir}/sessions.json"
if [ ! -f "$sessions_index" ]; then
  echo '{"sessions": []}' > "$sessions_index"
fi

# Check if session already in index
session_exists=$(jq --arg sid "$session_id" '.sessions | map(select(.session_id == $sid)) | length > 0' "$sessions_index")

if [ "$session_exists" = "false" ]; then
  # Add new session to index
  jq --arg sid "$session_id" \
     --arg start "$timestamp" \
     --arg cwd "$cwd" \
     '.sessions += [{session_id: $sid, started_at: $start, cwd: $cwd, event_count: 1}]' \
     "$sessions_index" > "${sessions_index}.tmp" && mv "${sessions_index}.tmp" "$sessions_index"
else
  # Update event count
  jq --arg sid "$session_id" \
     '(.sessions[] | select(.session_id == $sid) | .event_count) += 1' \
     "$sessions_index" > "${sessions_index}.tmp" && mv "${sessions_index}.tmp" "$sessions_index"
fi

# Output success (no output to transcript by default)
exit 0
