#!/usr/bin/env bash
# run-ios-simulator.sh — iOS simulator E2E.
#
# Default: XCUITest (local Xcode). Use --maestro for Maestro flows (CI parity).
#
# Usage:
#   ./scripts/device-tests/run-ios-simulator.sh [--maestro] [--udid <SIM_UDID>] [--skip-build] [--smoke-only]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

USE_MAESTRO=false
PASS_ARGS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --maestro)
      USE_MAESTRO=true
      shift
      ;;
    *)
      PASS_ARGS+=("$1")
      shift
      ;;
  esac
done

if [ "$USE_MAESTRO" = true ]; then
  exec bash "$SCRIPT_DIR/run-ios-maestro.sh" "${PASS_ARGS[@]}"
fi

exec bash "$SCRIPT_DIR/run-ios-xctest.sh"
