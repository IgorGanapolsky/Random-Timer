#!/usr/bin/env bash
# verify-billing-catalog.sh — Retail-device billing catalog smoke via adb + PostHog correlation hints.
# Opens paywall path, captures logcat billing lines, prints device/package version for evidence.
# Requires PLAY_BILLING_TEST_MODE=1 or a license-tester device account (see lib/billing-guard.sh).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"
# shellcheck source=lib/billing-guard.sh
source "$SCRIPT_DIR/lib/billing-guard.sh"

DEVICE_COUNT=$(adb devices | grep -c "device$" || true)
if [ "$DEVICE_COUNT" -eq 0 ]; then
  echo "No Android device connected." >&2
  exit 2
fi

assert_play_billing_test_safe

MODEL=$(adb shell getprop ro.product.model 2>/dev/null | tr -d '\r')
SERIAL=$(adb devices -l | awk '/device usb/ {print $1; exit}')

echo "== Device =="
echo "serial=$SERIAL model=$MODEL"

VERSION_LINE=$(adb shell dumpsys package "$PACKAGE" 2>/dev/null | tr -d '\r' | grep -E "versionName=|versionCode=" | head -2 || true)
echo "package=$PACKAGE"
echo "$VERSION_LINE"

echo "== Launch + paywall affordance tap =="
adb logcat -c
adb shell am force-stop "$PACKAGE" 2>/dev/null || true
sleep 1
adb shell am start -n "$ACTIVITY"
sleep 8

if wait_for_text "PRO: 1H" 15; then
  tap_text "PRO: 1H" || true
  sleep 5
elif wait_for_text "Start First Drill" 10; then
  tap_text "Start First Drill" || true
  sleep 2
  wait_for_text "PRO: 1H" 15 && tap_text "PRO: 1H" || true
  sleep 5
else
  echo "WARN: paywall affordance not found; continuing with launch-only catalog probe"
fi

echo "== Logcat billing signals (last 80) =="
adb logcat -d 2>/dev/null | grep -iE "billing|catalog|elite_tactical|ProManager|posthog" | tail -80 || true

echo "== PostHog correlation =="
echo "Filter: event=billing_product_catalog_status AND properties.\$device_model=$MODEL (last 1h)"
echo "Expect status=ok with available_product_ids including elite_tactical_monthly after fix ships via Play."
