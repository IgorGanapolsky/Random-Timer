#!/usr/bin/env bash
# test-audio.sh — Gap 4: Audio playback verification
# Verifies audio focus and alarm stream during alarm.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"
source "$SCRIPT_DIR/lib/assert.sh"

echo -e "${BOLD}══ Audio Tests ══${RESET}"

# Helper: start timer, wait for alarm
setup_alarm() {
  cleanup
  start_timer_via_ui
  sleep 1
  if ! wait_for_alarm_or_complete; then
    return 1
  fi
  return 0
}

# ── Test 1: Audio focus acquired during alarm ──
begin_test "audio_focus_acquired_during_alarm"
if setup_alarm; then
  AUDIO_DUMP=$(adb shell dumpsys audio 2>/dev/null || true)
  FOCUS_SECTION=$(echo "$AUDIO_DUMP" | grep -B 5 -A 10 -i "focus" | grep -i "alarm\|randomtimer\|USAGE_ALARM\|usage=4" || true)
  assert_not_empty "$FOCUS_SECTION" "Audio focus held with alarm usage during alarm"
else
  assert_eq "alarm_fired" "true" "Alarm fired for audio focus test"
fi
cleanup

# ── Test 2: Audio focus released after stop ──
begin_test "audio_focus_released_after_stop"
if setup_alarm; then
  stop_timer_via_ui
  sleep 2

  AUDIO_DUMP=$(adb shell dumpsys audio 2>/dev/null || true)
  FOCUS_HOLDER=$(echo "$AUDIO_DUMP" | grep -A 5 -i "audio focus" | grep "$PACKAGE" || true)
  assert_eq "$FOCUS_HOLDER" "" "Audio focus released after stop"
else
  assert_eq "alarm_fired" "true" "Alarm fired for audio release test"
fi
cleanup

# ── Test 3: Alarm audio attributes use USAGE_ALARM ──
begin_test "alarm_audio_attributes_correct"
if setup_alarm; then
  AUDIO_DUMP=$(adb shell dumpsys audio 2>/dev/null || true)
  ALARM_USAGE=$(echo "$AUDIO_DUMP" | grep -i "USAGE_ALARM\|usage=ALARM\|usage 4\|usage=4" || true)
  assert_not_empty "$ALARM_USAGE" "Audio uses USAGE_ALARM attributes"
else
  assert_eq "alarm_fired" "true" "Alarm fired for audio attributes test"
fi
cleanup

print_summary
