#!/bin/bash
# 2026 Standard Git Hygiene Script
# CTO Mission: Purge stale worktrees and merged branches.

echo "--- MISSION: GIT HYGIENE ---"

# 1. Prune dangling worktrees (metadata only)
git worktree prune
echo "✓ Dangling worktree metadata pruned."

# 2. Fetch and prune remote-tracking branches
git fetch --prune
echo "✓ Remote branches pruned."

# 3. Identify and remove worktrees where the branch is merged into develop
CURRENT_DIR=$(pwd)
DEVELOP_SHA=$(git rev-parse develop)

git worktree list --porcelain | grep "^worktree" | cut -d' ' -f2 | while read -r WT_PATH; do
    if [[ "$WT_PATH" == "$CURRENT_DIR" ]]; then
        continue # Don't nuke the current active one
    fi
    
    cd "$WT_PATH" 2>/dev/null || continue
    BRANCH=$(git branch --show-current)
    
    # Check if branch is fully merged into develop
    if git merge-base --is-ancestor HEAD develop && [[ "$BRANCH" != "develop" && "$BRANCH" != "main" ]]; then
        echo "Pruning merged worktree: $WT_PATH (Branch: $BRANCH)"
        cd "$CURRENT_DIR"
        git worktree remove --force "$WT_PATH"
    fi
    cd "$CURRENT_DIR"
done

# 4. Delete local branches whose remote is 'gone'
git branch -vv | grep ': gone]' | awk '{print $1}' | while read -r GONE_BRANCH; do
    echo "Deleting stale local branch: $GONE_BRANCH"
    git branch -D "$GONE_BRANCH"
done

# 5. Garbage Collection
git gc --prune=now --quiet
echo "✓ Garbage collection complete."

echo "--- HYGIENE MISSION COMPLETE ---"
