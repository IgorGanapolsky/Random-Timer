#!/usr/bin/env bash
set -euo pipefail

# iOS verification helper.
#
# Usage:
#   ./scripts/shell/ios_verify.sh        # unit tests only (skips UI tests)
#   ./scripts/shell/ios_verify.sh --ui   # includes UI tests

include_ui_tests=false
if [[ "${1:-}" == "--ui" ]]; then
  include_ui_tests=true
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT/native-ios"

echo "==> Selecting an available iPhone simulator..."
SIM_ID="$(
  xcrun simctl list devices available -j | python3 -c '
import json, sys
data = json.load(sys.stdin)
for runtime, devices in data.get("devices", {}).items():
    if "iOS" not in runtime:
        continue
    for d in devices:
        if d.get("isAvailable") and "iPhone" in d.get("name", ""):
            print(d["udid"])
            raise SystemExit(0)
raise SystemExit("No available iPhone simulator found")
'
)"

echo "==> Using simulator id: ${SIM_ID}"

echo "==> Build for testing..."
if [[ "${include_ui_tests}" == "false" ]]; then
  xcodebuild build-for-testing \
    -project RandomTimer.xcodeproj \
    -scheme RandomTimer \
    -destination "platform=iOS Simulator,id=${SIM_ID}" \
    -skip-testing:RandomTimerUITests \
    -quiet \
    CODE_SIGNING_ALLOWED=NO
else
  xcodebuild build-for-testing \
    -project RandomTimer.xcodeproj \
    -scheme RandomTimer \
    -destination "platform=iOS Simulator,id=${SIM_ID}" \
    -quiet \
    CODE_SIGNING_ALLOWED=NO
fi

echo "==> Run tests..."
if [[ "${include_ui_tests}" == "false" ]]; then
  xcodebuild test \
    -project RandomTimer.xcodeproj \
    -scheme RandomTimer \
    -destination "platform=iOS Simulator,id=${SIM_ID}" \
    -skip-testing:RandomTimerUITests \
    -quiet \
    CODE_SIGNING_ALLOWED=NO
else
  xcodebuild test \
    -project RandomTimer.xcodeproj \
    -scheme RandomTimer \
    -destination "platform=iOS Simulator,id=${SIM_ID}" \
    -quiet \
    CODE_SIGNING_ALLOWED=NO
fi
