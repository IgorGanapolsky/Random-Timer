#!/usr/bin/env bash
# ai-mobile-guardrails.sh
# Enforces high-ROI AI/mobile guardrails inspired by Callstack agent best practices.
set -euo pipefail

MODE="ci"
ERRORS=0

pass() { echo "✅ $1"; }
fail() { echo "❌ $1"; ERRORS=$((ERRORS + 1)); }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --staged)
      MODE="staged"
      shift
      ;;
    --ci)
      MODE="ci"
      shift
      ;;
    *)
      echo "Unknown arg: $1"
      echo "Usage: $0 [--staged|--ci]"
      exit 2
      ;;
  esac
done

if [[ "$MODE" == "staged" ]]; then
  STAGED="$(git diff --cached --name-only --diff-filter=ACM || true)"
  if [[ -z "${STAGED:-}" ]]; then
    echo "No staged files found. Skipping AI mobile guardrails."
    exit 0
  fi
  if ! echo "$STAGED" | rg -q '^(native-android/|native-ios/|\.github/workflows/|scripts/|\.maestro/|docs/AI_AGENT_MOBILE_BEST_PRACTICES\.md)'; then
    echo "No staged mobile/guardrail files changed. Skipping AI mobile guardrails."
    exit 0
  fi
fi

require_file() {
  local path="$1"
  local label="$2"
  if [[ -f "$path" ]]; then
    pass "$label"
  else
    fail "$label missing: $path"
  fi
}

require_pattern() {
  local path="$1"
  local pattern="$2"
  local label="$3"
  if [[ ! -f "$path" ]]; then
    fail "$label (file missing: $path)"
    return
  fi
  if rg -q "$pattern" "$path"; then
    pass "$label"
  else
    fail "$label"
  fi
}

echo "Running AI mobile guardrails (${MODE})..."

# 1) Cross-platform E2E assets must exist.
require_file ".maestro/ci-smoke-test.yaml" "Android CI smoke Maestro flow exists"
require_file ".maestro/ios-smoke-test.yaml" "iOS smoke Maestro flow exists"
require_file ".maestro/alarm-circle-tap-android.yaml" "Android alarm interaction flow exists"
require_file ".maestro/alarm-circle-tap-ios.yaml" "iOS alarm interaction flow exists"
require_file "scripts/device-tests/ci-maestro.sh" "Android CI Maestro runner exists"

# 2) Core parity tests must exist.
require_file "native-android/app/src/test/java/com/iganapolsky/randomtimer/ui/components/CircularTimerTest.kt" "Android circular timer parity tests exist"
require_file "native-ios/RandomTimerTests/CircularTimerViewTests.swift" "iOS circular timer parity tests exist"
require_file "native-android/app/src/test/java/com/iganapolsky/randomtimer/billing/ProManagerDebugUnlockGuardTest.kt" "Android debug/release unlock guard test exists"

# 3) Volume explicit controls and accessibility must exist on both platforms.
ANDROID_TIMER_SETUP="native-android/app/src/main/java/com/iganapolsky/randomtimer/ui/screens/TimerSetupScreen.kt"
IOS_TIMER_SETUP="native-ios/RandomTimer/Sources/UI/Screens/TimerSetupScreen.swift"
require_pattern "$ANDROID_TIMER_SETUP" 'contentDescription = "Decrease volume"' "Android explicit volume decrement control"
require_pattern "$ANDROID_TIMER_SETUP" 'contentDescription = "Increase volume"' "Android explicit volume increment control"
require_pattern "$IOS_TIMER_SETUP" 'accessibilityLabel: "Decrease volume"' "iOS explicit volume decrement control"
require_pattern "$IOS_TIMER_SETUP" 'accessibilityLabel: "Increase volume"' "iOS explicit volume increment control"

# 4) Guardrails must be wired into pre-commit and CI.
require_pattern "scripts/pre-commit" 'scripts/ui-ux-audit\.sh --staged --with-lint' "Pre-commit enforces Android UI/UX audit"
require_pattern "scripts/pre-commit" 'scripts/ai-mobile-guardrails\.sh --staged' "Pre-commit enforces AI mobile guardrails"
require_pattern ".github/workflows/ci.yml" 'scripts/ui-ux-audit\.sh --ci --with-lint' "CI enforces Android UI/UX audit"
require_pattern ".github/workflows/ci.yml" 'scripts/ai-mobile-guardrails\.sh --ci' "CI enforces AI mobile guardrails"
require_pattern ".github/workflows/device-tests.yml" 'ci-maestro\.sh' "Device-tests workflow executes Maestro suite"

# 5) Team playbook document must exist.
require_file "docs/AI_AGENT_MOBILE_BEST_PRACTICES.md" "AI mobile best-practices playbook exists"
require_pattern "docs/AI_AGENT_MOBILE_BEST_PRACTICES.md" '^## High-ROI Controls' "Playbook includes High-ROI controls"
require_pattern "docs/AI_AGENT_MOBILE_BEST_PRACTICES.md" '^## Enforcement Matrix' "Playbook includes enforcement matrix"

if [[ "$ERRORS" -gt 0 ]]; then
  echo "AI mobile guardrails failed with $ERRORS error(s)."
  exit 1
fi

echo "AI mobile guardrails passed."

