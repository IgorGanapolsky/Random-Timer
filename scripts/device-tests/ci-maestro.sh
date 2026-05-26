#!/usr/bin/env sh
# ci-maestro.sh — Android device smoke on CI emulator.
# 1) Compose instrumentation (stable on API 30 emulator)
# 2) Maestro ci-smoke-test.yaml (parity with local Maestro flows)
# Called by .github/workflows/device-tests.yml
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
REPO_ROOT="$(CDPATH= cd -- "${SCRIPT_DIR}/../.." && pwd)"

adb shell am force-stop com.iganapolsky.randomtimer 2>/dev/null || true

cd "${REPO_ROOT}/native-android"
chmod +x gradlew

echo "== Android Compose smoke (TimerSetupSmokeTest) =="
./gradlew connectedDebugAndroidTest \
  --no-daemon \
  --stacktrace \
  -PenableFirebasePlugins=false \
  -Pandroid.testInstrumentationRunnerArguments.class=com.iganapolsky.randomtimer.ui.TimerSetupSmokeTest

echo "== Android Maestro smoke (ci-smoke-emulator.yaml) =="
APK="${REPO_ROOT}/native-android/app/build/outputs/apk/debug/app-debug.apk"
if [ ! -f "${APK}" ]; then
  echo "Debug APK missing; assembling..."
  ./gradlew assembleDebug --no-daemon -q -PenableFirebasePlugins=false
fi
adb install -r -d "${APK}" || adb install -r "${APK}"

if ! command -v maestro >/dev/null 2>&1; then
  curl -Ls "https://get.maestro.mobile.dev" | bash
fi
export PATH="${HOME}/.maestro/bin:${PATH}"
export MAESTRO_DRIVER_STARTUP_TIMEOUT="${MAESTRO_DRIVER_STARTUP_TIMEOUT:-180000}"
export MAESTRO_DISABLE_ANALYTICS=true

cd "${REPO_ROOT}"
maestro test .maestro/ci-smoke-emulator.yaml
