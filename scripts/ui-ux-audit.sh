#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_SCREEN="$ROOT_DIR/native-android/app/src/main/java/com/iganapolsky/randomtimer/ui/screens/TimerSetupScreen.kt"
WITH_LINT=0
HAS_RG=0
if command -v rg >/dev/null 2>&1; then
  HAS_RG=1
fi

for arg in "$@"; do
  case "$arg" in
    --with-lint)
      WITH_LINT=1
      ;;
    --staged|--ci)
      # Mode flags are accepted for future expansion; checks are currently the same.
      ;;
    *)
      echo "Unknown argument: $arg"
      exit 1
      ;;
  esac
done

ERRORS=0

fail() {
  echo "❌ $1"
  ERRORS=$((ERRORS + 1))
}

pass() {
  echo "✅ $1"
}

pattern_exists() {
  local pattern="$1"
  local path="$2"
  if [[ "$HAS_RG" -eq 1 ]]; then
    rg -q "$pattern" "$path"
  else
    grep -Eq "$pattern" "$path"
  fi
}

pattern_count() {
  local pattern="$1"
  local path="$2"
  if [[ "$HAS_RG" -eq 1 ]]; then
    rg -n "$pattern" "$path" | wc -l | tr -d ' '
  else
    grep -En "$pattern" "$path" | wc -l | tr -d ' '
  fi
}

extract_nudge_size() {
  local path="$1"
  if [[ "$HAS_RG" -eq 1 ]]; then
    rg -N -o 'val nudgeSize = [0-9]+\.dp' "$path" | head -n1 | rg -o '[0-9]+' | head -n1
  else
    grep -Eo 'val nudgeSize = [0-9]+\.dp' "$path" | head -n1 | grep -Eo '[0-9]+' | head -n1
  fi
}

if [[ ! -f "$TARGET_SCREEN" ]]; then
  fail "Missing expected file: $TARGET_SCREEN"
fi

if [[ $ERRORS -eq 0 ]]; then
  if ! pattern_exists "private enum class NudgeType" "$TARGET_SCREEN"; then
    fail "Nudge button contract missing enum-backed icon type."
  else
    pass "Nudge type enum found."
  fi

  decrement_count="$(pattern_count "type = NudgeType.Decrement" "$TARGET_SCREEN")"
  increment_count="$(pattern_count "type = NudgeType.Increment" "$TARGET_SCREEN")"
  if [[ "${decrement_count:-0}" -lt 3 ]]; then
    fail "Expected at least 3 decrement nudge controls (min/max/volume); found $decrement_count."
  else
    pass "Decrement nudge controls present ($decrement_count)."
  fi
  if [[ "${increment_count:-0}" -lt 3 ]]; then
    fail "Expected at least 3 increment nudge controls (min/max/volume); found $increment_count."
  else
    pass "Increment nudge controls present ($increment_count)."
  fi

  if pattern_exists "label = \"\\+\"|label = \"−\"|label = \"\\\\u2212\"" "$TARGET_SCREEN"; then
    fail "Text glyph +/- controls detected; icon/drawn nudge controls required."
  else
    pass "No text-glyph +/- nudge controls detected."
  fi

  if ! pattern_exists "modifier = modifier.size\\(width = width, height = height\\)" "$TARGET_SCREEN"; then
    fail "NudgeButton must explicitly honor both width and height."
  else
    pass "NudgeButton size contract found."
  fi

  nudge_size="$(extract_nudge_size "$TARGET_SCREEN")"
  if [[ -z "${nudge_size:-}" ]]; then
    fail "Could not resolve timer nudge button size."
  elif [[ "$nudge_size" -lt 36 ]]; then
    fail "Timer nudge buttons below minimum size: ${nudge_size}dp (minimum is 36dp)."
  else
    pass "Timer nudge size is ${nudge_size}dp."
  fi

  volume_block="$(awk '/private fun VolumeSlider\(/,/^}/' "$TARGET_SCREEN")"
  if ! grep -q "contentDescription = \"Decrease volume\"" <<< "$volume_block"; then
    fail "Volume control is missing explicit decrease button."
  else
    pass "Volume decrease button present."
  fi
  if ! grep -q "contentDescription = \"Increase volume\"" <<< "$volume_block"; then
    fail "Volume control is missing explicit increase button."
  else
    pass "Volume increase button present."
  fi

  nudge_block="$(awk '/private fun NudgeButton\(/,/^}/' "$TARGET_SCREEN")"
  if grep -q "TimerColors.BackgroundDark" <<< "$nudge_block"; then
    fail "NudgeButton disabled state uses hard dark fill; use glass style for visual consistency."
  else
    pass "NudgeButton disabled style uses glass-consistent fill."
  fi
fi

if [[ "$WITH_LINT" -eq 1 ]]; then
  echo "Running Android lint UI/UX checks..."
  DUMMY_CREATED=0
  GOOGLE_SERVICES_PATH="$ROOT_DIR/native-android/app/google-services.json"
  if [[ ! -f "$GOOGLE_SERVICES_PATH" ]]; then
    cat > "$GOOGLE_SERVICES_PATH" <<'GSEOF'
{
  "project_info": { "project_number": "000000000000", "project_id": "random-timer-ci", "storage_bucket": "random-timer-ci.appspot.com" },
  "client": [{ "client_info": { "mobilesdk_app_id": "1:000000000000:android:0000000000000000", "android_client_info": { "package_name": "com.iganapolsky.randomtimer" } }, "api_key": [{ "current_key": "CI_PLACEHOLDER" }] }],
  "configuration_version": "1"
}
GSEOF
    DUMMY_CREATED=1
  fi

  set +e
  (
    cd "$ROOT_DIR/native-android"
    ./gradlew lintDebug --no-daemon
  )
  LINT_EXIT=$?
  set -e

  if [[ "$DUMMY_CREATED" -eq 1 ]]; then
    rm -f "$GOOGLE_SERVICES_PATH"
  fi

  if [[ "$LINT_EXIT" -ne 0 ]]; then
    fail "Android lintDebug failed."
  else
    pass "Android lintDebug passed."
  fi
fi

if [[ "$ERRORS" -gt 0 ]]; then
  echo "UI/UX audit failed with $ERRORS error(s)."
  exit 1
fi

echo "UI/UX audit passed."
