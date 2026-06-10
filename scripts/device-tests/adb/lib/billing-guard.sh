#!/usr/bin/env bash
# billing-guard.sh — Block device billing automation unless explicitly opted in.
#
# Production Play IAP on a retail account charges real money unless the Google
# account is on Play Console → Settings → License testing. Device scripts that
# can reach the paywall purchase sheet MUST call assert_play_billing_test_safe
# before any purchase-adjacent UI (Subscribe / Start Annual / etc.).
#
# Opt-in paths (either is sufficient):
#   1. PLAY_BILLING_TEST_MODE=1  — operator acknowledges license-tester setup
#   2. Device primary account email matches PLAY_LICENSE_TESTER_EMAILS (comma-separated)

assert_play_billing_test_safe() {
  local mode="${PLAY_BILLING_TEST_MODE:-}"
  local mode_lower
  mode_lower="$(printf '%s' "$mode" | tr '[:upper:]' '[:lower:]')"
  if [ "$mode" = "1" ] || [ "$mode_lower" = "true" ] || [ "$mode_lower" = "yes" ]; then
    echo "billing-guard: PLAY_BILLING_TEST_MODE enabled"
    return 0
  fi

  local allowlist="${PLAY_LICENSE_TESTER_EMAILS:-iganapolsky@gmail.com}"
  local device_email
  device_email="$(adb shell dumpsys account 2>/dev/null | tr -d '\r' | grep -E 'type=com\.google' -A2 | grep 'name=' | head -1 | sed -E 's/.*name=([^,} ]+).*/\1/' || true)"

  if [ -n "$device_email" ]; then
    local normalized
    normalized="$(printf '%s' "$device_email" | tr '[:upper:]' '[:lower:]')"
    IFS=',' read -ra emails <<< "$allowlist"
    for raw in "${emails[@]}"; do
      local candidate
      candidate="$(printf '%s' "$raw" | tr -d '[:space:]' | tr '[:upper:]' '[:lower:]')"
      [ -n "$candidate" ] || continue
      if [ "$normalized" = "$candidate" ]; then
        echo "billing-guard: device account $device_email matches license tester allowlist"
        return 0
      fi
    done
    echo "billing-guard: ABORT — device account '$device_email' not in PLAY_LICENSE_TESTER_EMAILS." >&2
  else
    echo "billing-guard: ABORT — could not read device Google account; set PLAY_BILLING_TEST_MODE=1 after adding account to License testing." >&2
  fi

  echo "billing-guard: Retail Play IAP without license tester charges real money (see docs/PLAY_TESTING_TRACKS.md)." >&2
  echo "billing-guard: Add the account under Play Console → Settings → License testing, then re-run with PLAY_BILLING_TEST_MODE=1." >&2
  return 3
}
