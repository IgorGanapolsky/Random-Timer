#!/bin/bash

# Free Tier Protection Script
# CRITICAL: Prevents expensive CI/CD configurations
# Author: Solo developer with ZERO budget

set -e

echo "🛡️ Free Tier Protection Check"
echo "=============================="

ERRORS=0
WARNINGS=0

# Check for high-frequency schedules (anything more frequent than daily)
echo "Checking for dangerous schedules..."
if grep -r "cron.*\*/[0-9]\+" .github/workflows/*.yml 2>/dev/null; then
  echo "❌ ERROR: High-frequency schedule detected!"
  echo "   Maximum allowed: Once daily (0 6 * * *)"
  ERRORS=$((ERRORS + 1))
fi

# Check for hourly schedules
if grep -r "cron.*0 \* \* \* \*" .github/workflows/*.yml 2>/dev/null; then
  echo "❌ ERROR: Hourly schedule detected! Too expensive!"
  ERRORS=$((ERRORS + 1))
fi

# Check for timeout limits over 10 minutes
echo "Checking workflow timeouts..."
if grep -r "timeout-minutes: [0-9]\{2,\}" .github/workflows/*.yml 2>/dev/null | grep -v "timeout-minutes: 10"; then
  echo "❌ ERROR: Workflow timeout too high (>10 min)!"
  echo "   Maximum allowed: 10 minutes"
  ERRORS=$((ERRORS + 1))
fi

# Check for matrix builds (they multiply costs)
echo "Checking for matrix builds..."
if grep -r "matrix:" .github/workflows/*.yml 2>/dev/null; then
  echo "⚠️ WARNING: Matrix builds detected - these multiply costs!"
  echo "   Consider removing or limiting matrix builds"
  WARNINGS=$((WARNINGS + 1))
fi

# Check for multiple triggers on same workflow
echo "Checking for multiple triggers..."
for file in .github/workflows/*.yml; do
  if [ -f "$file" ]; then
    TRIGGER_COUNT=$(grep -E "^  (push|pull_request|issues|schedule):" "$file" 2>/dev/null | wc -l || echo 0)
    if [ "$TRIGGER_COUNT" -gt 2 ]; then
      echo "⚠️ WARNING: $(basename $file) has $TRIGGER_COUNT triggers!"
      echo "   This can cause exponential run growth"
      WARNINGS=$((WARNINGS + 1))
    fi
  fi
done

# Check for missing concurrency controls
echo "Checking for concurrency controls..."
for file in .github/workflows/*.yml; do
  if [ -f "$file" ]; then
    if ! grep -q "concurrency:" "$file" 2>/dev/null; then
      echo "⚠️ WARNING: $(basename $file) missing concurrency control!"
      echo "   Add: concurrency: { group: \${{ github.workflow }}, cancel-in-progress: true }"
      WARNINGS=$((WARNINGS + 1))
    fi
  fi
done

# Check EAS configuration
if [ -f "eas.json" ]; then
  echo "Checking EAS configuration..."
  
  # Check for auto-submit (expensive)
  if grep -q "autoSubmit.*true" eas.json 2>/dev/null; then
    echo "❌ ERROR: EAS auto-submit is enabled! This costs builds!"
    ERRORS=$((ERRORS + 1))
  fi
  
  # Check for production builds without protection
  if grep -q '"production"' eas.json 2>/dev/null; then
    if ! grep -q "MANUAL_BUILD_ONLY" eas.json 2>/dev/null; then
      echo "⚠️ WARNING: Production builds not protected!"
      echo "   Add env var MANUAL_BUILD_ONLY to prevent accidents"
      WARNINGS=$((WARNINGS + 1))
    fi
  fi
fi

# Count total active workflows
ACTIVE_WORKFLOWS=$(find .github/workflows -name "*.yml" -o -name "*.yaml" 2>/dev/null | wc -l || echo 0)
if [ "$ACTIVE_WORKFLOWS" -gt 5 ]; then
  echo "⚠️ WARNING: Too many workflows ($ACTIVE_WORKFLOWS)!"
  echo "   Recommended: 3 or fewer for solo developers"
  WARNINGS=$((WARNINGS + 1))
fi

# Summary
echo ""
echo "=============================="
echo "📊 Free Tier Check Summary"
echo "=============================="
echo "Errors:   $ERRORS"
echo "Warnings: $WARNINGS"
echo "Workflows: $ACTIVE_WORKFLOWS"

if [ "$ERRORS" -gt 0 ]; then
  echo ""
  echo "❌ FAILED: Fix errors before committing!"
  echo "You cannot afford these expensive configurations!"
  exit 1
elif [ "$WARNINGS" -gt 0 ]; then
  echo ""
  echo "⚠️ PASSED WITH WARNINGS"
  echo "Consider fixing warnings to stay safely in free tier"
  exit 0
else
  echo ""
  echo "✅ PASSED: Configuration is free-tier safe!"
  exit 0
fi
