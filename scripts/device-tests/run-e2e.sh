#!/usr/bin/env bash
# run-e2e.sh — Run Android (connected device) + iOS (simulator) E2E suites.
#
# Usage:
#   ./scripts/device-tests/run-e2e.sh [--skip-android-install] [--ios-udid <SIM_UDID>] [--ios-smoke-only]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export DEVICE_TESTS_REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

SKIP_ANDROID_INSTALL=false
IOS_UDID=""
IOS_SMOKE_ONLY=false

while [ $# -gt 0 ]; do
  case "$1" in
    --skip-android-install)
      SKIP_ANDROID_INSTALL=true
      shift
      ;;
    --ios-udid)
      IOS_UDID="${2:-}"
      shift 2
      ;;
    --ios-smoke-only)
      IOS_SMOKE_ONLY=true
      shift
      ;;
    --help|-h)
      echo "Usage: $0 [--skip-android-install] [--ios-udid <SIM_UDID>] [--ios-smoke-only]"
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

ANDROID_ARGS=()
if [ "$SKIP_ANDROID_INSTALL" = true ]; then
  ANDROID_ARGS+=(--skip-install)
fi

echo "=== Android E2E ==="
bash "$SCRIPT_DIR/run-all.sh" "${ANDROID_ARGS[@]}"

echo ""
echo "=== iOS Simulator E2E ==="
IOS_ARGS=()
if [ -n "$IOS_UDID" ]; then
  IOS_ARGS+=(--udid "$IOS_UDID")
fi
if [ "$IOS_SMOKE_ONLY" = true ]; then
  IOS_ARGS+=(--smoke-only)
fi
bash "$SCRIPT_DIR/run-ios-simulator.sh" "${IOS_ARGS[@]}"

