#!/bin/bash
# Post Tool Use Hook - Automatic RLHF Learning
#
# This hook runs AFTER Claude completes a tool use.
# It captures success/failure signals for automatic learning.
#
# Hook Data (JSON via stdin):
# {
#   "session_id": "string",
#   "tool_name": "Read|Write|Edit|Bash|...",
#   "tool_input": { ... },
#   "tool_response": { "content": "..." },
#   "tool_use_id": "string",
#   "cwd": "/path/to/project"
# }
#
# IMPORTANT: This enables AUTOMATIC RLHF - no user intervention needed!

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VENV_DIR="$PROJECT_ROOT/.claude/scripts/feedback/venv"
SEMANTIC_MEMORY="$PROJECT_ROOT/.claude/scripts/feedback/semantic-memory-v2.py"
FEEDBACK_LOG="$PROJECT_ROOT/.claude/memory/feedback/feedback-log.jsonl"
METRICS_LOG="$PROJECT_ROOT/.claude/memory/feedback/tool-metrics.jsonl"

# Read hook data from stdin
HOOK_DATA=$(cat)

# Extract fields using jq (if available) or grep
if command -v jq &> /dev/null; then
    TOOL_NAME=$(echo "$HOOK_DATA" | jq -r '.tool_name // "unknown"')
    TOOL_RESPONSE=$(echo "$HOOK_DATA" | jq -r '.tool_response.content // ""' | head -c 500)
    TOOL_USE_ID=$(echo "$HOOK_DATA" | jq -r '.tool_use_id // "unknown"')
else
    # Fallback to grep
    TOOL_NAME=$(echo "$HOOK_DATA" | grep -o '"tool_name"[[:space:]]*:[[:space:]]*"[^"]*"' | cut -d'"' -f4)
    TOOL_RESPONSE=""
    TOOL_USE_ID=""
fi

# Ensure directories exist
mkdir -p "$(dirname "$FEEDBACK_LOG")"
mkdir -p "$(dirname "$METRICS_LOG")"

# Log tool usage metrics (always)
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo "{\"timestamp\": \"$TIMESTAMP\", \"tool_name\": \"$TOOL_NAME\", \"tool_use_id\": \"$TOOL_USE_ID\"}" >> "$METRICS_LOG"

# Detect error patterns in tool response for automatic negative feedback
ERROR_DETECTED=false
ERROR_CONTEXT=""

if echo "$TOOL_RESPONSE" | grep -qi "error\|failed\|exception\|not found\|permission denied\|traceback"; then
    ERROR_DETECTED=true
    ERROR_CONTEXT="Tool $TOOL_NAME returned error: ${TOOL_RESPONSE:0:200}"
fi

# Detect common anti-patterns
if [ "$TOOL_NAME" = "Bash" ]; then
    # Check for dangerous commands that succeeded (shouldn't have been run)
    if echo "$TOOL_RESPONSE" | grep -qi "rm -rf\|git push --force\|drop table"; then
        ERROR_DETECTED=true
        ERROR_CONTEXT="Dangerous command executed: ${TOOL_RESPONSE:0:200}"
    fi
fi

if [ "$TOOL_NAME" = "Write" ] || [ "$TOOL_NAME" = "Edit" ]; then
    # Check for common mistakes in file operations
    TOOL_INPUT=$(echo "$HOOK_DATA" | jq -r '.tool_input // {}' 2>/dev/null || echo "{}")
    FILE_PATH=$(echo "$TOOL_INPUT" | jq -r '.file_path // ""' 2>/dev/null || echo "")

    # Check if editing protected files
    if echo "$FILE_PATH" | grep -qi "\.env\|secrets\|credentials\|\.claude/memory"; then
        ERROR_DETECTED=true
        ERROR_CONTEXT="Edited sensitive file: $FILE_PATH"
    fi
fi

# Validator script
VALIDATOR="$PROJECT_ROOT/.claude/scripts/feedback/validate-feedback.js"

# If error detected, log automatic negative feedback
if [ "$ERROR_DETECTED" = true ]; then
    echo ""
    echo "=================================================="
    echo "AUTO-RLHF: Error pattern detected!"
    echo "=================================================="
    echo "Tool: $TOOL_NAME"
    echo "Context: $ERROR_CONTEXT"
    echo "=================================================="

    # Create feedback entry
    FEEDBACK_ENTRY="{\"timestamp\": \"$TIMESTAMP\", \"feedback\": \"negative\", \"reward\": -1, \"source\": \"auto\", \"tool_name\": \"$TOOL_NAME\", \"context\": \"$ERROR_CONTEXT\", \"tags\": [\"auto-detected\", \"tool-error\", \"$TOOL_NAME\"]}"

    # Validate and auto-correct before logging
    if [ -f "$VALIDATOR" ]; then
        VALIDATED=$(echo "$FEEDBACK_ENTRY" | node "$VALIDATOR" 2>/dev/null)
        if [ -n "$VALIDATED" ]; then
            echo "$VALIDATED" >> "$FEEDBACK_LOG"
        else
            echo "$FEEDBACK_ENTRY" >> "$FEEDBACK_LOG"
        fi
    else
        echo "$FEEDBACK_ENTRY" >> "$FEEDBACK_LOG"
    fi

    # Trigger re-indexing if semantic memory v2 exists
    if [ -f "$SEMANTIC_MEMORY" ] && [ -d "$VENV_DIR" ]; then
        "$VENV_DIR/bin/python3" "$SEMANTIC_MEMORY" --add-feedback \
            --feedback-type negative \
            --feedback-context "$ERROR_CONTEXT" 2>/dev/null &
        # Run in background to not block Claude
    fi
fi

# Detect success patterns for positive reinforcement
SUCCESS_DETECTED=false
if [ "$TOOL_NAME" = "Bash" ]; then
    # Check for successful test runs
    if echo "$TOOL_RESPONSE" | grep -qi "tests passed\|build succeeded\|all checks passed"; then
        SUCCESS_DETECTED=true
        SUCCESS_CONTEXT="Successful: ${TOOL_RESPONSE:0:200}"
    fi
fi

if [ "$SUCCESS_DETECTED" = true ]; then
    FEEDBACK_ENTRY="{\"timestamp\": \"$TIMESTAMP\", \"feedback\": \"positive\", \"reward\": 1, \"source\": \"auto\", \"tool_name\": \"$TOOL_NAME\", \"context\": \"$SUCCESS_CONTEXT\", \"tags\": [\"auto-detected\", \"tool-success\", \"$TOOL_NAME\"]}"

    # Validate and auto-correct before logging
    if [ -f "$VALIDATOR" ]; then
        VALIDATED=$(echo "$FEEDBACK_ENTRY" | node "$VALIDATOR" 2>/dev/null)
        if [ -n "$VALIDATED" ]; then
            echo "$VALIDATED" >> "$FEEDBACK_LOG"
        else
            echo "$FEEDBACK_ENTRY" >> "$FEEDBACK_LOG"
        fi
    else
        echo "$FEEDBACK_ENTRY" >> "$FEEDBACK_LOG"
    fi
fi

# Update knowledge graph periodically (every 10th tool use)
KNOWLEDGE_GRAPH="$PROJECT_ROOT/.claude/scripts/feedback/knowledge-graph.py"
METRICS_COUNT=$(wc -l < "$METRICS_LOG" 2>/dev/null | tr -d ' ' || echo "0")

if [ -f "$KNOWLEDGE_GRAPH" ] && [ -d "$VENV_DIR" ]; then
    # Rebuild graph every 10 tool uses for pattern discovery
    if [ $((METRICS_COUNT % 10)) -eq 0 ] && [ "$METRICS_COUNT" -gt 0 ]; then
        "$VENV_DIR/bin/python3" "$KNOWLEDGE_GRAPH" --build 2>/dev/null &
        # Run in background to not block Claude
    fi
fi

# Exit 0 - hook succeeded, continue normally
exit 0
