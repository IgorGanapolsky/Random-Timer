#!/bin/bash
# Complete all Google Play Console App Content declarations
# Opens all required pages in Chrome tabs with answers displayed in terminal

set -e

PACKAGE="com.iganapolsky.randomtimer"
BASE_URL="https://play.google.com/console/developers/$PACKAGE/app-content"

# Check AAB exists
AAB_PATH="app/build/outputs/bundle/release/app-release.aab"
if [ ! -f "$AAB_PATH" ]; then
    echo "❌ AAB not found: $AAB_PATH"
    echo "Build it first: ./gradlew bundleRelease"
    exit 1
fi

echo "============================================================"
echo "Google Play Console - App Content Declarations"
echo "============================================================"
echo ""
echo "Package: $PACKAGE"
echo "AAB Ready: $(ls -lh $AAB_PATH | awk '{print $5}')"
echo ""
echo "This script will open all required pages in Chrome."
echo "Use the answers below to complete each form."
echo ""
echo "============================================================"
echo "📋 DECLARATION ANSWERS (Copy-paste ready)"
echo "============================================================"
echo ""
echo "1️⃣  DATA SAFETY"
echo "   URL: $BASE_URL/data-safety"
echo "   ❌ No - app does NOT collect or share any user data"
echo "   ❌ No encryption needed"
echo ""
echo "2️⃣  ADVERTISING ID"
echo "   URL: $BASE_URL/advertising-id"
echo "   ❌ No - app does NOT use advertising ID"
echo ""
echo "3️⃣  GOVERNMENT APPS"
echo "   URL: $BASE_URL/government-apps"
echo "   ❌ No"
echo ""
echo "4️⃣  FINANCIAL FEATURES"
echo "   URL: $BASE_URL/financial-features"
echo "   ❌ No to all"
echo ""
echo "5️⃣  HEALTH APPS"
echo "   URL: $BASE_URL/health"
echo "   ❌ No"
echo ""
echo "6️⃣  FOREGROUND SERVICE (FGS) PERMISSIONS ⚠️  IMPORTANT"
echo "   URL: $BASE_URL/foreground-service"
echo "   ✅ YES - app uses foreground service"
echo "   Type: Timer / Stopwatch"
echo "   Justification (copy-paste):"
echo "   ---"
echo "   App runs a countdown timer that must continue when the app is in the background to notify the user when time expires."
echo "   ---"
echo ""
echo "7️⃣  EXACT ALARM PERMISSION ⚠️  IMPORTANT"
echo "   URL: $BASE_URL/exact-alarm"
echo "   ✅ YES - app uses USE_EXACT_ALARM"
echo "   Use case: Timer / Alarm"
echo "   Justification (copy-paste):"
echo "   ---"
echo "   App schedules exact alarms to notify the user precisely when their random timer completes."
echo "   ---"
echo ""
echo "============================================================"
echo ""
echo "Opening pages in 3 seconds..."
echo "(Keep this terminal open for reference)"
echo ""
sleep 3

# Open all pages in Chrome tabs
open -a "Google Chrome" "$BASE_URL"
sleep 1
open -a "Google Chrome" "$BASE_URL/data-safety"
sleep 0.5
open -a "Google Chrome" "$BASE_URL/advertising-id"
sleep 0.5
open -a "Google Chrome" "$BASE_URL/government-apps"
sleep 0.5
open -a "Google Chrome" "$BASE_URL/financial-features"
sleep 0.5
open -a "Google Chrome" "$BASE_URL/health"
sleep 0.5
open -a "Google Chrome" "$BASE_URL/foreground-service"
sleep 0.5
open -a "Google Chrome" "$BASE_URL/exact-alarm"

echo "✅ Opened 7 tabs in Chrome"
echo ""
echo "📋 Complete each tab using the answers above"
echo ""
echo "After completing all App Content declarations:"
echo ""
echo "8️⃣  STORE LISTING - Verify & Re-save"
echo "   Go to: Store listing (left sidebar)"
echo "   - Verify app name and description"
echo "   - Verify screenshots and graphics are showing"
echo "   - Click 'Save' at bottom if needed"
echo ""
echo "9️⃣  CLOSED TESTING - REQUIRED for 2026 ⚠️"
echo "   Go to: Testing → Closed testing"
echo "   - Create closed testing track"
echo "   - Upload AAB: $AAB_PATH"
echo "   - Add 20+ testers (family, friends, community)"
echo "   - Run for 14+ days before production access"
echo ""
echo "🔗 Direct link to closed testing:"
echo "   https://play.google.com/console/developers/$PACKAGE/testing/closed"
echo ""
echo "============================================================"
echo "Keep this terminal open for reference!"
echo "============================================================"
