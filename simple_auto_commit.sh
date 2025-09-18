#!/bin/bash

# Dead Simple Auto-Commit Script
# Just watches files and commits to git - no fancy stuff

PROJECT_DIR="${1:-$(pwd)}"
echo "🔍 Watching $PROJECT_DIR for changes..."

# Kill any existing watchers
pkill -f "fswatch.*$PROJECT_DIR" 2>/dev/null

# Simple file watcher that just commits to git
fswatch -r \
    --exclude="\.git/" \
    --exclude="node_modules/" \
    --exclude="\.DS_Store" \
    "$PROJECT_DIR" | while read file; do
    
    echo "📝 File changed: $file"
    
    cd "$PROJECT_DIR"
    git add .
    git commit -m "Auto-commit: $(basename "$file") changed at $(date)"
    
    echo "✅ Committed to git"
done
