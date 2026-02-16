#!/usr/bin/env bash
# setup-device.sh — Push PhoneClaw ClawScripts to test device
# Prerequisites: PhoneClaw APK installed, Accessibility service enabled

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

echo -e "${BOLD}══ PhoneClaw Device Setup ══${RESET}"

# Check device connected
DEVICE_COUNT=$(adb devices | grep -c "device$" || true)
if [ "$DEVICE_COUNT" -eq 0 ]; then
  echo -e "${RED}No Android device connected.${RESET}"
  exit 2
fi

# Create target directory on device
adb shell mkdir -p /sdcard/phoneclaw/randomtimer 2>/dev/null || true

# Push ClawScript files
echo -e "${CYAN}Pushing ClawScripts to device...${RESET}"
adb push "$SCRIPT_DIR/visual-alarm-notification.js" /sdcard/phoneclaw/randomtimer/
adb push "$SCRIPT_DIR/visual-lockscreen-alarm.js" /sdcard/phoneclaw/randomtimer/

echo -e "${GREEN}Scripts pushed to /sdcard/phoneclaw/randomtimer/${RESET}"
echo ""
echo -e "${BOLD}To run visual tests:${RESET}"
echo "  1. Open PhoneClaw app on the device"
echo "  2. Load script from /sdcard/phoneclaw/randomtimer/"
echo "  3. Start Random Timer alarm (use: make device-tests-adb to trigger)"
echo "  4. Run the ClawScript while alarm is active"
echo ""
echo -e "${BOLD}Available scripts:${RESET}"
echo "  visual-alarm-notification.js  — Verify alarm notification renders correctly"
echo "  visual-lockscreen-alarm.js    — Verify lock screen alarm display"
