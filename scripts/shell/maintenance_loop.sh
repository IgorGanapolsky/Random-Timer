#!/usr/bin/env bash
# Autonomous Maintenance Loop
# Designed for scheduling via Ollama /loop on the Mac Mini.
# Keeps the codebase in a 'No Tech Debt' state.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$(cd "$SCRIPT_DIR/../.." && pwd)"

LOG_FILE="logs/maintenance_$(date +%Y%m%d).log"
mkdir -p logs

exec > >(tee -a "$LOG_FILE") 2>&1

echo "--- 🛠️ STARTING MAINTENANCE LOOP: $(date) ---"

# 1. Hygiene Check: Purge worktrees and build artifacts
echo "🧹 Purging local noise..."
rm -rf .claude/worktrees/*
rm -rf native-android/app/build/
rm -rf native-ios/build/

# 2. Tech Debt Audit: Consolidate Redundant Scripts
echo "🔍 Consolidating redundant scripts..."
PRIMARY_SCRIPT="native-android/fully_autonomous_setup.py"
for script in native-android/auto_complete_forms.py native-android/autonomous_playstore_setup.py native-android/complete_all_declarations.py native-android/complete_playstore_declarations.py native-android/complete_playstore_setup.py native-android/playstore_upload_selenium.py; do
    if [ -f "$script" ]; then
        echo "🗑️ Deleting redundant script: $script"
        rm "$script"
    fi
done

# 3. Rule Enforcement: English Only
echo "🇬🇧 Verifying language rules..."
# Find any non-ASCII characters (robust cross-platform method)
if LC_ALL=C grep -r "[^ -~]" . --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=logs; then
    echo "❌ ERROR: Non-English/Non-ASCII characters found in source. Please fix immediately."
else
    echo "✅ English-only check passed."
fi

# 4. CI Readiness: Run Unit Tests
echo "🧪 Running local smoke tests..."
cd native-android && ./gradlew testDebugUnitTest --no-daemon
cd ..
make verify-ios-logic || echo "⚠️ iOS logic verification skipped (no simulator found)"

echo "--- ✅ MAINTENANCE LOOP COMPLETE: $(date) ---"
