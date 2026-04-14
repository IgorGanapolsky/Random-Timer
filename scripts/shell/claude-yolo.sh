#!/bin/bash
# claude-yolo: run claude in full yolo permissions mode
# Warning: This bypasses all permission checks. Use with caution.
claude --dangerously-skip-permissions "$@"
