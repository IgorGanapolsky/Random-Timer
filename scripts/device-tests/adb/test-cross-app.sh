#!/usr/bin/env bash
# test-cross-app.sh — Gap 5: Timer survives app switches
# Verifies timer continues running when user navigates away and returns.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"
source "$SCRIPT_DIR/lib/assert.sh"

echo -e "${BOLD}══ Cross-App Tests ══${RESET}"

# ── Test 1: Timer notification persists after pressing HOME ──
begin_test "timer_continues_after_home"
cleanup
start_timer_via_ui

sleep 2
TIMER_NOTIF=$(get_timer_notifications)
assert_contains "$TIMER_NOTIF" "Timer Running" "Timer running before HOME press"

background_app
sleep 3

TIMER_NOTIF=$(get_timer_notifications)
assert_contains "$TIMER_NOTIF" "Timer Running" "Timer still running after HOME press"

foreground_app
sleep 2

TIMER_NOTIF=$(get_timer_notifications)
assert_contains "$TIMER_NOTIF" "Timer Running" "Timer still running after return"
cleanup

# ── Test 2: Timer continues after switching to another app ──
begin_test "timer_continues_after_app_switch"
cleanup
start_timer_via_ui
sleep 2

adb shell am start -a android.settings.SETTINGS >/dev/null 2>&1
sleep 3

TIMER_NOTIF=$(get_timer_notifications)
assert_contains "$TIMER_NOTIF" "Timer Running" "Timer survives app switch to Settings"

foreground_app
sleep 2
TIMER_NOTIF=$(get_timer_notifications)
assert_contains "$TIMER_NOTIF" "Timer Running" "Timer intact after return from Settings"
cleanup

# ── Test 3: Alarm fires while in another app ──
begin_test "alarm_fires_while_in_other_app"
cleanup
start_timer_via_ui
sleep 1

adb shell am start -a android.settings.SETTINGS >/dev/null 2>&1
sleep 2

if wait_for_alarm_or_complete; then
  assert_eq "true" "true" "Alarm fires while in another app"
else
  assert_eq "alarm_fired" "true" "Alarm fires while in another app"
fi
cleanup

print_summary
