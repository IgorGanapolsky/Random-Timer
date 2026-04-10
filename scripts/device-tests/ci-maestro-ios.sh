#!/usr/bin/env bash
# ci-maestro-ios.sh — Run iOS simulator smoke/regression verification in CI.
# Called by .github/workflows/device-tests.yml
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
NATIVE_IOS_DIR="$PROJECT_ROOT/native-ios"
SIMULATOR_UDID="${SIMULATOR_UDID:?SIMULATOR_UDID is required}"
BUNDLE_ID="com.igorganapolsky.randomtimer"
DERIVED_DATA_PATH="$NATIVE_IOS_DIR/build/device-tests-ios"
APP_PATH="$DERIVED_DATA_PATH/Build/Products/Debug-iphonesimulator/RandomTimer.app"
MAESTRO_ARTIFACT_DIR="$NATIVE_IOS_DIR/build/maestro"
AGENT_DEVICE_ARTIFACT_DIR="$NATIVE_IOS_DIR/build/agent-device"
LAST_STAGE_FILE="$AGENT_DEVICE_ARTIFACT_DIR/last-stage.txt"
IOS_BUILD_TIMEOUT_SECONDS="${IOS_BUILD_TIMEOUT_SECONDS:-900}"
MAESTRO_FLOW_TIMEOUT_SECONDS="${MAESTRO_FLOW_TIMEOUT_SECONDS:-420}"
AGENT_DEVICE_TIMEOUT_SECONDS="${AGENT_DEVICE_TIMEOUT_SECONDS:-120}"
AGENT_DEVICE_DIAGNOSTIC_TIMEOUT_SECONDS="${AGENT_DEVICE_DIAGNOSTIC_TIMEOUT_SECONDS:-30}"
SIMCTL_TIMEOUT_SECONDS="${SIMCTL_TIMEOUT_SECONDS:-120}"

mkdir -p "$MAESTRO_ARTIFACT_DIR" "$AGENT_DEVICE_ARTIFACT_DIR"
export AGENT_DEVICE_SESSION="${AGENT_DEVICE_SESSION:-random-timer-ios-ci}"
export AGENT_DEVICE_RUN_ID="${GITHUB_RUN_ID:-local}"
export AGENT_DEVICE_SESSION_LOCK=strip

record_stage() {
  printf '%s %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$*" | tee "$LAST_STAGE_FILE"
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

copy_agent_device_logs() {
  if [ -d "$HOME/.agent-device/logs" ]; then
    rm -rf "$AGENT_DEVICE_ARTIFACT_DIR/logs"
    cp -R "$HOME/.agent-device/logs" "$AGENT_DEVICE_ARTIFACT_DIR/logs"
  fi
}

trap copy_agent_device_logs EXIT

agent_device() {
  npx -y agent-device "$@" --platform ios --udid "$SIMULATOR_UDID" --no-record
}

retry_agent_device() {
  local label="$1"
  local seconds="$2"
  shift 2
  local attempt
  for attempt in 1 2 3; do
    record_stage "agent-device ${label} attempt ${attempt}"
    echo "Agent Device ${label}: attempt ${attempt}/3"
    if run_with_timeout "$seconds" npx -y agent-device "$@" --platform ios --udid "$SIMULATOR_UDID" --no-record; then
      return 0
    fi
    copy_agent_device_logs
    sleep 5
  done
  return 1
}

retry_agent_device_capture() {
  local label="$1"
  local seconds="$2"
  local output="$3"
  shift 3
  local attempt
  for attempt in 1 2 3; do
    record_stage "agent-device ${label} attempt ${attempt}"
    echo "Agent Device ${label}: attempt ${attempt}/3"
    if run_with_timeout "$seconds" npx -y agent-device "$@" --platform ios --udid "$SIMULATOR_UDID" --no-record > "$output"; then
      return 0
    fi
    copy_agent_device_logs
    sleep 5
  done
  return 1
}

if ! command -v maestro >/dev/null 2>&1; then
  curl -Ls "https://get.maestro.mobile.dev" | bash
fi
export PATH="$HOME/.maestro/bin:$PATH"
export MAESTRO_DRIVER_STARTUP_TIMEOUT=300000
export MAESTRO_DISABLE_ANALYTICS=true

run_maestro_flow() {
  local name="$1"
  local flow="$2"
  local attempt
  local log_path
  for attempt in 1 2; do
    log_path="$MAESTRO_ARTIFACT_DIR/${name}-attempt-${attempt}.log"
    record_stage "maestro ${name} attempt ${attempt}"
    echo "Maestro ${name}: attempt ${attempt}/2"
    if run_with_timeout "$MAESTRO_FLOW_TIMEOUT_SECONDS" bash -o pipefail -c \
      'maestro test -p ios --device "$1" "$2" | tee "$3"' \
      _ "$SIMULATOR_UDID" "$flow" "$log_path"; then
      return 0
    fi
    sleep 10
  done
  return 1
}

xcrun simctl shutdown "$SIMULATOR_UDID" 2>/dev/null || true
xcrun simctl boot "$SIMULATOR_UDID" 2>/dev/null || true
record_stage "boot simulator"
run_with_timeout "$SIMCTL_TIMEOUT_SECONDS" xcrun simctl bootstatus "$SIMULATOR_UDID" -b

cd "$NATIVE_IOS_DIR"
rm -rf "$DERIVED_DATA_PATH"
record_stage "xcodebuild simulator app"
run_with_timeout "$IOS_BUILD_TIMEOUT_SECONDS" xcodebuild build \
  -project RandomTimer.xcodeproj \
  -scheme RandomTimer \
  -destination "platform=iOS Simulator,id=${SIMULATOR_UDID}" \
  -derivedDataPath "$DERIVED_DATA_PATH" \
  -quiet \
  CODE_SIGNING_ALLOWED=NO \
  'OTHER_SWIFT_FLAGS=$(inherited) -D RT_SKIP_FIREBASE_FOR_CI'

if [ ! -d "$APP_PATH" ]; then
  echo "Built app not found at $APP_PATH"
  exit 1
fi

record_stage "install simulator app"
xcrun simctl uninstall "$SIMULATOR_UDID" "$BUNDLE_ID" 2>/dev/null || true
run_with_timeout "$SIMCTL_TIMEOUT_SECONDS" xcrun simctl install "$SIMULATOR_UDID" "$APP_PATH"

run_maestro_flow "ios-smoke" "$PROJECT_ROOT/.maestro/ios-smoke-test.yaml"
run_maestro_flow "pro-locks" "$PROJECT_ROOT/.maestro/regression-pro-locks-visible-ios.yaml"
run_maestro_flow "free-sound-preview" "$PROJECT_ROOT/.maestro/regression-free-sound-preview-ios.yaml"
run_maestro_flow "sound-arsenal-paywall" "$PROJECT_ROOT/.maestro/regression-sound-arsenal-paywall-ios.yaml"

# The paywall regression flow intentionally leaves the app on the paywall.
# Reset app state before Agent Device validates the home screen.
xcrun simctl terminate "$SIMULATOR_UDID" "$BUNDLE_ID" 2>/dev/null || true
xcrun simctl uninstall "$SIMULATOR_UDID" "$BUNDLE_ID" 2>/dev/null || true
record_stage "reinstall simulator app for agent-device"
run_with_timeout "$SIMCTL_TIMEOUT_SECONDS" xcrun simctl install "$SIMULATOR_UDID" "$APP_PATH"

retry_agent_device "install" "$AGENT_DEVICE_TIMEOUT_SECONDS" install "$BUNDLE_ID" "$APP_PATH"
retry_agent_device "open" "$AGENT_DEVICE_TIMEOUT_SECONDS" open "$BUNDLE_ID" --relaunch
sleep 8
xcrun simctl io "$SIMULATOR_UDID" screenshot "$AGENT_DEVICE_ARTIFACT_DIR/home-pre-agent.png" || true
if [ ! -s "$AGENT_DEVICE_ARTIFACT_DIR/home-pre-agent.png" ]; then
  echo "Simulator home screenshot was not captured."
  exit 1
fi

# Agent Device screenshot/snapshot can hang or focus its runner shell on macOS runners.
# Keep them as bounded diagnostic artifacts; Maestro assertions and simctl screenshots are the blocking app proof.
record_stage "agent-device diagnostic screenshot"
if ! run_with_timeout "$AGENT_DEVICE_DIAGNOSTIC_TIMEOUT_SECONDS" npx -y agent-device \
  screenshot "$AGENT_DEVICE_ARTIFACT_DIR/home.png" --platform ios --udid "$SIMULATOR_UDID" --no-record; then
  echo "::warning::Agent Device screenshot failed; preserving simctl screenshot and logs."
  copy_agent_device_logs
fi

record_stage "agent-device diagnostic snapshot"
if run_with_timeout "$AGENT_DEVICE_DIAGNOSTIC_TIMEOUT_SECONDS" npx -y agent-device \
  snapshot -i -c --depth 8 --platform ios --udid "$SIMULATOR_UDID" --no-record \
  > "$AGENT_DEVICE_ARTIFACT_DIR/interactive-snapshot.txt"; then
  if ! grep -Eq "Random Tactical Timer|Start Timer|Timer Range" "$AGENT_DEVICE_ARTIFACT_DIR/interactive-snapshot.txt"; then
    echo "::warning::Agent Device snapshot did not include expected home anchors; preserving diagnostic snapshot."
    sed -n '1,160p' "$AGENT_DEVICE_ARTIFACT_DIR/interactive-snapshot.txt"
  fi
else
  echo "::warning::Agent Device snapshot failed; preserving logs and screenshot artifacts."
  copy_agent_device_logs
fi
agent_device close "$BUNDLE_ID" || true
