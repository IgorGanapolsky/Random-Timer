#!/bin/bash

# AI Agent Performance Metrics Dashboard
# Tracks velocity, success rates, and code quality for autonomous agents

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BOLD}${CYAN}🤖 AI Agent Performance Metrics Dashboard${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}\n"

# Function to get time difference in human-readable format
time_diff() {
    local start=$1
    local end=${2:-$(date -u +%s)}
    local diff=$((end - start))
    
    if [ $diff -lt 60 ]; then
        echo "${diff}s"
    elif [ $diff -lt 3600 ]; then
        echo "$((diff / 60))m $((diff % 60))s"
    elif [ $diff -lt 86400 ]; then
        echo "$((diff / 3600))h $((diff % 3600 / 60))m"
    else
        echo "$((diff / 86400))d $((diff % 86400 / 3600))h"
    fi
}

# 1. Agent Activity Overview
echo -e "${BOLD}📊 Agent Activity Overview${NC}"
echo -e "${BLUE}─────────────────────────────────────${NC}"

# Count of AI-labeled issues
total_issues=$(gh issue list --state all --label "ai:ready,ai:in-progress,ai:review-needed,ai:completed" --json number | jq '. | length')
ready_issues=$(gh issue list --state open --label "ai:ready" --json number | jq '. | length')
in_progress=$(gh issue list --state open --label "ai:in-progress" --json number | jq '. | length')
review_needed=$(gh issue list --state open --label "ai:review-needed" --json number | jq '. | length')
completed=$(gh issue list --state all --label "ai:completed" --json number | jq '. | length')

echo -e "📋 Total AI-managed issues: ${BOLD}$total_issues${NC}"
echo -e "  ✅ Ready: ${GREEN}$ready_issues${NC}"
echo -e "  🔄 In Progress: ${YELLOW}$in_progress${NC}"
echo -e "  👀 Review Needed: ${MAGENTA}$review_needed${NC}"
echo -e "  ✨ Completed: ${CYAN}$completed${NC}"
echo

# 2. Pull Request Metrics
echo -e "${BOLD}🔀 Pull Request Metrics${NC}"
echo -e "${BLUE}─────────────────────────────────────${NC}"

# AI-generated PRs
ai_prs=$(gh pr list --state all --label "ai:generated" --json number,state,createdAt,mergedAt,closedAt | jq '.')
total_ai_prs=$(echo "$ai_prs" | jq '. | length')
open_ai_prs=$(echo "$ai_prs" | jq '[.[] | select(.state == "OPEN")] | length')
merged_ai_prs=$(echo "$ai_prs" | jq '[.[] | select(.state == "MERGED")] | length')
closed_ai_prs=$(echo "$ai_prs" | jq '[.[] | select(.state == "CLOSED" and .mergedAt == null)] | length')

echo -e "🤖 Total AI-generated PRs: ${BOLD}$total_ai_prs${NC}"
echo -e "  📂 Open: ${GREEN}$open_ai_prs${NC}"
echo -e "  ✅ Merged: ${CYAN}$merged_ai_prs${NC}"
echo -e "  ❌ Closed (not merged): ${RED}$closed_ai_prs${NC}"

# Success rate
if [ "$total_ai_prs" -gt 0 ]; then
    success_rate=$(echo "scale=1; $merged_ai_prs * 100 / $total_ai_prs" | bc)
    echo -e "  📈 Success Rate: ${BOLD}${success_rate}%${NC}"
fi
echo

# 3. Workflow Execution Metrics
echo -e "${BOLD}⚙️  Workflow Execution Metrics${NC}"
echo -e "${BLUE}─────────────────────────────────────${NC}"

# Agent Orchestrator runs
orchestrator_runs=$(gh run list --workflow=agent-orchestrator.yml --limit 20 --json status,conclusion,createdAt)
total_orchestrator=$(echo "$orchestrator_runs" | jq '. | length')
successful_orchestrator=$(echo "$orchestrator_runs" | jq '[.[] | select(.conclusion == "success")] | length')
failed_orchestrator=$(echo "$orchestrator_runs" | jq '[.[] | select(.conclusion == "failure")] | length')

echo -e "🎯 Agent Orchestrator (last 20 runs):"
echo -e "  Total: $total_orchestrator | ✅ Success: ${GREEN}$successful_orchestrator${NC} | ❌ Failed: ${RED}$failed_orchestrator${NC}"

# Agent Executor runs
executor_runs=$(gh run list --workflow=agent-executor.yml --limit 20 --json status,conclusion,createdAt 2>/dev/null || echo "[]")
if [ "$executor_runs" != "[]" ]; then
    total_executor=$(echo "$executor_runs" | jq '. | length')
    successful_executor=$(echo "$executor_runs" | jq '[.[] | select(.conclusion == "success")] | length')
    failed_executor=$(echo "$executor_runs" | jq '[.[] | select(.conclusion == "failure")] | length')
    
    echo -e "🤖 Agent Executor (last 20 runs):"
    echo -e "  Total: $total_executor | ✅ Success: ${GREEN}$successful_executor${NC} | ❌ Failed: ${RED}$failed_executor${NC}"
fi
echo

# 4. Velocity Metrics
echo -e "${BOLD}⚡ Velocity Metrics${NC}"
echo -e "${BLUE}─────────────────────────────────────${NC}"

# Average time to complete issues (last 10 completed)
completed_issues=$(gh issue list --state closed --label "ai:completed" --limit 10 --json number,createdAt,closedAt)

if [ "$(echo "$completed_issues" | jq '. | length')" -gt 0 ]; then
    total_time=0
    count=0
    
    while read -r issue; do
        created=$(echo "$issue" | jq -r '.createdAt')
        closed=$(echo "$issue" | jq -r '.closedAt')
        
        if [ "$closed" != "null" ]; then
            created_ts=$(date -u -j -f "%Y-%m-%dT%H:%M:%SZ" "$created" +%s 2>/dev/null || date -u -d "$created" +%s)
            closed_ts=$(date -u -j -f "%Y-%m-%dT%H:%M:%SZ" "$closed" +%s 2>/dev/null || date -u -d "$closed" +%s)
            time_taken=$((closed_ts - created_ts))
            total_time=$((total_time + time_taken))
            count=$((count + 1))
        fi
    done < <(echo "$completed_issues" | jq -c '.[]')
    
    if [ $count -gt 0 ]; then
        avg_time=$((total_time / count))
        avg_hours=$((avg_time / 3600))
        echo -e "⏱️  Average completion time: ${BOLD}${avg_hours} hours${NC}"
    fi
fi

# Issues completed in last 7 days
seven_days_ago=$(date -u -v-7d +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -d "7 days ago" +"%Y-%m-%dT%H:%M:%SZ")
recent_completed=$(gh issue list --state closed --label "ai:completed" --json number,closedAt | \
    jq --arg date "$seven_days_ago" '[.[] | select(.closedAt > $date)] | length')

echo -e "📈 Issues completed (last 7 days): ${BOLD}$recent_completed${NC}"
echo

# 5. Code Quality Metrics
echo -e "${BOLD}✨ Code Quality Indicators${NC}"
echo -e "${BLUE}─────────────────────────────────────${NC}"

# Check recent AI PRs for test coverage and linting
recent_ai_prs=$(gh pr list --state all --label "ai:generated" --limit 5 --json number,title,statusCheckRollup)

passed_checks=0
failed_checks=0

while read -r pr; do
    checks=$(echo "$pr" | jq '.statusCheckRollup')
    if [ "$checks" != "null" ] && [ "$checks" != "[]" ]; then
        pr_passed=$(echo "$checks" | jq '[.[] | select(.conclusion == "SUCCESS" or .state == "SUCCESS")] | length')
        pr_failed=$(echo "$checks" | jq '[.[] | select(.conclusion == "FAILURE" or .state == "FAILURE")] | length')
        passed_checks=$((passed_checks + pr_passed))
        failed_checks=$((failed_checks + pr_failed))
    fi
done < <(echo "$recent_ai_prs" | jq -c '.[]')

total_checks=$((passed_checks + failed_checks))
if [ $total_checks -gt 0 ]; then
    check_pass_rate=$(echo "scale=1; $passed_checks * 100 / $total_checks" | bc)
    echo -e "✅ CI Check Pass Rate: ${BOLD}${check_pass_rate}%${NC} ($passed_checks/$total_checks)"
fi

# 6. Active Worktrees
echo -e "\n${BOLD}🌳 Active Git Worktrees${NC}"
echo -e "${BLUE}─────────────────────────────────────${NC}"

worktrees=$(git worktree list)
worktree_count=$(echo "$worktrees" | wc -l)
echo -e "📁 Total worktrees: ${BOLD}$worktree_count${NC}"
echo "$worktrees" | while read -r line; do
    path=$(echo "$line" | awk '{print $1}')
    branch=$(echo "$line" | sed 's/.*\[\(.*\)\]/\1/')
    dirname=$(basename "$path")
    echo -e "  └─ ${CYAN}$dirname${NC} → ${branch}"
done

# 7. Recommendations
echo -e "\n${BOLD}💡 Recommendations${NC}"
echo -e "${BLUE}─────────────────────────────────────${NC}"

if [ "$ready_issues" -gt 0 ]; then
    echo -e "• ${YELLOW}$ready_issues issues${NC} are ready for AI agents to pick up"
fi

if [ "$in_progress" -gt 3 ]; then
    echo -e "• Consider monitoring ${YELLOW}$in_progress in-progress issues${NC} for potential bottlenecks"
fi

if [ "$open_ai_prs" -gt 2 ]; then
    echo -e "• ${YELLOW}$open_ai_prs AI-generated PRs${NC} are open and may need review"
fi

if [ "$failed_checks" -gt "$passed_checks" ] && [ "$total_checks" -gt 0 ]; then
    echo -e "• ${RED}CI checks are failing frequently${NC} - consider reviewing test stability"
fi

echo -e "\n${GREEN}✨ Dashboard generated at $(date '+%Y-%m-%d %H:%M:%S')${NC}"
