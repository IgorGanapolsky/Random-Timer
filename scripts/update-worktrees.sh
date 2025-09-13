#!/bin/bash

# Update all worktrees to latest develop branch
# This enables parallel AI agent development

set -e

YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🔄 Updating all worktrees to latest develop...${NC}\n"

# Get current directory
MAIN_DIR=$(pwd)

# Array of worktrees
WORKTREES=(
    "sp-ai-intelligence:feature/ai-intelligence"
    "sp-biometrics:feature/biometrics"
    "sp-secure-storage:feature/secure-storage"
    "sp-ci-hardening:chore/ci-hardening"
)

# Update main repo first
echo -e "${GREEN}📦 Updating main repository...${NC}"
git fetch origin develop
git pull origin develop --rebase || true

# Update each worktree
for worktree_config in "${WORKTREES[@]}"; do
    IFS=':' read -r worktree branch <<< "$worktree_config"
    worktree_path="../$worktree"
    
    if [ -d "$worktree_path" ]; then
        echo -e "\n${YELLOW}🌳 Updating worktree: $worktree${NC}"
        cd "$worktree_path"
        
        # Fetch latest
        git fetch origin develop
        
        # Check if branch exists
        if git show-ref --verify --quiet "refs/heads/$branch"; then
            git checkout "$branch"
            # Rebase on develop
            git rebase origin/develop || {
                echo -e "${RED}⚠️  Rebase failed for $worktree, resetting to develop${NC}"
                git rebase --abort 2>/dev/null || true
                git checkout -B "$branch" origin/develop
            }
        else
            # Create branch from develop
            git checkout -b "$branch" origin/develop
        fi
        
        echo -e "${GREEN}✅ $worktree updated to latest develop${NC}"
        
        # Show status
        echo "  Branch: $(git branch --show-current)"
        echo "  Last commit: $(git log -1 --oneline)"
        
        cd "$MAIN_DIR"
    else
        echo -e "${RED}❌ Worktree not found: $worktree_path${NC}"
    fi
done

echo -e "\n${GREEN}✨ All worktrees updated!${NC}"

# Show final status
echo -e "\n${YELLOW}📊 Worktree Status:${NC}"
git worktree list

echo -e "\n${YELLOW}💡 Next Steps:${NC}"
echo "1. Assign issues to specific worktrees"
echo "2. Run agents in parallel across worktrees"
echo "3. Monitor progress with: ./scripts/agent-metrics.sh"
