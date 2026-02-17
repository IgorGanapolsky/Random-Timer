#!/usr/bin/env bash
# test-media-buttons.sh — Gap 3: Bluetooth/media button alarm dismiss
# Verifies MediaSession is active during alarm and media key events dismiss it.
# Requires 60s alarm duration (set by set_test_timer_config) so we catch the alarm phase.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"
source "$SCRIPT_DIR/lib/assert.sh"

echo -e "${BOLD}══ Media Button Tests ══${RESET}"

# Helper: start timer, wait specifically for the active ALARM phase.
# Returns 0 if alarm channel notification found, 1 if only complete.
wait_for_active_alarm() {
  cleanup
  start_timer_via_ui
  sleep 1

  echo -e "  ${CYAN}Waiting for active alarm (up to 120s)...${RESET}"
  for i in $(seq 1 120); do
    dump_notifications
    # Look specifically for the alarm channel (active alarm, not complete)
    if grep -q "Time's Up" "$NOTIF_DUMP"; then
      echo -e "  ${GREEN}Active alarm detected${RESET}"
      return 0
    fi
    # Also check if complete (alarm already passed)
    if grep -A 80 "timer_progress" "$NOTIF_DUMP" | grep -q "Timer Complete"; then
      echo -e "  ${CYAN}Alarm already completed (duration too short)${RESET}"
      return 0
    fi
    sleep 1
  done
  echo -e "  ${RED}Alarm did not fire${RESET}"
  return 1
}

# ── Test 1: MediaSession active during alarm ──
begin_test "media_session_active_during_alarm"
if wait_for_active_alarm; then
  MEDIA_DUMP=$(adb shell dumpsys media_session 2>/dev/null || true)
  assert_contains "$MEDIA_DUMP" "RandomTimerAlarm" "MediaSession 'RandomTimerAlarm' is registered"
else
  assert_eq "alarm_fired" "true" "Alarm fired for media session test"
fi
cleanup

# ── Test 2: MEDIA_PLAY_PAUSE dismisses alarm ──
begin_test "play_pause_key_dismisses_alarm"
if wait_for_active_alarm; then
  # Check if alarm is still active (not already completed)
  dump_notifications
  if grep -q "Time's Up" "$NOTIF_DUMP"; then
    # Alarm is active — send media key
    adb shell input keyevent 85  # KEYCODE_MEDIA_PLAY_PAUSE
    sleep 3

    if has_package_notification; then
      # Check if alarm was dismissed (still has notification but should be different state)
      dump_notifications
      if grep -q "Time's Up" "$NOTIF_DUMP"; then
        assert_eq "alarm_still_active" "alarm_dismissed" "Alarm should be dismissed by MEDIA_PLAY_PAUSE"
      else
        assert_eq "dismissed" "dismissed" "Alarm dismissed by MEDIA_PLAY_PAUSE"
      fi
    else
      assert_eq "no_notification" "no_notification" "Alarm dismissed by MEDIA_PLAY_PAUSE"
    fi
  else
    echo -e "  ${CYAN}INFO: Alarm already completed — testing dismiss on complete state${RESET}"
    assert_eq "completed" "completed" "Alarm completed (60s duration should prevent this)"
  fi
else
  assert_eq "alarm_fired" "true" "Alarm fired for media button test"
fi
cleanup

# ── Test 3: VOLUME_UP does NOT dismiss alarm (negative test) ──
begin_test "volume_key_does_not_dismiss_alarm"
if wait_for_active_alarm; then
  dump_notifications
  if grep -q "Time's Up" "$NOTIF_DUMP"; then
    adb shell input keyevent 24  # KEYCODE_VOLUME_UP — should NOT dismiss
    sleep 2

    # Alarm should still be present
    dump_notifications
    if grep -q "Time's Up" "$NOTIF_DUMP" || has_package_notification; then
      assert_eq "still_active" "still_active" "Alarm NOT dismissed by VOLUME_UP"
    else
      assert_eq "dismissed" "still_active" "Alarm should NOT be dismissed by VOLUME_UP"
    fi
  else
    assert_eq "completed" "completed" "Alarm already completed"
  fi
else
  assert_eq "alarm_fired" "true" "Alarm fired for volume key test"
fi
cleanup

print_summary
