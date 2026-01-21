#!/bin/bash
# Commit Middleware Hook - Auto-injects AB# from branch name
# Uses Claude Code v2.1.0 updatedInput feature for middleware behavior
#
# This hook intercepts git commit commands and adds Azure DevOps work item
# references automatically based on the branch name.
#
# Input: Tool call JSON from stdin (CLAUDE_TOOL_INPUT env var)
# Output: JSON with optional "updatedInput" field to modify the commit message

set -e

# Read the tool input
TOOL_INPUT="${CLAUDE_TOOL_INPUT:-}"

# Only process Bash tool calls that are git commits
if [[ "$CLAUDE_TOOL_NAME" != "Bash" ]]; then
    exit 0
fi

# Check if this is a git commit command
if ! echo "$TOOL_INPUT" | grep -q "git commit"; then
    exit 0
fi

# Get current branch name
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")

# Extract work item ID from branch name
# Supports: feature/1234567-desc, bugfix/1234567-desc, hotfix/1234567-desc, etc.
WORK_ITEM_ID=$(echo "$BRANCH" | grep -oE '^(feature|bugfix|hotfix|task|pbi|spike|chore|refactor)/([0-9]+)' | grep -oE '[0-9]+' || echo "")

if [[ -z "$WORK_ITEM_ID" ]]; then
    # No work item ID in branch, skip
    exit 0
fi

# Check if commit message already has AB#
if echo "$TOOL_INPUT" | grep -qE "AB#[0-9]+"; then
    # Already has AB#, skip
    exit 0
fi

# Log the middleware action
echo "🔗 Middleware: Auto-adding AB#$WORK_ITEM_ID from branch $BRANCH"

# Output the middleware result with updatedInput
# This tells Claude Code to modify the commit command
cat << EOF
{
  "decision": "ask",
  "message": "Auto-adding AB#$WORK_ITEM_ID work item reference from branch name",
  "updatedInput": {
    "command": "$(echo "$TOOL_INPUT" | sed "s/git commit -m \"/git commit -m \"AB#$WORK_ITEM_ID - /")"
  }
}
EOF
