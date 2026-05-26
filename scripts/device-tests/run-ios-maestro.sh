#!/usr/bin/env bash
# run-ios-maestro.sh — iOS Simulator Maestro flows (CI parity). Requires working Maestro+iOS pairing.
#
# Usage:
#   ./scripts/device-tests/run-ios-maestro.sh [--udid <SIM_UDID>] [--skip-build] [--smoke-only]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
export DEVICE_TESTS_REPO_ROOT="$PROJECT_ROOT"
# shellcheck source=lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

NATIVE_IOS_DIR="$PROJECT_ROOT/native-ios"
BUNDLE_ID="com.igorganapolsky.randomtimer"
DERIVED_DATA_PATH="$NATIVE_IOS_DIR/build/local-e2e-ios"
APP_PATH="$DERIVED_DATA_PATH/Build/Products/Debug-iphonesimulator/RandomTimer.app"
MAESTRO_DIR="$PROJECT_ROOT/.maestro"
FLOW_TIMEOUT_SECONDS="${MAESTRO_FLOW_TIMEOUT_SECONDS:-300}"
IOS_BUILD_TIMEOUT_SECONDS="${IOS_BUILD_TIMEOUT_SECONDS:-900}"

UDID=""
SKIP_BUILD=false
SMOKE_ONLY=false

while [ $# -gt 0 ]; do
  case "$1" in
    --udid)
      UDID="${2:-}"
      shift 2
      ;;
    --skip-build)
      SKIP_BUILD=true
      shift
      ;;
    --smoke-only)
      SMOKE_ONLY=true
      shift
      ;;
    --help|-h)
      echo "Usage: $0 [--udid <SIM_UDID>] [--skip-build] [--smoke-only]"
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

require_maestro

resolve_simulator_udid() {
  if [ -n "$UDID" ]; then
    return 0
  fi
  UDID="$(xcrun simctl list devices booted | awk -F '[()]' '/Booted/ {print $2; exit}')"
  if [ -z "$UDID" ]; then
    UDID="$(xcrun simctl list devices available | awk -F '[()]' '/iPhone/ {print $2; exit}')"
    if [ -z "$UDID" ]; then
      echo "No available iPhone simulators found." >&2
      exit 2
    fi
  fi
}

run_with_timeout() {
  local seconds="$1"
  shift
  python3 - "$seconds" "$@" <<'PY'
import os
import signal
import subprocess
import sys

seconds = int(sys.argv[1])
cmd = sys.argv[2:]
proc = subprocess.Popen(cmd, start_new_session=True)
try:
    sys.exit(proc.wait(timeout=seconds))
except subprocess.TimeoutExpired:
    print(f"::error::Command timed out after {seconds}s: {' '.join(cmd)}", file=sys.stderr)
    os.killpg(proc.pid, signal.SIGTERM)
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        proc.wait()
    sys.exit(124)
PY
}

run_maestro_flow() {
  local name="$1"
  local flow="$2"
  local attempt
  for attempt in 1 2 3; do
    echo "Maestro ${name}: attempt ${attempt}/3"
    if run_with_timeout "$FLOW_TIMEOUT_SECONDS" maestro test -p ios --device "$UDID" "$flow"; then
      return 0
    fi
    xcrun simctl terminate "$UDID" "$BUNDLE_ID" 2>/dev/null || true
    sleep 5
  done
  return 1
}

resolve_simulator_udid
echo "Using iOS simulator UDID: $UDID"
open -a Simulator >/dev/null 2>&1 || true
xcrun simctl boot "$UDID" 2>/dev/null || true
run_with_timeout 120 xcrun simctl bootstatus "$UDID" -b

if [ "$SKIP_BUILD" = false ]; then
  echo "Building iOS simulator app..."
  cd "$NATIVE_IOS_DIR"
  rm -rf "$DERIVED_DATA_PATH"
  run_with_timeout "$IOS_BUILD_TIMEOUT_SECONDS" xcodebuild build \
    -project RandomTimer.xcodeproj \
    -scheme RandomTimer \
    -destination "platform=iOS Simulator,id=${UDID}" \
    -derivedDataPath "$DERIVED_DATA_PATH" \
    -quiet \
    CODE_SIGNING_ALLOWED=NO \
    'OTHER_SWIFT_FLAGS=$(inherited) -D RT_SKIP_FIREBASE_FOR_CI'
fi

if [ ! -d "$APP_PATH" ]; then
  echo "Built app not found at $APP_PATH" >&2
  exit 1
fi

echo "Installing app on simulator..."
xcrun simctl uninstall "$UDID" "$BUNDLE_ID" 2>/dev/null || true
run_with_timeout 120 xcrun simctl install "$UDID" "$APP_PATH"
xcrun simctl privacy "$UDID" grant notifications "$BUNDLE_ID" 2>/dev/null || true

if [ "$SMOKE_ONLY" = true ]; then
  FLOWS=( "ios-smoke-test.yaml" )
else
  FLOWS=(
    "ios-smoke-test.yaml"
    "regression-pro-locks-visible-ios.yaml"
    "regression-free-sound-preview-ios.yaml"
    "regression-sound-arsenal-paywall-ios.yaml"
    "regression-paywall-sticky-cta-ios.yaml"
  )
fi

FAIL=0
for flow in "${FLOWS[@]}"; do
  flow_path="$MAESTRO_DIR/$flow"
  echo ""
  echo "Running: $flow"
  if ! run_maestro_flow "$flow" "$flow_path"; then
    FAIL=1
  fi
done

exit "$FAIL"
