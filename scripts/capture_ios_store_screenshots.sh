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

RUNTIME_ID="${IOS_RUNTIME_ID:-com.apple.CoreSimulator.SimRuntime.iOS-26-4}"
IPHONE_TYPE="com.apple.CoreSimulator.SimDeviceType.iPhone-16-Pro-Max"
IPAD_TYPE="com.apple.CoreSimulator.SimDeviceType.iPad-Pro-13-inch-M4-8GB"
IPHONE_NAME="RandomTimer AppStore iPhone 16 Pro Max"
IPAD_NAME="RandomTimer AppStore iPad Pro 13 M4"

ensure_sim() {
  local name="$1"
  local type="$2"
  if ! xcrun simctl list devices available | grep -q "$name"; then
    xcrun simctl create "$name" "$type" "$RUNTIME_ID" >/dev/null
  fi
}

ensure_sim "$IPHONE_NAME" "$IPHONE_TYPE"
ensure_sim "$IPAD_NAME" "$IPAD_TYPE"

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
  xcodebuild test-without-building \
    -project native-ios/RandomTimer.xcodeproj \
    -scheme RandomTimer \
    -destination "$destination" \
    -only-testing:RandomTimerUITests/RandomTimerUITests/testCaptureAppStoreScreenshots \
    CODE_SIGNING_ALLOWED=NO
}

echo "==> Building once for UI-test capture"
xcodebuild build-for-testing \
  -project native-ios/RandomTimer.xcodeproj \
  -scheme RandomTimer \
  -destination "platform=iOS Simulator,name=$IPHONE_NAME" \
  CODE_SIGNING_ALLOWED=NO

run_capture "platform=iOS Simulator,name=$IPHONE_NAME"
run_capture "platform=iOS Simulator,name=$IPAD_NAME"

cp "$TMP_OUT_DIR"/*.png "$OUT_DIR"/

REPORT_PATH="$OUT_DIR/agent-device-dimensions.txt"
: >"$REPORT_PATH"
for shot in "$OUT_DIR"/*.png; do
  w="$(/usr/bin/sips -g pixelWidth "$shot" 2>/dev/null | awk -F': ' '/pixelWidth/{print $2}')"
  h="$(/usr/bin/sips -g pixelHeight "$shot" 2>/dev/null | awk -F': ' '/pixelHeight/{print $2}')"
  printf "%s\t%sx%s\n" "$(basename "$shot")" "${w:-?}" "${h:-?}" | tee -a "$REPORT_PATH"
done
