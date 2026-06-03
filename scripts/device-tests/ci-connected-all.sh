#!/usr/bin/env sh
# ci-connected-all.sh — Run every connectedDebugAndroidTest class on CI emulator.
# device-tests.yml runs only TimerSetupSmokeTest; native-release must gate on the full suite.
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
REPO_ROOT="$(CDPATH= cd -- "${SCRIPT_DIR}/../.." && pwd)"

adb shell am force-stop com.iganapolsky.randomtimer 2>/dev/null || true

cd "${REPO_ROOT}/native-android"
chmod +x gradlew

echo "== Android connectedDebugAndroidTest (all classes) =="
./gradlew connectedDebugAndroidTest \
  --no-daemon \
  --stacktrace \
  -PenableFirebasePlugins=false
