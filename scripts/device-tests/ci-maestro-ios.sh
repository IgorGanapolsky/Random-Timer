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

if ! command -v maestro >/dev/null 2>&1; then
  curl -Ls "https://get.maestro.mobile.dev" | bash
fi
export PATH="$HOME/.maestro/bin:$PATH"
export MAESTRO_DRIVER_STARTUP_TIMEOUT=120000
export MAESTRO_DISABLE_ANALYTICS=true

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

maestro test -p ios --device "$SIMULATOR_UDID" "$PROJECT_ROOT/.maestro/ios-smoke-test.yaml" \
  | tee "$MAESTRO_ARTIFACT_DIR/ios-smoke.log"
maestro test -p ios --device "$SIMULATOR_UDID" "$PROJECT_ROOT/.maestro/regression-pro-locks-visible-ios.yaml" \
  | tee "$MAESTRO_ARTIFACT_DIR/pro-locks.log"
maestro test -p ios --device "$SIMULATOR_UDID" "$PROJECT_ROOT/.maestro/regression-sound-arsenal-paywall-ios.yaml" \
  | tee "$MAESTRO_ARTIFACT_DIR/sound-arsenal-paywall.log"

npx -y agent-device install "$BUNDLE_ID" "$APP_PATH" --platform ios --udid "$SIMULATOR_UDID"
npx -y agent-device open "$BUNDLE_ID" --platform ios --udid "$SIMULATOR_UDID" --relaunch
npx -y agent-device snapshot -i --platform ios --udid "$SIMULATOR_UDID" \
  > "$AGENT_DEVICE_ARTIFACT_DIR/interactive-snapshot.txt"
grep -q "Random Tactical Timer" "$AGENT_DEVICE_ARTIFACT_DIR/interactive-snapshot.txt"
npx -y agent-device screenshot "$AGENT_DEVICE_ARTIFACT_DIR/home.png" --platform ios --udid "$SIMULATOR_UDID"
npx -y agent-device close "$BUNDLE_ID" --platform ios --udid "$SIMULATOR_UDID"
