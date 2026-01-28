#!/bin/bash
# Ralph Mode - Continuous Iteration Loop
# Runs tests, fixes failures, retries until stable
# Usage: ralph-loop.sh start "<description>" [work-item-id]
#        ralph-loop.sh status
#        ralph-loop.sh stop

set -e

RALPH_DIR=".claude/ralph"
ATTEMPTS_FILE="$RALPH_DIR/ATTEMPTS.md"
STATE_FILE="$RALPH_DIR/state.json"
LOG_FILE="$RALPH_DIR/loop.log"
MAX_ATTEMPTS=10

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
  echo -e "${BLUE}[ralph]${NC} $1"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

error() {
  echo -e "${RED}[ralph]${NC} $1"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" >> "$LOG_FILE"
}

success() {
  echo -e "${GREEN}[ralph]${NC} $1"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS: $1" >> "$LOG_FILE"
}

init_ralph() {
  mkdir -p "$RALPH_DIR"

  local description="$1"
  local work_item="${2:-none}"
  local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

  # Initialize state
  cat > "$STATE_FILE" << EOF
{
  "status": "running",
  "description": "$description",
  "work_item": "$work_item",
  "started_at": "$timestamp",
  "attempt": 0,
  "max_attempts": $MAX_ATTEMPTS,
  "last_error": null,
  "checkpoints": []
}
EOF

  # Initialize ATTEMPTS.md
  cat > "$ATTEMPTS_FILE" << EOF
# Ralph Mode: $description

**Work Item:** $work_item
**Started:** $timestamp
**Status:** 🔄 In Progress

---

## Task Breakdown

<!-- Claude: Break down the task into checkboxes -->

- [ ] Task 1: [Pending]
- [ ] Task 2: [Pending]
- [ ] Task 3: [Pending]

---

## Attempt Log

### Attempt 1
**Time:** $timestamp
**Status:** 🔄 Starting

#### Actions Taken
- Initializing Ralph Mode

#### Test Results
\`\`\`
Pending first run...
\`\`\`

#### Learnings
- [To be filled after attempt]

---

## Final Summary

**Total Attempts:** 0
**Final Status:** In Progress
**Key Learnings:**
- [To be filled on completion]
EOF

  log "Ralph Mode initialized for: $description"
  log "ATTEMPTS file: $ATTEMPTS_FILE"
  log "State file: $STATE_FILE"
}

run_quality_checks() {
  log "Running quality checks..."

  local result=0
  local output=""

  # TypeScript check
  log "  → TypeScript compilation..."
  if ! output=$(npm run compile 2>&1); then
    error "TypeScript failed"
    echo "$output"
    return 1
  fi

  # Lint check
  log "  → ESLint..."
  if ! output=$(npm run lint:check 2>&1); then
    error "Lint failed"
    echo "$output"
    return 1
  fi

  # Tests
  log "  → Running tests..."
  if ! output=$(npm test 2>&1); then
    error "Tests failed"
    echo "$output"
    return 1
  fi

  success "All quality checks passed!"
  return 0
}

update_attempt() {
  local attempt=$1
  local status=$2
  local error_msg="${3:-}"

  # Update state.json
  local tmp=$(mktemp)
  jq --arg status "$status" \
     --arg attempt "$attempt" \
     --arg error "$error_msg" \
     '.status = $status | .attempt = ($attempt | tonumber) | .last_error = $error' \
     "$STATE_FILE" > "$tmp" && mv "$tmp" "$STATE_FILE"
}

add_checkpoint() {
  local message="$1"
  local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

  local tmp=$(mktemp)
  jq --arg msg "$message" \
     --arg ts "$timestamp" \
     '.checkpoints += [{"message": $msg, "timestamp": $ts}]' \
     "$STATE_FILE" > "$tmp" && mv "$tmp" "$STATE_FILE"

  log "Checkpoint: $message"
}

get_status() {
  if [[ ! -f "$STATE_FILE" ]]; then
    echo "No active Ralph session"
    return 1
  fi

  cat "$STATE_FILE" | jq .
  echo ""
  echo "ATTEMPTS file: $ATTEMPTS_FILE"
}

stop_ralph() {
  if [[ ! -f "$STATE_FILE" ]]; then
    error "No active Ralph session to stop"
    return 1
  fi

  local tmp=$(mktemp)
  jq '.status = "stopped"' "$STATE_FILE" > "$tmp" && mv "$tmp" "$STATE_FILE"

  log "Ralph Mode stopped"
}

# Main loop - this is called by Claude, not run automatically
main_loop() {
  local attempt=1

  while [[ $attempt -le $MAX_ATTEMPTS ]]; do
    log "=== Attempt $attempt of $MAX_ATTEMPTS ==="

    update_attempt "$attempt" "running"

    if run_quality_checks; then
      update_attempt "$attempt" "success"
      success "All checks passed on attempt $attempt!"

      # Update ATTEMPTS.md with success
      add_checkpoint "All quality checks passed"

      return 0
    else
      update_attempt "$attempt" "failed" "Quality checks failed"
      error "Attempt $attempt failed, will retry..."

      # Give Claude a chance to fix
      add_checkpoint "Attempt $attempt failed - awaiting fixes"

      ((attempt++))

      # Wait for fixes before next attempt
      sleep 2
    fi
  done

  error "Max attempts ($MAX_ATTEMPTS) reached without success"
  update_attempt "$MAX_ATTEMPTS" "max_attempts_reached"
  return 1
}

# Command handling
case "${1:-}" in
  start)
    if [[ -z "${2:-}" ]]; then
      echo "Usage: ralph-loop.sh start \"<description>\" [work-item-id]"
      exit 1
    fi
    init_ralph "$2" "${3:-}"
    ;;
  loop)
    main_loop
    ;;
  status)
    get_status
    ;;
  stop)
    stop_ralph
    ;;
  checkpoint)
    add_checkpoint "${2:-Manual checkpoint}"
    ;;
  *)
    echo "Ralph Mode - Continuous Iteration Loop"
    echo ""
    echo "Usage:"
    echo "  ralph-loop.sh start \"<description>\" [work-item-id]  - Start new session"
    echo "  ralph-loop.sh loop                                   - Run test/fix loop"
    echo "  ralph-loop.sh status                                 - Show current status"
    echo "  ralph-loop.sh stop                                   - Stop session"
    echo "  ralph-loop.sh checkpoint \"<message>\"                - Add checkpoint"
    ;;
esac
