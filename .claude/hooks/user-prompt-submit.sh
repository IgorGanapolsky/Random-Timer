#!/bin/bash
# User Prompt Submit Hook - Random Timer
# Detects feedback and task patterns

set -e

SCRIPT_DIR="$(dirname "$0")"
MEMORY_DIR="$SCRIPT_DIR/../memory"

# Read user message from stdin
USER_MESSAGE=$(cat)

# Detect thumbs down
if echo "$USER_MESSAGE" | grep -qi "thumbs down\|👎"; then
    echo ""
    echo "=================================================="
    echo "🚨 THUMBS DOWN DETECTED"
    echo "=================================================="
    echo ""
    echo "Claude MUST:"
    echo "   1. STOP and ask what went wrong"
    echo "   2. APOLOGIZE and explain prevention"
    echo "   3. Fix the issue"
    echo ""
    echo "=================================================="
fi

# Detect thumbs up
if echo "$USER_MESSAGE" | grep -qi "thumbs up\|👍"; then
    echo ""
    echo "=================================================="
    echo "✅ THUMBS UP - Great work!"
    echo "=================================================="
fi

# Output the original message for Claude to process
echo "$USER_MESSAGE"
