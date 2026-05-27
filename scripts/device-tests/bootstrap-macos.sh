#!/usr/bin/env bash
# bootstrap-macos.sh — Fix common local mobile E2E toolchain gaps on Apple Silicon macOS.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ANDROID_DIR="$REPO_ROOT/native-android"
DAEMON_JVM_PROPS="$ANDROID_DIR/gradle/gradle-daemon-jvm.properties"

echo "== Random Timer: mobile E2E bootstrap (macOS) =="

if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew is required. Install from https://brew.sh and re-run." >&2
  exit 2
fi

echo "→ JDK 21 (Gradle / jlink)"
brew list openjdk@21 >/dev/null 2>&1 || brew install openjdk@21

echo "→ JDK (Maestro CLI)"
brew list openjdk >/dev/null 2>&1 || brew install openjdk

if [ -f "$DAEMON_JVM_PROPS" ]; then
  echo "→ Removing local gradle-daemon-jvm.properties (JetBrains 21 pin breaks macOS arm64 auto-download)"
  rm -f "$DAEMON_JVM_PROPS"
fi

if ! command -v maestro >/dev/null 2>&1; then
  echo "→ Maestro CLI"
  curl -Ls "https://get.maestro.mobile.dev" | bash
fi
export PATH="$HOME/.maestro/bin:$PATH"

if ! command -v idb_companion >/dev/null 2>&1; then
  echo "→ idb-companion (optional; for Maestro+iOS when XCTest is not used)"
  brew install facebook/fb/idb-companion || true
fi

# shellcheck source=lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"
export DEVICE_TESTS_REPO_ROOT="$REPO_ROOT"
ensure_android_java
require_java

echo ""
echo "Toolchain:"
java -version 2>&1 | head -1
maestro --version 2>&1 | head -1 || echo "Maestro: not on PATH (add ~/.maestro/bin)"
command -v adb >/dev/null && adb devices || echo "adb: no devices"
xcodebuild -version 2>&1 | head -1 || echo "xcodebuild: not found"

echo ""
echo "Bootstrap complete. Next:"
echo "  ./scripts/device-tests/run-all.sh          # Android device"
echo "  ./scripts/device-tests/run-ios-xctest.sh # iOS simulator (recommended locally)"
