#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  capture_ios_store_screenshots.sh [--repo-root <path>] [--locale <locale>]

Captures clean raw iOS App Store screenshots into:
  native-ios/fastlane/screenshots/<locale>/originals/

The script drives the existing UI test target in a deterministic capture mode
for one large iPhone and one 13-inch iPad simulator, then prints pixel sizes
for the captured PNGs.
EOF
}

REPO_ROOT=""
LOCALE="en-US"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-root) REPO_ROOT="$2"; shift 2 ;;
    --locale) LOCALE="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ -z "$REPO_ROOT" ]]; then
  REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fi

cd "$REPO_ROOT"

resolve_latest_ios_runtime() {
  xcrun simctl list runtimes -j | python3 -c '
import json
import re
import sys

runtimes = []
for runtime in json.load(sys.stdin).get("runtimes", []):
    identifier = runtime.get("identifier", "")
    if not identifier.startswith("com.apple.CoreSimulator.SimRuntime.iOS-"):
        continue
    if not runtime.get("isAvailable", False):
        continue
    version = runtime.get("version") or identifier
    version_key = tuple(int(part) for part in re.findall(r"\d+", version or identifier))
    runtimes.append((version_key, identifier))

if not runtimes:
    raise SystemExit("No available iOS simulator runtime found")

print(sorted(runtimes, reverse=True)[0][1])
'
}

resolve_device_type() {
  local family="$1"
  shift

  xcrun simctl list devicetypes -j | env FAMILY="$family" PREFERRED_IDS="$(IFS=,; echo "$*")" python3 -c '
import json
import os
import sys

family = os.environ["FAMILY"]
preferred_ids = [item for item in os.environ.get("PREFERRED_IDS", "").split(",") if item]
device_types = json.load(sys.stdin).get("devicetypes", [])
identifiers = {device_type.get("identifier", ""): device_type for device_type in device_types}

for identifier in preferred_ids:
    if identifier in identifiers:
        print(identifier)
        raise SystemExit(0)

needle = "iPhone" if family == "iphone" else "iPad"
for device_type in device_types:
    if needle in device_type.get("name", ""):
        print(device_type["identifier"])
        raise SystemExit(0)

raise SystemExit(f"No available {needle} simulator device type found")
'
}

find_existing_sim() {
  local name="$1"
  local runtime_id="$2"

  xcrun simctl list devices available -j | env SIM_NAME="$name" SIM_RUNTIME_ID="$runtime_id" python3 -c '
import json
import os
import sys

devices = json.load(sys.stdin).get("devices", {})
for device in devices.get(os.environ["SIM_RUNTIME_ID"], []):
    if device.get("isAvailable") and device.get("name") == os.environ["SIM_NAME"]:
        print(device["udid"])
        raise SystemExit(0)
'
}

RUNTIME_ID="$(resolve_latest_ios_runtime)"
IPHONE_TYPE="$(resolve_device_type iphone \
  com.apple.CoreSimulator.SimDeviceType.iPhone-17-Pro-Max \
  com.apple.CoreSimulator.SimDeviceType.iPhone-16-Pro-Max \
  com.apple.CoreSimulator.SimDeviceType.iPhone-15-Pro-Max)"
IPAD_TYPE="$(resolve_device_type ipad \
  com.apple.CoreSimulator.SimDeviceType.iPad-Pro-13-inch-M5-16GB \
  com.apple.CoreSimulator.SimDeviceType.iPad-Pro-13-inch-M5-12GB \
  com.apple.CoreSimulator.SimDeviceType.iPad-Pro-13-inch-M4-16GB \
  com.apple.CoreSimulator.SimDeviceType.iPad-Pro-13-inch-M4-8GB \
  com.apple.CoreSimulator.SimDeviceType.iPad-Pro-12-9-inch-6th-generation-16GB \
  com.apple.CoreSimulator.SimDeviceType.iPad-Pro-12-9-inch-6th-generation-8GB)"
IPHONE_NAME="RandomTimer AppStore iPhone 16 Pro Max"
IPAD_NAME="RandomTimer AppStore iPad Pro 13 M4"

ensure_sim() {
  local name="$1"
  local type="$2"
  local existing_udid=""
  existing_udid="$(find_existing_sim "$name" "$RUNTIME_ID" || true)"
  if [[ -n "$existing_udid" ]]; then
    echo "$existing_udid"
    return 0
  fi

  xcrun simctl create "$name" "$type" "$RUNTIME_ID"
}

IPHONE_UDID="$(ensure_sim "$IPHONE_NAME" "$IPHONE_TYPE")"
IPAD_UDID="$(ensure_sim "$IPAD_NAME" "$IPAD_TYPE")"

echo "==> Using iOS runtime: $RUNTIME_ID"
echo "==> Using iPhone simulator type: $IPHONE_TYPE ($IPHONE_UDID)"
echo "==> Using iPad simulator type: $IPAD_TYPE ($IPAD_UDID)"

OUT_DIR="native-ios/fastlane/screenshots/$LOCALE/originals"
TMP_OUT_DIR="/tmp/appstore_screenshots"
mkdir -p "$OUT_DIR"

BACKUP_DIR="$OUT_DIR/_backup/$(date +%Y%m%d_%H%M%S)"
shopt -s nullglob
existing_raws=("$OUT_DIR"/*.png)
if [[ ${#existing_raws[@]} -gt 0 ]]; then
  mkdir -p "$BACKUP_DIR"
  mv "$OUT_DIR"/*.png "$BACKUP_DIR"/
fi
shopt -u nullglob

mkdir -p "$TMP_OUT_DIR"
find "$TMP_OUT_DIR" -mindepth 1 -maxdepth 1 -delete 2>/dev/null || true

run_capture() {
  local destination="$1"
  shift
  xcodebuild test-without-building \
    -project native-ios/RandomTimer.xcodeproj \
    -scheme RandomTimer \
    -destination "$destination" \
    "$@" \
    CODE_SIGNING_ALLOWED=NO
}

IPHONE_CAPTURE_TESTS=(
  -only-testing:RandomTimerUITests/RandomTimerUITests/testCaptureAppStorePhoneSetupScreenshot
  -only-testing:RandomTimerUITests/RandomTimerUITests/testCaptureAppStorePhoneActiveScreenshot
  -only-testing:RandomTimerUITests/RandomTimerUITests/testCaptureAppStorePhoneAlarmScreenshot
  -only-testing:RandomTimerUITests/RandomTimerUITests/testCaptureAppStorePhoneRunningScreenshot
)

IPAD_CAPTURE_TESTS=(
  -only-testing:RandomTimerUITests/RandomTimerUITests/testCaptureAppStorePadSetupScreenshot
  -only-testing:RandomTimerUITests/RandomTimerUITests/testCaptureAppStorePadRunningScreenshot
  -only-testing:RandomTimerUITests/RandomTimerUITests/testCaptureAppStorePadStoppedScreenshot
)

echo "==> Building once for UI-test capture"
xcodebuild build-for-testing \
  -project native-ios/RandomTimer.xcodeproj \
  -scheme RandomTimer \
  -destination "platform=iOS Simulator,id=$IPHONE_UDID" \
  CODE_SIGNING_ALLOWED=NO

run_capture "platform=iOS Simulator,id=$IPHONE_UDID" "${IPHONE_CAPTURE_TESTS[@]}"
run_capture "platform=iOS Simulator,id=$IPAD_UDID" "${IPAD_CAPTURE_TESTS[@]}"

cp "$TMP_OUT_DIR"/*.png "$OUT_DIR"/

REPORT_PATH="$OUT_DIR/agent-device-dimensions.txt"
: >"$REPORT_PATH"
for shot in "$OUT_DIR"/*.png; do
  w="$(/usr/bin/sips -g pixelWidth "$shot" 2>/dev/null | awk -F': ' '/pixelWidth/{print $2}')"
  h="$(/usr/bin/sips -g pixelHeight "$shot" 2>/dev/null | awk -F': ' '/pixelHeight/{print $2}')"
  printf "%s\t%sx%s\n" "$(basename "$shot")" "${w:-?}" "${h:-?}" | tee -a "$REPORT_PATH"
done
