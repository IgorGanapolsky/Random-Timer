#!/usr/bin/env bash
# common.sh — Shared ADB helpers for device tests
# Source this file: source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
#
# On Android 12+ (API 31+), non-exported services cannot be started from shell UID.
# All timer control uses UI automation (uiautomator + input tap) instead of direct intents.

set -euo pipefail

PACKAGE="com.iganapolsky.randomtimer"
SERVICE="$PACKAGE/com.iganapolsky.randomtimer.service.TimerForegroundService"
ACTIVITY="$PACKAGE/.MainActivity"
UI_DUMP="/sdcard/device_test_dump.xml"

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

wait_for_device() {
  echo -e "${CYAN}Waiting for device...${RESET}"
  adb wait-for-device
  local timeout=30
  while [ "$timeout" -gt 0 ]; do
    if adb shell getprop sys.boot_completed 2>/dev/null | grep -q "1"; then
      return 0
    fi
    sleep 1
    timeout=$((timeout - 1))
  done
  echo -e "${RED}Device boot timeout${RESET}"
  return 1
}

grant_permissions() {
  adb shell pm grant "$PACKAGE" android.permission.POST_NOTIFICATIONS 2>/dev/null || true
}

# Tap a UI element by its text content using uiautomator.
# Usage: tap_text "Start Timer"
tap_text() {
  local text="$1"
  adb shell uiautomator dump "$UI_DUMP" >/dev/null 2>&1
  local dump
  dump=$(adb shell cat "$UI_DUMP" 2>/dev/null || true)

  # Extract bounds for the element with matching text
  local bounds
  bounds=$(echo "$dump" | tr '>' '\n' | grep "text=\"$text\"" | head -1 | \
    grep -o 'bounds="\[[0-9]*,[0-9]*\]\[[0-9]*,[0-9]*\]"' | head -1 || true)

  if [ -z "$bounds" ]; then
    echo -e "  ${RED}tap_text: '$text' not found in UI${RESET}" >&2
    return 1
  fi

  # Parse bounds "[x1,y1][x2,y2]" to get center coordinates
  local coords
  coords=$(echo "$bounds" | grep -o '[0-9]*' | head -4)
  local x1 y1 x2 y2
  x1=$(echo "$coords" | sed -n '1p')
  y1=$(echo "$coords" | sed -n '2p')
  x2=$(echo "$coords" | sed -n '3p')
  y2=$(echo "$coords" | sed -n '4p')
  local cx=$(( (x1 + x2) / 2 ))
  local cy=$(( (y1 + y2) / 2 ))

  adb shell input tap "$cx" "$cy"
}

# Wait for a text element to appear in the UI, polling every second.
# Usage: wait_for_text "Stop" 30
wait_for_text() {
  local text="$1"
  local timeout=${2:-30}
  while [ "$timeout" -gt 0 ]; do
    adb shell uiautomator dump "$UI_DUMP" >/dev/null 2>&1
    local dump
    dump=$(adb shell cat "$UI_DUMP" 2>/dev/null || true)
    if echo "$dump" | grep -q "text=\"$text\""; then
      return 0
    fi
    sleep 1
    timeout=$((timeout - 1))
  done
  return 1
}

# Configure timer for fast test execution:
# - Range sliders to minimum (0s-30s)
# - Alarm duration to 60s (longest, gives time for interaction tests)
set_test_timer_config() {
  # Slider bounds from uiautomator: x=[54..1026]
  # Min slider center y ≈ 549, Max slider center y ≈ 732
  adb shell input swipe 540 549 54 549 300   # drag min slider left
  sleep 0.3
  adb shell input swipe 540 732 54 732 300   # drag max slider left
  sleep 0.3
  # Tap "60s" alarm duration button (bounds [789,1057][848,1096])
  adb shell input tap 818 1076
  sleep 0.3
}

# Tap primary start CTA (first-run vs returning user).
tap_start_timer_button() {
  if wait_for_text "Start First Drill" 3; then
    tap_text "Start First Drill"
    return 0
  fi
  if wait_for_text "Start Timer" 3; then
    tap_text "Start Timer"
    return 0
  fi
  # Compose testTag exposed as view id on debug builds
  if adb shell uiautomator dump /sdcard/window_dump.xml >/dev/null 2>&1 \
    && adb shell cat /sdcard/window_dump.xml 2>/dev/null | grep -q 'resource-id="start_timer"'; then
    adb shell input tap 540 2200
    return 0
  fi
  echo "Start button not found (Start First Drill / Start Timer / start_timer)" >&2
  return 1
}

# Start timer via UI: launch app, set short range, and tap start.
start_timer_via_ui() {
  foreground_app
  sleep 2
  set_test_timer_config
  sleep 1
  tap_start_timer_button || return 1
  sleep 1
}

# Stop timer via UI: tap the "Stop" button on the timer screen.
stop_timer_via_ui() {
  foreground_app
  sleep 1
  if wait_for_text "Stop" 5; then
    tap_text "Stop"
    sleep 1
  fi
}

# Silence alarm via notification: expand shade and tap "Silence" action.
silence_alarm_via_notification() {
  adb shell cmd statusbar expand-notifications
  sleep 1
  tap_text "Silence" || true
  sleep 1
  adb shell cmd statusbar collapse
}

# Stop alarm via notification: expand shade and tap "Stop" action.
stop_timer_via_notification() {
  adb shell cmd statusbar expand-notifications
  sleep 1
  tap_text "Stop" || true
  sleep 1
  adb shell cmd statusbar collapse
}

# Force-stop the app entirely (clears all services and state).
force_stop_app() {
  adb shell am force-stop "$PACKAGE"
}

background_app() {
  adb shell input keyevent KEYCODE_HOME
}

foreground_app() {
  adb shell am start -n "$ACTIVITY" --activity-single-top >/dev/null 2>&1
}

NOTIF_DUMP="${TMPDIR:-/tmp}/device_test_notif_dump.txt"

# Dump notifications to a temp file (avoids shell variable truncation on large dumps).
dump_notifications() {
  adb shell dumpsys notification --noredact 2>/dev/null > "$NOTIF_DUMP"
}

get_alarm_notifications() {
  dump_notifications
  grep -A 80 "timer_alarm" "$NOTIF_DUMP" || true
}

get_timer_notifications() {
  dump_notifications
  grep -A 80 "timer_progress" "$NOTIF_DUMP" || true
}

has_package_notification() {
  dump_notifications
  grep -q "$PACKAGE" "$NOTIF_DUMP"
}

# Wait for alarm to fire. Checks for both alarm notification (brief) and
# complete notification (persists after alarm duration expires).
# Usage: wait_for_alarm_or_complete [timeout_seconds]
wait_for_alarm_or_complete() {
  local timeout=${1:-120}
  echo -e "  ${CYAN}Waiting for alarm (up to ${timeout}s)...${RESET}"
  for i in $(seq 1 "$timeout"); do
    dump_notifications
    if grep -q "Time's Up" "$NOTIF_DUMP"; then
      echo -e "  ${GREEN}Alarm notification detected${RESET}"
      return 0
    fi
    if grep -A 80 "timer_progress" "$NOTIF_DUMP" | grep -q "Timer Complete"; then
      echo -e "  ${GREEN}Timer complete notification detected${RESET}"
      return 0
    fi
    sleep 1
  done
  echo -e "  ${RED}Alarm did not fire within ${timeout}s${RESET}"
  return 1
}

cleanup() {
  force_stop_app 2>/dev/null || true
  sleep 1
}
