#!/bin/bash

# TRAE IDE Simple File Watcher for GitButler Integration
# Uses fswatch (built into macOS) to monitor file changes

PROJECT_PATH="${1:-$(pwd)}"
HOOK_SCRIPT="$HOME/bin/trae_gitbutler_hook.rb"

echo "🔍 TRAE GitButler Simple Watcher starting..."
echo "📁 Watching: $PROJECT_PATH"
echo "🔧 Hook script: $HOOK_SCRIPT"

# Check if fswatch is available
if ! command -v fswatch &> /dev/null; then
    echo "❌ fswatch not found. Installing via Homebrew..."
    brew install fswatch
fi

# Start watching for file changes
fswatch -r \
    --exclude="\.git/" \
    --exclude="node_modules/" \
    --exclude="\.trae/" \
    --exclude="\.DS_Store" \
    --exclude="\.log$" \
    --exclude="\.tmp$" \
    --exclude="\.swp$" \
    "$PROJECT_PATH" | while read file; do
    
    echo "📝 File changed: $file"
    
    # Determine the action based on file existence
    if [ -f "$file" ]; then
        "$HOOK_SCRIPT" save "$file"
    else
        "$HOOK_SCRIPT" delete "$file"
    fi
done
