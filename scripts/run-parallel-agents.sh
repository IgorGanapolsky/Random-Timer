#!/bin/bash

# TRUE PARALLEL AGENT EXECUTION IN WORKTREES
# This is what makes your system 100% functional

set -e

# Configuration
WORKTREES_BASE="/Users/igorganapolsky/workspace/git/apps/SuperPassword-worktrees"
ORIGINAL_BASE="/Users/igorganapolsky/workspace/git/apps"
LOG_DIR="logs/agents"

# Create log directory
mkdir -p "$LOG_DIR"

echo "🚀 STARTING TRUE PARALLEL AGENT EXECUTION"
echo "=========================================="

# Function to run agent in worktree
run_agent_in_worktree() {
    local worktree="$1"
    local issue_num="$2"
    local log_file="$LOG_DIR/agent-$issue_num.log"
    
    echo "🤖 Starting agent in $worktree for issue #$issue_num"
    
    (
        cd "$worktree"
        
        # Update to latest
        git fetch origin develop
        git reset --hard origin/develop
        
        # Create feature branch
        BRANCH="agent/issue-$issue_num-$(date +%s)"
        git checkout -b "$BRANCH"
        
        # Run Claude agent
        if [ -f "../SuperPassword/scripts/claude-agent.py" ]; then
            python ../SuperPassword/scripts/claude-agent.py \
                --issue "$issue_num" \
                --repo "IgorGanapolsky/SuperPassword" \
                >> "$log_file" 2>&1
        fi
        
        # Push changes
        git push origin "$BRANCH"
        
        # Create PR
        gh pr create \
            --base develop \
            --title "🤖 [Agent] Fix issue #$issue_num" \
            --body "Automated fix for #$issue_num" \
            --label "ai:generated,auto-merge"
            
        echo "✅ Agent completed in $worktree"
    ) &
}

# Map issues to specialized worktrees
echo "📋 Finding work for agents..."

# Security agent
SECURITY_ISSUE=$(gh issue list --state open --label "ai:ready" --label "security" --limit 1 --json number --jq '.[0].number' 2>/dev/null)
if [ ! -z "$SECURITY_ISSUE" ]; then
    if [ -d "$ORIGINAL_BASE/sp-secure-storage" ]; then
        run_agent_in_worktree "$ORIGINAL_BASE/sp-secure-storage" "$SECURITY_ISSUE"
    fi
fi

# Frontend agent
FRONTEND_ISSUE=$(gh issue list --state open --label "ai:ready" --label "frontend" --limit 1 --json number --jq '.[0].number' 2>/dev/null)
if [ ! -z "$FRONTEND_ISSUE" ]; then
    if [ -d "$WORKTREES_BASE/feature-dev" ]; then
        run_agent_in_worktree "$WORKTREES_BASE/feature-dev" "$FRONTEND_ISSUE"
    fi
fi

# Backend agent
BACKEND_ISSUE=$(gh issue list --state open --label "ai:ready" --label "backend" --limit 1 --json number --jq '.[0].number' 2>/dev/null)
if [ ! -z "$BACKEND_ISSUE" ]; then
    if [ -d "$WORKTREES_BASE/bug-fixes" ]; then
        run_agent_in_worktree "$WORKTREES_BASE/bug-fixes" "$BACKEND_ISSUE"
    fi
fi

# Mobile agent
MOBILE_ISSUE=$(gh issue list --state open --label "ai:ready" --label "mobile" --limit 1 --json number --jq '.[0].number' 2>/dev/null)
if [ ! -z "$MOBILE_ISSUE" ]; then
    if [ -d "$ORIGINAL_BASE/sp-biometrics" ]; then
        run_agent_in_worktree "$ORIGINAL_BASE/sp-biometrics" "$MOBILE_ISSUE"
    fi
fi

# AI agent
AI_ISSUE=$(gh issue list --state open --label "ai:ready" --label "ai" --limit 1 --json number --jq '.[0].number' 2>/dev/null)
if [ ! -z "$AI_ISSUE" ]; then
    if [ -d "$ORIGINAL_BASE/sp-ai-intelligence" ]; then
        run_agent_in_worktree "$ORIGINAL_BASE/sp-ai-intelligence" "$AI_ISSUE"
    fi
fi

# Wait for all agents to complete
echo "⏳ Waiting for all agents to complete..."
wait

echo "✅ All agents completed!"
echo ""
echo "📊 Results:"
ls -la "$LOG_DIR"/*.log 2>/dev/null || echo "No logs found"

# Show PR status
echo ""
echo "🔀 New PRs created:"
gh pr list --state open --label "ai:generated" --json number,title --jq '.[] | "#\(.number): \(.title)"'
