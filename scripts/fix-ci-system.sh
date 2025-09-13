#!/bin/bash

set -e

echo "🔧 CI System Recovery Script"
echo "============================"
echo ""

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI is not installed. Please install it first."
    echo "   https://cli.github.com/"
    exit 1
fi

# Check if user is authenticated
if ! gh auth status &> /dev/null; then
    echo "❌ You are not authenticated with GitHub CLI."
    echo "   Please run 'gh auth login' first."
    exit 1
fi

echo "Step 1: Re-enabling core workflows"
echo "------------------------------"

# Array of core workflows to enable
CORE_WORKFLOWS=(
    "Security Pipeline"
    "Release Pipeline"
    "Agent Orchestrator"
    "Agent Executor"
)

# Re-enable core workflows
for workflow in "${CORE_WORKFLOWS[@]}"; do
    echo "🔄 Re-enabling $workflow..."
    gh workflow enable "$workflow" || echo "⚠️  Failed to enable $workflow"
    sleep 1
done

echo ""
echo "Step 2: Checking for syntax issues"
echo "------------------------------"

# Check for syntax issues in YAML files
echo "🔍 Checking for syntax issues in workflow files..."
for file in .github/workflows/*.yml; do
    echo "Checking $file..."
    if command -v yamllint &> /dev/null; then
        yamllint -d relaxed "$file" || echo "⚠️  Syntax issues found in $file"
    else
        echo "⚠️  yamllint not installed, skipping syntax check"
        echo "   Install with: brew install yamllint (macOS) or apt install yamllint (Linux)"
        break
    fi
done

echo ""
echo "Step 3: Setting up monitoring"
echo "------------------------------"

# Create monitoring issue
echo "📊 Creating monitoring issue..."
MONITORING_ISSUE=$(gh issue create \
    --title "CI System Monitoring and Recovery" \
    --body "## CI System Monitoring

### Current Status
- Re-enabled core workflows on $(date)
- Implemented safety measures

### Monitoring Checklist
- [ ] Check GitHub Actions usage daily for 1 week
- [ ] Set GitHub spending limit to \$10/month
- [ ] Monitor for unusual workflow patterns
- [ ] Consolidate workflows to minimal set

### Safety Measures
- Concurrency controls added
- Reduced schedule frequencies
- Removed dangerous triggers
- Added rate limiting

### Next Steps
- Complete workflow consolidation
- Document workflow architecture
- Create monitoring dashboard
" \
    --label "ci,monitoring" || echo "0")

if [ "$MONITORING_ISSUE" != "0" ]; then
    echo "✅ Created monitoring issue: $MONITORING_ISSUE"
else
    echo "⚠️  Failed to create monitoring issue"
fi

echo ""
echo "Step 4: Generating report"
echo "------------------------------"

# Get current workflow status
ACTIVE_WORKFLOWS=$(gh workflow list --json name --jq '.[].name' | wc -l | tr -d ' ')
DISABLED_WORKFLOWS=$(gh workflow list --all --json name,state --jq '.[] | select(.state=="disabled_manually") | .name' | wc -l | tr -d ' ')

# Generate report
echo "📊 CI System Recovery Report" | tee ci-recovery-report.txt
echo "===========================" | tee -a ci-recovery-report.txt
echo "" | tee -a ci-recovery-report.txt
echo "Generated: $(date)" | tee -a ci-recovery-report.txt
echo "" | tee -a ci-recovery-report.txt
echo "Current Status:" | tee -a ci-recovery-report.txt
echo "- Active Workflows: $ACTIVE_WORKFLOWS" | tee -a ci-recovery-report.txt
echo "- Disabled Workflows: $DISABLED_WORKFLOWS" | tee -a ci-recovery-report.txt
echo "- Core Workflows Re-enabled: ${#CORE_WORKFLOWS[@]}" | tee -a ci-recovery-report.txt
echo "" | tee -a ci-recovery-report.txt
echo "Next Steps:" | tee -a ci-recovery-report.txt
echo "1. Set GitHub spending limit to \$10/month" | tee -a ci-recovery-report.txt
echo "2. Monitor workflow runs for 1 week" | tee -a ci-recovery-report.txt
echo "3. Consolidate workflows to minimal set" | tee -a ci-recovery-report.txt
echo "" | tee -a ci-recovery-report.txt
echo "For detailed recovery plan, see CI_SYSTEM_RECOVERY_PLAN.md" | tee -a ci-recovery-report.txt

echo ""
echo "✅ CI System Recovery Script completed"
echo "Check ci-recovery-report.txt for details"

if [ "$MONITORING_ISSUE" != "0" ]; then
    echo "📊 Monitor progress at: $MONITORING_ISSUE"
fi