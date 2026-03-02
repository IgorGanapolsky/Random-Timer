#!/usr/bin/env sh
# ci-maestro.sh — Run all Android Maestro tests on an emulator in CI.
# Called by .github/workflows/device-tests.yml
set -eu

adb install -r native-android/app/build/outputs/apk/debug/app-debug.apk
adb shell pm grant com.iganapolsky.randomtimer android.permission.POST_NOTIFICATIONS 2>/dev/null || true

# Re-enable animator duration for Compose rendering (Maestro needs it)
adb shell settings put global animator_duration_scale 1.0

# Warm-start: launch app, wait for Compose to fully render, then kill.
# CI emulators are slow — Compose UI needs extra time on first launch.
adb shell am start -n com.iganapolsky.randomtimer/.MainActivity
sleep 15
adb shell am force-stop com.iganapolsky.randomtimer
sleep 3

export PATH="$HOME/.maestro/bin:$PATH"
PASS=0
FAIL=0

# CI-safe subset: exclude tests with runScript (sh-incompatible) and
# long timeouts (alarm-circle-tap waits 330s for alarm on slow emulator).
for flow in \
  .maestro/smoke-test.yaml \
  .maestro/persistence-test.yaml \
  .maestro/paused-timer-cannot-show-setup.yaml
do
  echo "== Running: $flow =="
  adb shell am force-stop com.iganapolsky.randomtimer 2>/dev/null || true
  sleep 2
  if maestro test "$flow"; then
    echo "PASSED: $flow"
    PASS=$((PASS + 1))
  else
    echo "FAILED: $flow"
    FAIL=$((FAIL + 1))
  fi
done

echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
