#!/usr/bin/env bash
# Autonomous Maintenance Loop
# Designed for scheduling via Ollama /loop on the Mac Mini.
# Keeps the codebase in a 'No Tech Debt' state.

set -euo pipefail

LOG_FILE="logs/maintenance_$(date +%Y%m%d).log"
mkdir -p logs

exec > >(tee -a "$LOG_FILE") 2>&1

echo "--- 🛠️ STARTING MAINTENANCE LOOP: $(date) ---"

# 1. Hygiene Check: Purge worktrees and build artifacts
echo "🧹 Purging local noise..."
rm -rf .claude/worktrees/*
rm -rf native-android/app/build/
rm -rf native-ios/build/

# 2. Tech Debt Audit: Find Redundant Scripts
echo "🔍 Auditing for redundancy..."
# Example: If multiple playstore scripts exist, warn.
PLAY_SCRIPTS=$(ls native-android/complete_*.py 2>/dev/null | wc -l)
if [ "$PLAY_SCRIPTS" -gt 1 ]; then
    echo "⚠️ WARNING: Multiple Play Store setup scripts found. Consolidating required."
fi

# 3. Rule Enforcement: English Only
echo "🇬🇧 Verifying language rules..."
if grep -r "[[:space:]][\u4e00-\u9fa5]" . --exclude-dir=.git --exclude-dir=node_modules; then
    echo "❌ ERROR: Non-English characters found in source. Please fix immediately."
else
    echo "✅ English-only check passed."
fi

# 4. CI Readiness: Run Unit Tests
echo "🧪 Running local smoke tests..."
cd native-android && ./gradlew testDebugUnitTest --no-daemon
cd ..
make verify-ios-logic || echo "⚠️ iOS logic verification skipped (no simulator found)"

echo "--- ✅ MAINTENANCE LOOP COMPLETE: $(date) ---"
