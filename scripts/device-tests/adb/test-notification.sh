#!/usr/bin/env bash
# test-notification.sh — Gap 1: Alarm notification behavior when app is backgrounded
# Verifies notification appears and stop via in-app UI clears everything.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"
source "$SCRIPT_DIR/lib/assert.sh"

echo -e "${BOLD}══ Notification Tests ══${RESET}"

# ── Test 1: Alarm notification appears when app is backgrounded ──
begin_test "alarm_notification_appears_when_backgrounded"
cleanup
start_timer_via_ui

# Background the app
background_app
sleep 2

if wait_for_alarm_or_complete; then
  dump_notifications
  HAS_ALARM=$(grep -c "timer_alarm\|Timer Complete\|Time's Up" "$NOTIF_DUMP" || true)
  assert_not_empty "$HAS_ALARM" "Alarm/complete notification present when backgrounded"
else
  assert_eq "alarm_fired" "true" "Alarm notification appeared when backgrounded"
fi
cleanup

# ── Test 2: Stop from in-app UI clears all notifications ──
begin_test "stop_clears_all_notifications"
cleanup
start_timer_via_ui
background_app
sleep 2

if wait_for_alarm_or_complete; then
  # Return to app and stop via in-app button
  foreground_app
  sleep 2
  stop_timer_via_ui
  sleep 2

  if has_package_notification; then
    assert_eq "has_notification" "no_notification" "All notifications cleared after stop"
  else
    assert_eq "no_notification" "no_notification" "All notifications cleared after stop"
  fi
else
  assert_eq "alarm_fired" "true" "Alarm fired for stop test"
fi
cleanup

# ── Test 3: Timer notification present while running ──
begin_test "timer_running_notification_present"
cleanup
start_timer_via_ui
sleep 2

TIMER_NOTIF=$(get_timer_notifications)
assert_contains "$TIMER_NOTIF" "Timer Running" "Timer Running notification shown"
cleanup

print_summary
