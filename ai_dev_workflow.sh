#!/bin/bash

# AI Development Workflow Manager
# CTO-approved simple solution

set -e

PROJECT_DIR="$(pwd)"
BRANCH_PREFIX="ai-session"
SESSION_ID="$(date +%Y%m%d-%H%M%S)"

echo "🤖 AI Development Workflow Manager"
echo "📁 Project: $PROJECT_DIR"
echo "🆔 Session: $SESSION_ID"

# Function to create AI session branch
create_ai_branch() {
    local branch_name="${BRANCH_PREFIX}-${SESSION_ID}"
    echo "🌿 Creating AI session branch: $branch_name"
    
    git checkout -b "$branch_name" 2>/dev/null || {
        echo "⚠️  Branch exists, switching to it"
        git checkout "$branch_name"
    }
    
    echo "✅ Ready for AI development on branch: $branch_name"
}

# Function to commit AI changes
commit_ai_changes() {
    local message="${1:-AI changes - session $SESSION_ID}"
    
    echo "📝 Committing AI changes..."
    git add .
    
    if git diff --staged --quiet; then
        echo "ℹ️  No changes to commit"
        return 0
    fi
    
    git commit -m "$message"
    echo "✅ Changes committed: $message"
    
    # Show what was committed
    echo "📋 Files changed:"
    git diff --name-only HEAD~1 HEAD | sed 's/^/  - /'
}

# Function to finish AI session
finish_ai_session() {
    local current_branch=$(git branch --show-current)
    
    echo "🏁 Finishing AI session on branch: $current_branch"
    
    # Final commit if there are changes
    if ! git diff --quiet || ! git diff --staged --quiet; then
        commit_ai_changes "Final AI session commit"
    fi
    
    echo "✅ AI session complete!"
    echo "💡 Next steps:"
    echo "   1. Review changes in GitButler"
    echo "   2. Merge branch when ready: git checkout main && git merge $current_branch"
    echo "   3. Or use GitButler to manage the merge visually"
}

# Main command handling
case "${1:-start}" in
    "start")
        create_ai_branch
        ;;
    "commit")
        commit_ai_changes "$2"
        ;;
    "finish")
        finish_ai_session
        ;;
    "auto")
        echo "🔄 Starting auto-commit mode..."
        create_ai_branch
        
        # Simple file watcher for auto-commits
        fswatch -r \
            --exclude="\.git/" \
            --exclude="node_modules/" \
            --exclude="\.DS_Store" \
            --exclude="\.log$" \
            "$PROJECT_DIR" | while read file; do
            
            echo "📝 File changed: $(basename "$file")"
            sleep 1  # Debounce rapid changes
            commit_ai_changes "Auto: $(basename "$file") modified"
        done
        ;;
    *)
        echo "Usage: $0 {start|commit|finish|auto}"
        echo ""
        echo "Commands:"
        echo "  start  - Create new AI session branch"
        echo "  commit - Commit current changes"
        echo "  finish - Finish AI session"
        echo "  auto   - Start with auto-commit on file changes"
        exit 1
        ;;
esac
