#!/bin/bash
# Ralph Mode - Superior Intelligence Review
# Invokes a smarter agent to review changes before commit
# Usage: ralph-review.sh [--staged | --diff <base>]

set -e

RALPH_DIR=".claude/ralph"
REVIEW_LOG="$RALPH_DIR/review.log"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
  echo -e "${BLUE}[ralph-review]${NC} $1"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$REVIEW_LOG"
}

# Get diff to review
get_diff() {
  case "${1:-staged}" in
    --staged)
      git diff --cached
      ;;
    --diff)
      git diff "${2:-HEAD~1}"
      ;;
    *)
      git diff --cached
      ;;
  esac
}

# Generate review prompt
generate_review_prompt() {
  local diff="$1"

  cat << EOF
# Superior Intelligence Review Request

You are reviewing code changes before they are committed. Apply the "Untrusted Actor" pattern - assume the coding agent may have made mistakes.

## Review Criteria

1. **Correctness**: Does the code do what it's supposed to?
2. **Simplicity**: Is this the simplest solution? Any over-engineering?
3. **Security**: Any vulnerabilities introduced?
4. **Performance**: Any obvious performance issues?
5. **Patterns**: Does it follow project conventions?
6. **Tests**: Are changes adequately tested?

## Changes to Review

\`\`\`diff
$diff
\`\`\`

## Your Task

1. Review each changed file
2. List any issues found (CRITICAL, HIGH, MEDIUM, LOW)
3. Suggest specific fixes for CRITICAL/HIGH issues
4. Give overall verdict: APPROVE, REQUEST_CHANGES, or BLOCK

Format your response as:

### Issues Found
- [SEVERITY] file:line - description

### Suggested Fixes
\`\`\`
// specific code fixes
\`\`\`

### Verdict
[APPROVE|REQUEST_CHANGES|BLOCK]

### Summary
[Brief explanation]
EOF
}

main() {
  mkdir -p "$RALPH_DIR"

  log "Starting superior intelligence review..."

  # Get the diff
  local diff=$(get_diff "$@")

  if [[ -z "$diff" ]]; then
    log "No changes to review"
    echo "No staged changes found. Stage changes with 'git add' first."
    exit 0
  fi

  # Count lines changed
  local lines_added=$(echo "$diff" | grep "^+" | grep -v "^+++" | wc -l | tr -d ' ')
  local lines_removed=$(echo "$diff" | grep "^-" | grep -v "^---" | wc -l | tr -d ' ')

  log "Reviewing: +$lines_added -$lines_removed lines"

  # Generate the review prompt
  local prompt=$(generate_review_prompt "$diff")

  # Save prompt for Claude to use
  echo "$prompt" > "$RALPH_DIR/review-prompt.md"

  echo ""
  echo "=============================================="
  echo "  SUPERIOR INTELLIGENCE REVIEW REQUIRED"
  echo "=============================================="
  echo ""
  echo "Changes: +$lines_added -$lines_removed lines"
  echo ""
  echo "Claude MUST now invoke the review agent:"
  echo ""
  echo "  Use Task tool with:"
  echo "    subagent_type: compound-engineering:review:code-simplicity-reviewer"
  echo "    prompt: [contents of $RALPH_DIR/review-prompt.md]"
  echo ""
  echo "Or for security-sensitive changes:"
  echo "    subagent_type: compound-engineering:review:security-sentinel"
  echo ""
  echo "After review approval, proceed with commit."
  echo "=============================================="
  echo ""

  # Return the prompt path
  echo "$RALPH_DIR/review-prompt.md"
}

main "$@"
