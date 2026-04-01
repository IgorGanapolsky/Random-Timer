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
# Wait for activity to be fully drawn
for i in $(seq 1 30); do
  if adb shell dumpsys activity activities 2>/dev/null | grep -q 'mResumed=true.*randomtimer'; then
    echo "App activity resumed after ${i}s"
    break
  fi
  sleep 1
done
sleep 3
adb shell am force-stop com.iganapolsky.randomtimer
sleep 3

export PATH="$HOME/.maestro/bin:$PATH"
export MAESTRO_DRIVER_STARTUP_TIMEOUT=60000
PASS=0
FAIL=0

# CI-safe subset: uses ci-smoke-test (no compact-mode dependency),
# excludes runScript tests and long-timeout alarm tests.
for flow in \
  .maestro/ci-smoke-test.yaml
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
