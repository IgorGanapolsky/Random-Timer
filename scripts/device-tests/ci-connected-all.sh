#!/usr/bin/env sh
# ci-connected-all.sh — Run every connectedDebugAndroidTest class on CI emulator.
# device-tests.yml runs only TimerSetupSmokeTest; native-release must gate on the full suite.
# One Gradle invocation per class + force-stop between classes avoids cross-class crashes on API 30.
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
REPO_ROOT="$(CDPATH= cd -- "${SCRIPT_DIR}/../.." && pwd)"

cd "${REPO_ROOT}/native-android"
chmod +x gradlew

# Stable order: RangeSlider first (fresh emulator), then isolated screens, service, notification last.
TEST_CLASSES="
com.iganapolsky.randomtimer.ui.RangeSliderUiTest
com.iganapolsky.randomtimer.ui.screens.ActiveTimerScreenLandscapeLayoutTest
com.iganapolsky.randomtimer.ui.screens.ActiveTimerScreenTapCircleTest
com.iganapolsky.randomtimer.ui.TimerSetupSmokeTest
com.iganapolsky.randomtimer.service.TimerForegroundServiceResetTest
com.iganapolsky.randomtimer.ui.NotificationE2ETest
"

echo "== Android connectedDebugAndroidTest (per-class isolation) =="
for test_class in ${TEST_CLASSES}; do
  adb shell am force-stop com.iganapolsky.randomtimer 2>/dev/null || true
  echo "-- class ${test_class} --"
  ./gradlew connectedDebugAndroidTest \
    --no-daemon \
    --stacktrace \
    -PenableFirebasePlugins=false \
    -Pandroid.testInstrumentationRunnerArguments.class="${test_class}"
done
