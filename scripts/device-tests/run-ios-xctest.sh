#!/usr/bin/env bash
# run-ios-xctest.sh — iOS Simulator E2E via XCUITest (reliable on local Xcode).
#
# Usage:
#   ./scripts/device-tests/run-ios-xctest.sh [--device 'iPhone 17 Pro']
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
NATIVE_IOS_DIR="$PROJECT_ROOT/native-ios"
DESTINATION="${IOS_XCTEST_DESTINATION:-platform=iOS Simulator,name=iPhone 17 Pro}"

while [ $# -gt 0 ]; do
  case "$1" in
    --device)
      DESTINATION="platform=iOS Simulator,name=${2:-iPhone 17 Pro}"
      shift 2
      ;;
    --help|-h)
      echo "Usage: $0 [--device 'iPhone 17 Pro']"
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

# Core flows mirrored from .maestro/ios-*.yaml
UITESTS=(
  "RandomTimerUITests/RandomTimerUITests/testSetupStateShowsStartTimer"
  "RandomTimerUITests/RandomTimerUITests/testSetupStateKeepsStartTimerHittable"
  "RandomTimerUITests/RandomTimerUITests/testRunningStateShowsRunningLabelAndPauseAction"
  "RandomTimerUITests/RandomTimerUITests/testPausedStateShowsPausedLabelAndResumeAction"
  "RandomTimerUITests/RandomTimerUITests/testAlarmStateShowsStopAndResetActions"
  "RandomTimerUITests/RandomTimerUITests/testTappingTimerCircleSilencesAlarmAndStaysOnScreen"
  "RandomTimerUITests/RandomTimerUITests/testFreeSetupShowsPreviewWithoutExtendedRangeToggle"
  "RandomTimerUITests/RandomTimerUITests/testProSetupShowsExtendedRangeToggleAndHidesPreview"
)

ONLY_FLAGS=()
for t in "${UITESTS[@]}"; do
  ONLY_FLAGS+=("-only-testing:${t}")
done

echo "Running XCUITest E2E on: $DESTINATION"
# Stabilize CoreSimulator after Maestro/idb sessions (Mach -308 if sim is wedged).
xcrun simctl shutdown all 2>/dev/null || true
sleep 2
open -a Simulator >/dev/null 2>&1 || true
sleep 2

cd "$NATIVE_IOS_DIR"
xcodebuild test \
  -project RandomTimer.xcodeproj \
  -scheme RandomTimer \
  -destination "$DESTINATION" \
  "${ONLY_FLAGS[@]}" \
  CODE_SIGNING_ALLOWED=NO \
  'OTHER_SWIFT_FLAGS=$(inherited) -D RT_SKIP_FIREBASE_FOR_CI'
