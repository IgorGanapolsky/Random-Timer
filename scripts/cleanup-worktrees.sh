#!/bin/bash

# Worktree Cleanup Script
# Forces removal of all worktrees and their branches

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🧹 Cleaning up worktrees${NC}"
echo "======================="

# Get main repo path
MAIN_REPO="$(pwd)"
echo -e "${YELLOW}Main repo: $MAIN_REPO${NC}"

# List all worktrees
echo -e "\n${BLUE}Current worktrees:${NC}"
git worktree list

# Force remove each worktree
echo -e "\n${YELLOW}Removing worktrees...${NC}"

remove_worktree() {
    local path=$1
    local name=$(basename "$path")
    
    echo -e "\nProcessing: $name"
    
    # Remove the .git file to unlink
    rm -f "$path/.git" 2>/dev/null || true
    
    # Remove directory
    rm -rf "$path" 2>/dev/null || true
    
    # Remove from git worktree list
    git worktree prune
    
    echo -e "${GREEN}✓ Removed $name${NC}"
}

# Remove specific worktrees
remove_worktree "../sp-ci-hardening"
remove_worktree "../sp-ai-intelligence"
remove_worktree "../sp-biometrics"
remove_worktree "../sp-secure-storage"
remove_worktree "../SuperPassword-worktrees/bug-fixes"
remove_worktree "../SuperPassword-worktrees/docs"
remove_worktree "../SuperPassword-worktrees/feature-dev"
remove_worktree "../SuperPassword-worktrees/refactoring"
remove_worktree "../SuperPassword-worktrees/testing"

# Remove parent directory if empty
rmdir "../SuperPassword-worktrees" 2>/dev/null || true

# Clean up branches
echo -e "\n${BLUE}Cleaning up branches...${NC}"

# Switch to develop
git checkout develop

# Delete local branches
echo "Removing local branches..."
git branch | grep -v "develop\|main" | xargs git branch -D 2>/dev/null || true

# Delete remote branches
echo "Removing remote branches..."
git fetch origin
git remote prune origin
for branch in $(git branch -r | grep -v 'main\|develop\|HEAD' | sed 's/origin\///'); do
    git push origin --delete "$branch" 2>/dev/null || true
done

# Show final state
echo -e "\n${GREEN}✅ Cleanup complete!${NC}"
echo -e "\n${BLUE}Remaining worktrees:${NC}"
git worktree list

echo -e "\n${BLUE}Remaining branches:${NC}"
git branch -a