#!/usr/bin/env sh
# ci-maestro.sh — Run Android UI smoke verification on an emulator in CI.
# Called by .github/workflows/device-tests.yml
set -eu

adb shell am force-stop com.iganapolsky.randomtimer 2>/dev/null || true
adb shell pm clear com.iganapolsky.randomtimer 2>/dev/null || true

cd native-android
chmod +x gradlew

# Compose instrumentation is more reliable than Maestro for this setup screen on CI emulators.
./gradlew connectedDebugAndroidTest \
  --no-daemon \
  --stacktrace \
  -PenableFirebasePlugins=false \
  -Pandroid.testInstrumentationRunnerArguments.class=com.iganapolsky.randomtimer.ui.TimerSetupSmokeTest
