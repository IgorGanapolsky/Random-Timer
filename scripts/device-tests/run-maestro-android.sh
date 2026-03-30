#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <maestro-flow> [additional maestro args...]" >&2
  exit 2
fi

if ! command -v adb >/dev/null 2>&1; then
  echo "adb is required to run Android Maestro flows" >&2
  exit 2
fi

if ! command -v maestro >/dev/null 2>&1; then
  echo "maestro CLI is required to run Android Maestro flows" >&2
  exit 2
fi

SERIAL="${ANDROID_SERIAL:-$(adb devices | awk '/device$/{print $1; exit}')}"
if [ -z "$SERIAL" ]; then
  echo "No Android device/emulator connected." >&2
  exit 2
fi

MAESTRO_CLIENT_JAR="${MAESTRO_CLIENT_JAR:-$HOME/.maestro/lib/maestro-client.jar}"
if [ ! -f "$MAESTRO_CLIENT_JAR" ]; then
  echo "Maestro client jar not found at $MAESTRO_CLIENT_JAR" >&2
  exit 2
fi

PORT="${MAESTRO_ANDROID_PORT:-7001}"
DRIVER_DIR="${TMPDIR:-/tmp}/maestro-android-driver"
APP_APK="$DRIVER_DIR/maestro-app.apk"
SERVER_APK="$DRIVER_DIR/maestro-server.apk"
INSTRUMENT_LOG="$DRIVER_DIR/instrumentation.log"

mkdir -p "$DRIVER_DIR"
unzip -p "$MAESTRO_CLIENT_JAR" maestro-app.apk > "$APP_APK"
unzip -p "$MAESTRO_CLIENT_JAR" maestro-server.apk > "$SERVER_APK"

adb -s "$SERIAL" wait-for-device >/dev/null
adb -s "$SERIAL" install -r -t "$APP_APK" >/dev/null
adb -s "$SERIAL" install -r -t "$SERVER_APK" >/dev/null

adb -s "$SERIAL" shell am force-stop dev.mobile.maestro >/dev/null 2>&1 || true
adb -s "$SERIAL" shell am force-stop dev.mobile.maestro.test >/dev/null 2>&1 || true
adb -s "$SERIAL" forward --remove "tcp:$PORT" >/dev/null 2>&1 || true
adb -s "$SERIAL" forward "tcp:$PORT" "tcp:$PORT" >/dev/null

adb -s "$SERIAL" shell am instrument -w dev.mobile.maestro.test/androidx.test.runner.AndroidJUnitRunner \
  >"$INSTRUMENT_LOG" 2>&1 &
INSTRUMENT_PID=$!

cleanup() {
  kill "$INSTRUMENT_PID" >/dev/null 2>&1 || true
  adb -s "$SERIAL" shell am force-stop dev.mobile.maestro >/dev/null 2>&1 || true
  adb -s "$SERIAL" shell am force-stop dev.mobile.maestro.test >/dev/null 2>&1 || true
  adb -s "$SERIAL" forward --remove "tcp:$PORT" >/dev/null 2>&1 || true
}
trap cleanup EXIT

READY=false
for _ in $(seq 1 20); do
  if nc -z localhost "$PORT" >/dev/null 2>&1; then
    READY=true
    break
  fi
  sleep 1
done

if [ "$READY" != "true" ]; then
  echo "Timed out waiting for Maestro Android driver on localhost:$PORT" >&2
  if [ -f "$INSTRUMENT_LOG" ]; then
    echo "--- instrumentation log ---" >&2
    tail -n 40 "$INSTRUMENT_LOG" >&2 || true
  fi
  exit 1
fi

cd "$PROJECT_ROOT"
adb -s "$SERIAL" wait-for-device >/dev/null
adb -s "$SERIAL" shell true >/dev/null
sleep 1

TMP_ROOT="${TMPDIR:-/tmp}"
TMP_ROOT="${TMP_ROOT%/}"
MAESTRO_RUN_LOG="$(mktemp "$TMP_ROOT/maestro-android-run.XXXXXX")"
set +e
maestro test --no-reinstall-driver --device "$SERIAL" "$@" 2>&1 | tee "$MAESTRO_RUN_LOG"
STATUS=${PIPESTATUS[0]}
set -e

if [ "$STATUS" -ne 0 ] && grep -Eq "device offline|Unable to launch app|UNAVAILABLE: io exception|Connection refused" "$MAESTRO_RUN_LOG"; then
  adb -s "$SERIAL" wait-for-device >/dev/null
  adb -s "$SERIAL" shell true >/dev/null
  sleep 1
  maestro test --no-reinstall-driver --device "$SERIAL" "$@"
  exit $?
fi

exit "$STATUS"
