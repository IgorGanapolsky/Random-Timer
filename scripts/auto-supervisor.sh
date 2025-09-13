#!/bin/bash

# Automated Supervisor - Runs everything without human intervention
# Following Anthropic's Claude Code best practices

set -e

# Configuration
LOG_DIR="logs/supervisor"
WORK_DIR="agent_work"
INTERVAL=300  # Check every 5 minutes

# Colors for logging
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Create directories
mkdir -p "$LOG_DIR" "$WORK_DIR"

# Log function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_DIR/supervisor.log"
}

# Function to check and fix issues
fix_stuck_issues() {
    log "🔍 Checking for stuck issues..."
    
    # Find issues stuck in progress for >24 hours
    STUCK_ISSUES=$(gh issue list --state open --label "ai:in-progress" --json number,updatedAt | \
        jq --arg date "$(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -v-24H +%Y-%m-%dT%H:%M:%SZ)" \
        '[.[] | select(.updatedAt < $date) | .number]')
    
    if [ ! -z "$STUCK_ISSUES" ] && [ "$STUCK_ISSUES" != "[]" ]; then
        echo "$STUCK_ISSUES" | jq -r '.[]' | while read issue_num; do
            log "⚠️ Unsticking issue #$issue_num"
            gh issue edit "$issue_num" \
                --remove-label "ai:in-progress" \
                --add-label "ai:ready" \
                --add-label "ai:retry" 2>/dev/null || true
            
            gh issue comment "$issue_num" \
                --body "🔄 **Automated Recovery**: Issue was stuck for >24 hours. Resetting for agent retry." \
                2>/dev/null || true
        done
    fi
}

# Function to trigger orchestrator
trigger_orchestrator() {
    local ready_count=$(gh issue list --state open --label "ai:ready" --json number | jq '. | length')
    
    if [ "$ready_count" -gt 0 ]; then
        log "🚀 Triggering orchestrator for $ready_count ready issues"
        gh workflow run agent-orchestrator.yml \
            --field max_agents=3 \
            --field dry_run=false 2>/dev/null || true
    fi
}

# Function to merge ready PRs
auto_merge_prs() {
    log "🔀 Checking for mergeable PRs..."
    
    # Get PRs with auto-merge label
    PRS=$(gh pr list --state open --label "auto-merge" --json number,mergeable,statusCheckRollup)
    
    echo "$PRS" | jq -c '.[]' | while read pr; do
        PR_NUM=$(echo "$pr" | jq -r '.number')
        MERGEABLE=$(echo "$pr" | jq -r '.mergeable')
        
        if [ "$MERGEABLE" == "MERGEABLE" ] || [ "$MERGEABLE" == "UNKNOWN" ]; then
            # Check if only non-critical checks are failing
            CRITICAL_FAILURES=$(echo "$pr" | jq '.statusCheckRollup | [
                .[] | 
                select(.conclusion == "FAILURE") |
                select(.name != "Sync to Kanban Board") |
                select(.name != "Kanban Board Sync")
            ] | length')
            
            if [ "$CRITICAL_FAILURES" == "0" ]; then
                log "✅ Auto-merging PR #$PR_NUM"
                gh pr merge "$PR_NUM" --squash --delete-branch 2>/dev/null || \
                    log "⚠️ Could not merge PR #$PR_NUM"
            fi
        fi
    done
}

# Function to sync Kanban board
sync_kanban() {
    log "📊 Syncing Kanban board..."
    ./scripts/kanban-manager.sh > "$LOG_DIR/kanban.log" 2>&1 || \
        log "⚠️ Kanban sync failed (non-critical)"
}

# Function to update worktrees
update_worktrees() {
    log "🌳 Updating worktrees..."
    ./scripts/update-worktrees.sh > "$LOG_DIR/worktrees.log" 2>&1 || \
        log "⚠️ Worktree update failed"
}

# Function to generate metrics
generate_metrics() {
    log "📈 Generating metrics..."
    ./scripts/business-metrics.sh > "$LOG_DIR/business-metrics.log" 2>&1
    ./scripts/agent-metrics.sh > "$LOG_DIR/agent-metrics.log" 2>&1
}

# Function to create new issues from backlog
create_issues_from_backlog() {
    log "📝 Checking backlog for new work..."
    
    # Count current open issues
    OPEN_ISSUES=$(gh issue list --state open --json number | jq '. | length')
    
    # If less than 5 issues open, create more
    if [ "$OPEN_ISSUES" -lt 5 ]; then
        log "Creating new issues from backlog..."
        
        # Create feature issues
        if ! gh issue list --state all --search "in:title password strength meter" --json number | jq -e '.[0]' > /dev/null 2>&1; then
            gh issue create \
                --title "🎯 Add password strength meter component" \
                --body "Add visual password strength indicator with real-time feedback" \
                --label "enhancement,frontend,ai:ready"
        fi
        
        if ! gh issue list --state all --search "in:title data export" --json number | jq -e '.[0]' > /dev/null 2>&1; then
            gh issue create \
                --title "📤 Implement data export functionality" \
                --body "Allow users to export passwords as CSV or JSON" \
                --label "enhancement,backend,ai:ready"
        fi
    fi
}

# Function to check system health
check_health() {
    log "🏥 Running health checks..."
    
    # Check GitHub API rate limit
    RATE_LIMIT=$(gh api rate_limit --jq '.resources.core.remaining')
    if [ "$RATE_LIMIT" -lt 100 ]; then
        log "⚠️ Low GitHub API rate limit: $RATE_LIMIT"
        sleep 3600  # Wait an hour
    fi
    
    # Check disk space
    DISK_USAGE=$(df -h . | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$DISK_USAGE" -gt 90 ]; then
        log "⚠️ High disk usage: ${DISK_USAGE}%"
        # Clean up old logs
        find "$LOG_DIR" -name "*.log" -mtime +7 -delete
    fi
}

# Main supervisor loop
main() {
    log "🤖 Automated Supervisor Starting..."
    log "No human intervention required!"
    
    while true; do
        log "=== Starting supervision cycle ==="
        
        # Run all automation tasks
        check_health
        fix_stuck_issues
        trigger_orchestrator
        auto_merge_prs
        sync_kanban
        update_worktrees
        create_issues_from_backlog
        generate_metrics
        
        # Show summary
        log "📊 Summary:"
        log "  Open Issues: $(gh issue list --state open --json number | jq '. | length')"
        log "  Open PRs: $(gh pr list --state open --json number | jq '. | length')"
        log "  Ready for AI: $(gh issue list --state open --label 'ai:ready' --json number | jq '. | length')"
        log "  AI Working: $(gh issue list --state open --label 'ai:in-progress' --json number | jq '. | length')"
        
        log "💤 Sleeping for $INTERVAL seconds..."
        sleep $INTERVAL
    done
}

# Run in background
if [ "$1" == "--daemon" ]; then
    log "Starting in daemon mode..."
    nohup "$0" > "$LOG_DIR/daemon.log" 2>&1 &
    echo $! > "$LOG_DIR/supervisor.pid"
    log "Supervisor running with PID $(cat $LOG_DIR/supervisor.pid)"
else
    main
fi
