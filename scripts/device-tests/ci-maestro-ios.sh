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

mkdir -p "$MAESTRO_ARTIFACT_DIR" "$AGENT_DEVICE_ARTIFACT_DIR"
export AGENT_DEVICE_SESSION="${AGENT_DEVICE_SESSION:-random-timer-ios-ci}"
export AGENT_DEVICE_RUN_ID="${GITHUB_RUN_ID:-local}"
export AGENT_DEVICE_SESSION_LOCK=strip

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
  shift
  local attempt
  for attempt in 1 2 3; do
    echo "Agent Device ${label}: attempt ${attempt}/3"
    if "$@"; then
      return 0
    fi
    copy_agent_device_logs
    sleep 5
  done
  return 1
}

retry_agent_device_capture() {
  local label="$1"
  local output="$2"
  shift 2
  local attempt
  for attempt in 1 2 3; do
    echo "Agent Device ${label}: attempt ${attempt}/3"
    if "$@" > "$output"; then
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
  for attempt in 1 2; do
    echo "Maestro ${name}: attempt ${attempt}/2"
    if maestro test -p ios --device "$SIMULATOR_UDID" "$flow" \
      | tee "$MAESTRO_ARTIFACT_DIR/${name}-attempt-${attempt}.log"; then
      return 0
    fi
    sleep 10
  done
  return 1
}

xcrun simctl shutdown "$SIMULATOR_UDID" 2>/dev/null || true
xcrun simctl boot "$SIMULATOR_UDID" 2>/dev/null || true
xcrun simctl bootstatus "$SIMULATOR_UDID" -b

cd "$NATIVE_IOS_DIR"
rm -rf "$DERIVED_DATA_PATH"
xcodebuild build \
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

xcrun simctl uninstall "$SIMULATOR_UDID" "$BUNDLE_ID" 2>/dev/null || true
xcrun simctl install "$SIMULATOR_UDID" "$APP_PATH"

run_maestro_flow "ios-smoke" "$PROJECT_ROOT/.maestro/ios-smoke-test.yaml"
run_maestro_flow "pro-locks" "$PROJECT_ROOT/.maestro/regression-pro-locks-visible-ios.yaml"
run_maestro_flow "free-sound-preview" "$PROJECT_ROOT/.maestro/regression-free-sound-preview-ios.yaml"
run_maestro_flow "sound-arsenal-paywall" "$PROJECT_ROOT/.maestro/regression-sound-arsenal-paywall-ios.yaml"

retry_agent_device "install" agent_device install "$BUNDLE_ID" "$APP_PATH"
retry_agent_device "open" agent_device open "$BUNDLE_ID" --relaunch
retry_agent_device "wait-home" agent_device wait "Random Tactical Timer" 60000
retry_agent_device_capture "snapshot" "$AGENT_DEVICE_ARTIFACT_DIR/interactive-snapshot.txt" \
  agent_device snapshot -i -c --depth 8
grep -q "Random Tactical Timer" "$AGENT_DEVICE_ARTIFACT_DIR/interactive-snapshot.txt"
retry_agent_device "screenshot" agent_device screenshot "$AGENT_DEVICE_ARTIFACT_DIR/home.png"
agent_device close "$BUNDLE_ID" || true
