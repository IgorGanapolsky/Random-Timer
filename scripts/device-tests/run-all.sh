#!/usr/bin/env bash
# run-all.sh — Unified device test orchestrator
# Runs ADB shell tests and Maestro flows against a connected Android device.
#
# Usage:
#   ./scripts/device-tests/run-all.sh [--skip-install] [--adb-only] [--maestro-only]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
export DEVICE_TESTS_REPO_ROOT="$PROJECT_ROOT"
# shellcheck source=lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

SKIP_INSTALL=false
ADB_ONLY=false
MAESTRO_ONLY=false

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

# Parse arguments
for arg in "$@"; do
  case $arg in
    --skip-install) SKIP_INSTALL=true ;;
    --adb-only) ADB_ONLY=true ;;
    --maestro-only)
      MAESTRO_ONLY=true
      SKIP_INSTALL=true
      ;;
    --help|-h)
      echo "Usage: $0 [--skip-install] [--adb-only] [--maestro-only]"
      echo ""
      echo "  --skip-install  Skip APK build and install"
      echo "  --adb-only      Run only ADB shell tests"
      echo "  --maestro-only  Run only Maestro flows"
      exit 0
      ;;
    *) echo "Unknown argument: $arg"; exit 2 ;;
  esac
done

echo -e "${BOLD}══════════════════════════════════════════${RESET}"
echo -e "${BOLD}  Device Tests — Random Timer${RESET}"
echo -e "${BOLD}══════════════════════════════════════════${RESET}"

# ── Phase 1: Preflight ──
echo -e "\n${CYAN}Phase 1: Preflight${RESET}"

# Check device connected
DEVICE_COUNT=$(adb devices | grep -c "device$" || true)
if [ "$DEVICE_COUNT" -eq 0 ]; then
  echo -e "${RED}No Android device/emulator connected.${RESET}"
  echo "Connect a device or start an emulator, then retry."
  exit 2
fi
echo -e "  ${GREEN}Device connected${RESET} ($DEVICE_COUNT device(s))"

# Install debug APK
if [ "$SKIP_INSTALL" = false ]; then
  echo -e "  Building and installing debug APK..."
  ensure_android_java
  disable_gradle_daemon_jvm_props
  trap restore_gradle_daemon_jvm_props EXIT
  cd "$PROJECT_ROOT/native-android" && ./gradlew --stop 2>/dev/null || true
  cd "$PROJECT_ROOT/native-android" && ./gradlew assembleDebug --no-daemon -q \
    -Dorg.gradle.java.home="$JAVA_HOME"
  APK_PATH="$PROJECT_ROOT/native-android/app/build/outputs/apk/debug/app-debug.apk"
  adb install -r -d "$APK_PATH" >/dev/null
  echo -e "  ${GREEN}APK installed${RESET} (adb install -r)"
fi

# Grant runtime permissions
adb shell pm grant com.iganapolsky.randomtimer android.permission.POST_NOTIFICATIONS 2>/dev/null || true
echo -e "  ${GREEN}Permissions granted${RESET}"

# Clean up any running timer (uninstall when debug signature changed)
adb shell am force-stop com.iganapolsky.randomtimer 2>/dev/null || true
adb uninstall com.iganapolsky.randomtimer 2>/dev/null || true
sleep 1

# ── Phase 2: ADB Tests ──
ADB_PASS=0
ADB_FAIL=0

if [ "$MAESTRO_ONLY" = false ]; then
  echo -e "\n${CYAN}Phase 2: ADB Shell Tests${RESET}"

  ADB_TESTS=(
    "test-notification.sh"
    "test-lockscreen.sh"
    "test-media-buttons.sh"
    "test-audio.sh"
    "test-cross-app.sh"
  )

  for test_file in "${ADB_TESTS[@]}"; do
    test_path="$SCRIPT_DIR/adb/$test_file"
    if [ -f "$test_path" ]; then
      echo -e "\n${BOLD}Running: $test_file${RESET}"
      if bash "$test_path"; then
        ADB_PASS=$((ADB_PASS + 1))
      else
        ADB_FAIL=$((ADB_FAIL + 1))
      fi
    else
      echo -e "  ${RED}SKIP: $test_file not found${RESET}"
    fi
  done
fi

# ── Phase 3: Maestro Tests ──
MAESTRO_PASS=0
MAESTRO_FAIL=0

if [ "$ADB_ONLY" = false ]; then
  echo -e "\n${CYAN}Phase 3: Maestro Flows${RESET}"

  if command -v maestro &>/dev/null; then
    require_java
    MAESTRO_DIR="$PROJECT_ROOT/.maestro"
    MAESTRO_FLOWS=(
      "ci-smoke-test.yaml"
      "smoke-test.yaml"
      "cross-app-return.yaml"
      "persistence-test.yaml"
      "paused-timer-background-shows-notification.yaml"
      "paused-timer-cannot-show-setup.yaml"
      "alarm-notification-stop-android.yaml"
      "activation-banner-dismiss-android.yaml"
      "activation-smoke-android.yaml"
      "activation-paywall-from-pro-tap-android.yaml"
      "regression-pro-locks-visible-android.yaml"
    )

    for flow in "${MAESTRO_FLOWS[@]}"; do
      flow_path="$MAESTRO_DIR/$flow"
      if [ -f "$flow_path" ]; then
        echo -e "\n${BOLD}Running: $flow${RESET}"
        if maestro test "$flow_path"; then
          MAESTRO_PASS=$((MAESTRO_PASS + 1))
        else
          MAESTRO_FAIL=$((MAESTRO_FAIL + 1))
        fi
      fi
    done
  else
    echo -e "  ${CYAN}Maestro CLI not found — skipping Maestro flows${RESET}"
  fi
fi

# ── Phase 4: Summary ──
TOTAL_PASS=$((ADB_PASS + MAESTRO_PASS))
TOTAL_FAIL=$((ADB_FAIL + MAESTRO_FAIL))

echo ""
echo -e "${BOLD}══════════════════════════════════════════${RESET}"
echo -e "${BOLD}  Summary${RESET}"
echo -e "${BOLD}──────────────────────────────────────────${RESET}"
if [ "$MAESTRO_ONLY" = false ]; then
  echo -e "  ADB tests:     ${GREEN}$ADB_PASS passed${RESET}, ${RED}$ADB_FAIL failed${RESET}"
fi
if [ "$ADB_ONLY" = false ]; then
  echo -e "  Maestro flows:  ${GREEN}$MAESTRO_PASS passed${RESET}, ${RED}$MAESTRO_FAIL failed${RESET}"
fi
echo -e "${BOLD}──────────────────────────────────────────${RESET}"

if [ "$TOTAL_FAIL" -gt 0 ]; then
  echo -e "  ${RED}RESULT: $TOTAL_FAIL test suite(s) failed${RESET}"
  echo -e "${BOLD}══════════════════════════════════════════${RESET}"
  exit 1
else
  echo -e "  ${GREEN}RESULT: ALL PASSED${RESET}"
  echo -e "${BOLD}══════════════════════════════════════════${RESET}"
  exit 0
fi
