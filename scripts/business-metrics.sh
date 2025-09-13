#!/bin/bash

# Business Metrics Dashboard - Track ARR, velocity, and agent performance
# Path to $10M ARR with AI agents

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BOLD}${CYAN}💰 App Empire Business Dashboard${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}\n"

# Business Constants (adjust based on your actuals)
PRICE_PER_USER_MONTHLY=5.99
ENTERPRISE_PRICE=49.99
CONVERSION_RATE=0.02  # 2% free to paid
CAC=43  # Customer acquisition cost
CURRENT_USERS=100  # Update with actual
PAYING_USERS=2  # Update with actual

# Calculate current metrics
CURRENT_MRR=$(echo "$PAYING_USERS * $PRICE_PER_USER_MONTHLY" | bc)
CURRENT_ARR=$(echo "$CURRENT_MRR * 12" | bc)
LTV=$(echo "$PRICE_PER_USER_MONTHLY * 12 * 3" | bc)  # 3 year average

echo -e "${BOLD}📊 Current Business Metrics${NC}"
echo -e "${BLUE}─────────────────────────────────────${NC}"
echo -e "💵 MRR: ${GREEN}\$$CURRENT_MRR${NC}"
echo -e "📈 ARR: ${GREEN}\$$CURRENT_ARR${NC}"
echo -e "👥 Total Users: ${BOLD}$CURRENT_USERS${NC}"
echo -e "💳 Paying Users: ${GREEN}$PAYING_USERS${NC}"
echo -e "🔄 Conversion Rate: ${YELLOW}$(echo "scale=1; $PAYING_USERS * 100 / $CURRENT_USERS" | bc)%${NC}"
echo -e "💰 LTV: ${GREEN}\$$LTV${NC}"
echo -e "🎯 CAC: ${YELLOW}\$$CAC${NC}"
echo -e "📊 LTV/CAC Ratio: ${BOLD}$(echo "scale=1; $LTV / $CAC" | bc)x${NC}"
echo

# Development Velocity
echo -e "${BOLD}⚡ Development Velocity${NC}"
echo -e "${BLUE}─────────────────────────────────────${NC}"

# Get issues closed in last 7 days
CLOSED_THIS_WEEK=$(gh issue list --state closed --limit 100 --json closedAt | \
    jq --arg date "$(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -v-7d +%Y-%m-%dT%H:%M:%SZ)" \
    '[.[] | select(.closedAt > $date)] | length')

# Get PRs merged in last 7 days
MERGED_THIS_WEEK=$(gh pr list --state merged --limit 100 --json mergedAt | \
    jq --arg date "$(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -v-7d +%Y-%m-%dT%H:%M:%SZ)" \
    '[.[] | select(.mergedAt > $date)] | length')

# Active development streams
ACTIVE_BRANCHES=$(git branch -r | grep -v HEAD | wc -l)
ACTIVE_WORKTREES=$(git worktree list | wc -l)

echo -e "🚀 Issues Closed (7d): ${GREEN}$CLOSED_THIS_WEEK${NC}"
echo -e "🔀 PRs Merged (7d): ${GREEN}$MERGED_THIS_WEEK${NC}"
echo -e "🌳 Active Worktrees: ${YELLOW}$ACTIVE_WORKTREES${NC}"
echo -e "🌿 Active Branches: ${YELLOW}$ACTIVE_BRANCHES${NC}"

# Calculate velocity score
VELOCITY_SCORE=$(echo "scale=1; ($CLOSED_THIS_WEEK + $MERGED_THIS_WEEK) * 10" | bc)
echo -e "⚡ Velocity Score: ${BOLD}$VELOCITY_SCORE${NC}"
echo

# Agent Performance
echo -e "${BOLD}🤖 Agent Performance${NC}"
echo -e "${BLUE}─────────────────────────────────────${NC}"

# Get agent activity
ORCHESTRATOR_RUNS=$(gh run list --workflow=agent-orchestrator.yml --limit 20 --json conclusion | \
    jq '[.[] | select(.conclusion == "success")] | length')
ORCHESTRATOR_TOTAL=20
SUCCESS_RATE=$(echo "scale=1; $ORCHESTRATOR_RUNS * 100 / $ORCHESTRATOR_TOTAL" | bc)

# Issues by status
AI_READY=$(gh issue list --state open --label "ai:ready" --json number | jq '. | length')
AI_WORKING=$(gh issue list --state open --label "ai:in-progress" --json number | jq '. | length')
AI_COMPLETE=$(gh issue list --state all --label "ai:completed" --json number | jq '. | length')

echo -e "✅ Success Rate: ${GREEN}$SUCCESS_RATE%${NC}"
echo -e "📋 Ready for AI: ${YELLOW}$AI_READY${NC}"
echo -e "🔧 AI Working: ${BLUE}$AI_WORKING${NC}"
echo -e "✨ AI Completed: ${GREEN}$AI_COMPLETE${NC}"
echo -e "🎯 Efficiency: ${BOLD}$(echo "scale=1; $SUCCESS_RATE * 0.87" | bc)%${NC}"
echo

# Path to $10M ARR
echo -e "${BOLD}🚀 Path to \$10M ARR${NC}"
echo -e "${BLUE}─────────────────────────────────────${NC}"

TARGET_ARR=10000000
MONTHS_TO_TARGET=36
REQUIRED_USERS=$(echo "$TARGET_ARR / $PRICE_PER_USER_MONTHLY / 12" | bc)
REQUIRED_GROWTH_RATE=$(echo "scale=1; ($TARGET_ARR / $CURRENT_ARR)^(1/36) * 100 - 100" | bc)

echo -e "🎯 Target ARR: ${BOLD}\$10,000,000${NC}"
echo -e "📅 Timeline: ${YELLOW}36 months${NC}"
echo -e "👥 Users Needed: ${BOLD}$(printf "%'d" $REQUIRED_USERS)${NC}"
echo -e "📈 Required Monthly Growth: ${RED}${REQUIRED_GROWTH_RATE}%${NC}"

# Current trajectory
if [ "$CLOSED_THIS_WEEK" -gt 0 ]; then
    FEATURES_PER_MONTH=$((CLOSED_THIS_WEEK * 4))
    NEW_USERS_PER_FEATURE=50  # Estimate
    PROJECTED_NEW_USERS=$((FEATURES_PER_MONTH * NEW_USERS_PER_FEATURE))
    PROJECTED_MRR=$(echo "($CURRENT_USERS + $PROJECTED_NEW_USERS) * $CONVERSION_RATE * $PRICE_PER_USER_MONTHLY" | bc)
    
    echo -e "\n${YELLOW}📊 Current Trajectory:${NC}"
    echo -e "  Features/Month: $FEATURES_PER_MONTH"
    echo -e "  New Users/Month: $PROJECTED_NEW_USERS"
    echo -e "  Projected MRR: ${GREEN}\$$PROJECTED_MRR${NC}"
fi
echo

# App Portfolio Status
echo -e "${BOLD}📱 App Portfolio${NC}"
echo -e "${BLUE}─────────────────────────────────────${NC}"
echo -e "1️⃣  SuperPassword - ${GREEN}LIVE${NC} - ARR: \$$CURRENT_ARR"
echo -e "2️⃣  SecureNotes - ${YELLOW}PLANNED${NC} - Est. ARR: \$250,000"
echo -e "3️⃣  CryptoVault - ${YELLOW}PLANNED${NC} - Est. ARR: \$180,000"
echo -e "4️⃣  TeamPass - ${YELLOW}PLANNED${NC} - Est. ARR: \$500,000"
echo -e "5️⃣  BioLock - ${YELLOW}PLANNED${NC} - Est. ARR: \$320,000"
echo

# Action Items
echo -e "${BOLD}⚡ Critical Actions${NC}"
echo -e "${BLUE}─────────────────────────────────────${NC}"

if [ "$AI_READY" -gt 0 ]; then
    echo -e "🔴 ${RED}$AI_READY issues ready for AI agents!${NC}"
    echo -e "   Run: gh workflow run agent-orchestrator.yml"
fi

if [ "$ACTIVE_WORKTREES" -lt 5 ]; then
    echo -e "🟡 ${YELLOW}Only $ACTIVE_WORKTREES worktrees active${NC}"
    echo -e "   Need 5+ for parallel development"
fi

if [ "$SUCCESS_RATE" != "100.0" ]; then
    echo -e "🟡 ${YELLOW}Agent success rate below 100%${NC}"
    echo -e "   Debug failed runs"
fi

if [ "$PAYING_USERS" -lt 100 ]; then
    echo -e "🔴 ${RED}Need $(( 100 - PAYING_USERS )) more paying users for \$1K MRR${NC}"
    echo -e "   Launch marketing campaign"
fi

echo

# Competitive Analysis
echo -e "${BOLD}🏆 Market Position${NC}"
echo -e "${BLUE}─────────────────────────────────────${NC}"
echo -e "1Password: \$6.8B valuation - ${RED}2008 start (17 year head start)${NC}"
echo -e "Bitwarden: \$100M ARR - ${YELLOW}2016 start (9 year head start)${NC}"
echo -e "NordPass: \$50M ARR - ${YELLOW}2019 start (6 year head start)${NC}"
echo -e "${BOLD}SuperPassword: <\$1K ARR - ${GREEN}2024 start (AI advantage)${NC}"
echo -e "\n${CYAN}💡 With AI agents, we can achieve in 3 years what took them 10+${NC}"
echo

# Weekly Goal
echo -e "${BOLD}🎯 This Week's Goals${NC}"
echo -e "${BLUE}─────────────────────────────────────${NC}"
echo -e "✅ Close ${GREEN}10 issues${NC} (current: $CLOSED_THIS_WEEK)"
echo -e "✅ Merge ${GREEN}5 PRs${NC} (current: $MERGED_THIS_WEEK)"
echo -e "✅ Get ${GREEN}50 new users${NC}"
echo -e "✅ Convert ${GREEN}2 to paid${NC}"
echo -e "✅ Launch ${GREEN}1 new feature${NC}"
echo

# Motivational quote
QUOTES=(
    "The best time to plant a tree was 20 years ago. The second best time is now."
    "Every expert was once a beginner."
    "Success is not final, failure is not fatal: it is the courage to continue that counts."
    "The only way to do great work is to love what you do."
    "Move fast and break things. Unless you are breaking stuff, you are not moving fast enough."
)
RANDOM_QUOTE=${QUOTES[$RANDOM % ${#QUOTES[@]}]}

echo -e "${MAGENTA}\"$RANDOM_QUOTE\"${NC}"
echo
echo -e "${GREEN}✨ Dashboard generated at $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo -e "${BOLD}${CYAN}Keep shipping! The empire awaits... 🚀${NC}"
