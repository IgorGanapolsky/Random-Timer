# shellcheck shell=bash
# Shared helpers for local device E2E runners.

if [[ -z "${DEVICE_TESTS_REPO_ROOT:-}" ]]; then
  _device_tests_lib_dir=""
  if [[ -n "${BASH_SOURCE[0]:-}" ]]; then
    _device_tests_lib_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  fi
  if [[ -z "$_device_tests_lib_dir" ]] && command -v git >/dev/null 2>&1; then
    DEVICE_TESTS_REPO_ROOT="$(git -C "${PWD}" rev-parse --show-toplevel 2>/dev/null || true)"
  elif [[ -n "$_device_tests_lib_dir" ]]; then
    DEVICE_TESTS_REPO_ROOT="$(cd "$_device_tests_lib_dir/../../.." && pwd)"
  fi
fi

ensure_java() {
  if command -v brew >/dev/null 2>&1 && brew --prefix openjdk >/dev/null 2>&1; then
    export JAVA_HOME="$(brew --prefix openjdk)/libexec/openjdk.jdk/Contents/Home"
    export PATH="$JAVA_HOME/bin:$PATH"
  fi
}

require_java() {
  ensure_java
  if ! java -version >/dev/null 2>&1; then
    echo "Java runtime not found (required for Maestro). Install: brew install openjdk" >&2
    exit 2
  fi
}

require_maestro() {
  if ! command -v maestro >/dev/null 2>&1; then
    echo "Maestro CLI not found. Install from https://maestro.mobile.dev/ and retry." >&2
    exit 2
  fi
  require_java
  export MAESTRO_DISABLE_ANALYTICS="${MAESTRO_DISABLE_ANALYTICS:-true}"
  export MAESTRO_DRIVER_STARTUP_TIMEOUT="${MAESTRO_DRIVER_STARTUP_TIMEOUT:-300000}"
}

# Gradle 9.4 + gradle-daemon-jvm.properties (JetBrains 21) cannot auto-download on
# macOS aarch64. Local device tests use JDK 21 with jlink (Homebrew) and temporarily
# disable the generated daemon JVM pin file.
ensure_android_java() {
  local repo_root="${DEVICE_TESTS_REPO_ROOT:-}"
  if [ -n "$repo_root" ]; then
    local daemon_props="$repo_root/native-android/gradle/gradle-daemon-jvm.properties"
    if [ -f "$daemon_props" ] && [ "$(uname -s)" = "Darwin" ] && [ "$(uname -m)" = "arm64" ]; then
      rm -f "$daemon_props"
    fi
  fi
  if command -v brew >/dev/null 2>&1 && brew --prefix openjdk@21 >/dev/null 2>&1; then
    export JAVA_HOME="$(brew --prefix openjdk@21)/libexec/openjdk.jdk/Contents/Home"
    export PATH="$JAVA_HOME/bin:$PATH"
  fi
  if ! java -version >/dev/null 2>&1; then
    echo "JDK 21 required for Android builds. Install: brew install openjdk@21" >&2
    exit 2
  fi
  if [ ! -x "$JAVA_HOME/bin/jlink" ]; then
    echo "JDK 21 with jlink is required (brew install openjdk@21)." >&2
    exit 2
  fi
}

disable_gradle_daemon_jvm_props() {
  local repo_root="${DEVICE_TESTS_REPO_ROOT:?DEVICE_TESTS_REPO_ROOT not set}"
  local props="$repo_root/native-android/gradle/gradle-daemon-jvm.properties"
  if [ -f "$props" ] && [ ! -f "${props}.device-tests-bak" ]; then
    mv "$props" "${props}.device-tests-bak"
  fi
}

restore_gradle_daemon_jvm_props() {
  local repo_root="${DEVICE_TESTS_REPO_ROOT:?DEVICE_TESTS_REPO_ROOT not set}"
  local props="$repo_root/native-android/gradle/gradle-daemon-jvm.properties"
  if [ -f "${props}.device-tests-bak" ]; then
    mv "${props}.device-tests-bak" "$props"
  fi
}
