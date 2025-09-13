#!/bin/bash

# Workflow Health Monitoring Dashboard
# Provides real-time status of all GitHub Actions workflows

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

clear

echo -e "${MAGENTA}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${MAGENTA}║       📊 GitHub Actions Monitoring Dashboard 📊          ║${NC}"
echo -e "${MAGENTA}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to get status icon
get_status_icon() {
    case $1 in
        "completed") echo "✅" ;;
        "in_progress") echo "🔄" ;;
        "queued") echo "⏳" ;;
        "failure") echo "❌" ;;
        "cancelled") echo "⚠️" ;;
        "skipped") echo "⏭️" ;;
        *) echo "❓" ;;
    esac
}

# 1. Workflow Activity Summary
echo -e "${BLUE}📈 Workflow Activity (Last 24 Hours)${NC}"
echo "────────────────────────────────────"

RUNS_24H=$(gh api "/repos/$(gh repo view --json nameWithOwner -q .nameWithOwner)/actions/runs?created=>$(date -u -v-1d +%Y-%m-%d 2>/dev/null || date -u -d '1 day ago' +%Y-%m-%d)" --jq '.total_count' 2>/dev/null || echo "0")
RUNS_SUCCESS=$(gh run list --limit 50 --json conclusion | jq '[.[] | select(.conclusion=="success")] | length' 2>/dev/null || echo "0")
RUNS_FAILED=$(gh run list --limit 50 --json conclusion | jq '[.[] | select(.conclusion=="failure")] | length' 2>/dev/null || echo "0")

echo -e "Total Runs: ${CYAN}$RUNS_24H${NC}"
echo -e "Successful: ${GREEN}$RUNS_SUCCESS${NC}"
echo -e "Failed: ${RED}$RUNS_FAILED${NC}"

if [ "$RUNS_24H" -gt 0 ]; then
    SUCCESS_RATE=$((RUNS_SUCCESS * 100 / RUNS_24H))
    if [ "$SUCCESS_RATE" -gt 80 ]; then
        echo -e "Success Rate: ${GREEN}${SUCCESS_RATE}%${NC} ✨"
    elif [ "$SUCCESS_RATE" -gt 50 ]; then
        echo -e "Success Rate: ${YELLOW}${SUCCESS_RATE}%${NC} ⚠️"
    else
        echo -e "Success Rate: ${RED}${SUCCESS_RATE}%${NC} 🚨"
    fi
fi

echo ""

# 2. Active Workflows Status
echo -e "${BLUE}🔧 Active Workflows${NC}"
echo "──────────────────"

gh workflow list --all | grep "active" | while read -r line; do
    name=$(echo "$line" | awk '{print $1}')
    state=$(echo "$line" | awk '{print $2}')
    id=$(echo "$line" | awk '{print $3}')
    
    # Get last run status
    last_run=$(gh run list --workflow "$id" --limit 1 --json status,conclusion,createdAt 2>/dev/null | jq -r '.[0] | "\(.status)|\(.conclusion)|\(.createdAt)"' 2>/dev/null || echo "unknown|unknown|unknown")
    
    if [ "$last_run" != "unknown|unknown|unknown" ]; then
        status=$(echo "$last_run" | cut -d'|' -f1)
        conclusion=$(echo "$last_run" | cut -d'|' -f2)
        created=$(echo "$last_run" | cut -d'|' -f3 | cut -dT -f1)
        
        icon=$(get_status_icon "$conclusion")
        echo -e "$icon $name (last: $created)"
    else
        echo -e "❓ $name (no runs)"
    fi
done

echo ""

# 3. Recent Runs
echo -e "${BLUE}🏃 Recent Workflow Runs${NC}"
echo "─────────────────────"

gh run list --limit 10 --json name,status,conclusion,createdAt,event | \
    jq -r '.[] | "\(.conclusion // .status)|\(.name)|\(.event)|\(.createdAt)"' | \
    while IFS='|' read -r status name event created; do
        icon=$(get_status_icon "$status")
        created_date=$(echo "$created" | cut -dT -f1)
        created_time=$(echo "$created" | cut -dT -f2 | cut -d. -f1)
        
        # Truncate long names
        if [ ${#name} -gt 30 ]; then
            name="${name:0:27}..."
        fi
        
        printf "%s %-30s %s %s\n" "$icon" "$name" "$event" "$created_time"
    done

echo ""

# 4. Cost Analysis
echo -e "${BLUE}💰 Cost Analysis (Free Tier: 2000 min/month)${NC}"
echo "──────────────────────────────────────────"

# Estimate minutes used (rough calculation)
ESTIMATED_MINUTES=$((RUNS_24H * 3))  # Assume 3 min average
MONTHLY_PROJECTION=$((ESTIMATED_MINUTES * 30))

if [ "$MONTHLY_PROJECTION" -lt 1000 ]; then
    echo -e "Daily Usage: ${GREEN}~${ESTIMATED_MINUTES} minutes${NC}"
    echo -e "Monthly Projection: ${GREEN}~${MONTHLY_PROJECTION} minutes${NC} (Well under limit)"
elif [ "$MONTHLY_PROJECTION" -lt 1800 ]; then
    echo -e "Daily Usage: ${YELLOW}~${ESTIMATED_MINUTES} minutes${NC}"
    echo -e "Monthly Projection: ${YELLOW}~${MONTHLY_PROJECTION} minutes${NC} (Approaching limit)"
else
    echo -e "Daily Usage: ${RED}~${ESTIMATED_MINUTES} minutes${NC}"
    echo -e "Monthly Projection: ${RED}~${MONTHLY_PROJECTION} minutes${NC} (OVER LIMIT! 🚨)"
fi

echo ""

# 5. Alerts & Warnings
echo -e "${BLUE}⚠️ Alerts & Warnings${NC}"
echo "──────────────────"

# Check for high-frequency workflows
HIGH_FREQ=$(grep -r "cron.*\*/[0-9]" .github/workflows/*.yml 2>/dev/null | wc -l || echo 0)
if [ "$HIGH_FREQ" -gt 0 ]; then
    echo -e "${RED}🚨 Found $HIGH_FREQ high-frequency scheduled workflows!${NC}"
fi

# Check for workflows without concurrency
NO_CONCURRENCY=$(for f in .github/workflows/*.yml; do grep -L "concurrency:" "$f" 2>/dev/null; done | wc -l || echo 0)
if [ "$NO_CONCURRENCY" -gt 0 ]; then
    echo -e "${YELLOW}⚠️ $NO_CONCURRENCY workflows missing concurrency controls${NC}"
fi

# Check for stuck workflows
STUCK=$(gh run list --status in_progress --json createdAt | jq --arg date "$(date -u -v-1H +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ)" '[.[] | select(.createdAt < $date)] | length' 2>/dev/null || echo 0)
if [ "$STUCK" -gt 0 ]; then
    echo -e "${RED}🚨 $STUCK workflows stuck (running >1 hour)${NC}"
fi

if [ "$HIGH_FREQ" -eq 0 ] && [ "$NO_CONCURRENCY" -eq 0 ] && [ "$STUCK" -eq 0 ]; then
    echo -e "${GREEN}✅ All systems healthy${NC}"
fi

echo ""

# 6. Recommendations
echo -e "${BLUE}💡 Recommendations${NC}"
echo "─────────────────"

if [ "$RUNS_24H" -gt 50 ]; then
    echo "• Consider reducing workflow frequency"
fi

if [ "$RUNS_FAILED" -gt 5 ]; then
    echo "• Investigate failing workflows"
fi

if [ "$MONTHLY_PROJECTION" -gt 1500 ]; then
    echo "• Optimize workflow runtime to stay in free tier"
fi

echo "• Review: gh run list --limit 20"
echo "• Cancel stuck: gh run list --status in_progress --json databaseId -q '.[].databaseId' | xargs -I {} gh run cancel {}"

echo ""
echo -e "${CYAN}Last updated: $(date)${NC}"
echo -e "${CYAN}Auto-refresh: watch -n 60 $0${NC}"
