#!/usr/bin/env bash
# apk-size.sh — Builds the debug APK and reports its size in MB.
# Compares against baseline if one exists, showing delta.
# Saves baseline to scripts/benchmarks/baselines/apk-size.json
# Usage: ./scripts/benchmarks/apk-size.sh [--save-baseline] [--no-build]
#   --no-build: skip rebuild, just measure the existing APK (faster for CI)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
ANDROID_DIR="${PROJECT_ROOT}/native-android"
BASELINES_DIR="${SCRIPT_DIR}/baselines"
BASELINE_FILE="${BASELINES_DIR}/apk-size.json"

APK_PATH="${ANDROID_DIR}/app/build/outputs/apk/debug/app-debug.apk"

SAVE_BASELINE=false
SKIP_BUILD=false
for arg in "$@"; do
  case "$arg" in
    --save-baseline) SAVE_BASELINE=true ;;
    --no-build)      SKIP_BUILD=true ;;
  esac
done

# ── Helpers ────────────────────────────────────────────────────────────────────

separator() {
  printf '%0.s─' {1..60}
  printf '\n'
}

bytes_to_mb() {
  python3 -c "print(f'{$1 / 1048576:.2f}')"
}

# ── Preflight ──────────────────────────────────────────────────────────────────

if [[ ! -f "${ANDROID_DIR}/gradlew" ]]; then
  echo "ERROR: gradlew not found at ${ANDROID_DIR}/gradlew" >&2
  exit 1
fi

echo ""
echo "APK Size Benchmark"
separator

# ── Build ──────────────────────────────────────────────────────────────────────

if [[ "${SKIP_BUILD}" == "false" ]]; then
  echo "Building debug APK (./gradlew assembleDebug)..."
  echo ""
  cd "${ANDROID_DIR}"
  ./gradlew assembleDebug --no-daemon --quiet 2>&1 | tail -5
  echo ""
else
  echo "Skipping build (--no-build specified)."
  echo ""
fi

# ── Measure APK ───────────────────────────────────────────────────────────────

if [[ ! -f "${APK_PATH}" ]]; then
  echo "ERROR: APK not found at ${APK_PATH}" >&2
  echo "  Run without --no-build to trigger a build first." >&2
  exit 1
fi

APK_BYTES=$(stat -f%z "${APK_PATH}" 2>/dev/null || stat -c%s "${APK_PATH}")
APK_MB=$(bytes_to_mb "${APK_BYTES}")
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

echo "APK: ${APK_PATH}"
echo ""
printf "%-35s %10s\n" "Metric" "Value"
separator
printf "%-35s %9s MB\n" "APK size" "${APK_MB}"
printf "%-35s %10s\n"   "APK size (bytes)" "${APK_BYTES}"
separator
echo ""

# ── Baseline comparison ────────────────────────────────────────────────────────

REGRESSION=false

if [[ -f "${BASELINE_FILE}" ]]; then
  BASELINE_MB=$(python3 -c "import json; d=json.load(open('${BASELINE_FILE}')); print(d['apk_size_mb'])")
  BASELINE_BYTES=$(python3 -c "import json; d=json.load(open('${BASELINE_FILE}')); print(d['apk_size_bytes'])")
  BASELINE_TS=$(python3 -c "import json; d=json.load(open('${BASELINE_FILE}')); print(d['timestamp'])")

  DELTA_MB=$(python3 -c "print(f'{${APK_MB} - ${BASELINE_MB}:+.2f}')")
  DELTA_BYTES=$((APK_BYTES - BASELINE_BYTES))
  PCT_CHANGE=$(python3 -c "print(f'{(${APK_MB} - ${BASELINE_MB}) / ${BASELINE_MB} * 100:+.1f}')")

  echo "Comparison against baseline (recorded ${BASELINE_TS}):"
  printf "%-35s %10s MB\n" "Baseline APK size" "${BASELINE_MB}"
  printf "%-35s %+9s MB\n" "Delta" "${DELTA_MB}"
  printf "%-35s %9s%%\n"   "Change" "${PCT_CHANGE}"
  separator
  echo ""

  # Regression check: >10% larger than baseline
  IS_REGRESSION=$(python3 -c "
baseline=${BASELINE_MB}
current=${APK_MB}
pct = (current - baseline) / baseline * 100
print('yes' if pct > 10 else 'no')
")
  if [[ "${IS_REGRESSION}" == "yes" ]]; then
    echo "REGRESSION: APK size increased by more than 10% vs baseline (${PCT_CHANGE}%)" >&2
    REGRESSION=true
  fi
fi

# ── Save baseline ──────────────────────────────────────────────────────────────

if [[ "${SAVE_BASELINE}" == "true" ]] || [[ ! -f "${BASELINE_FILE}" ]]; then
  mkdir -p "${BASELINES_DIR}"
  python3 - <<PYEOF
import json
data = {
    "timestamp": "${TIMESTAMP}",
    "apk_size_mb": float("${APK_MB}"),
    "apk_size_bytes": int("${APK_BYTES}")
}
with open("${BASELINE_FILE}", "w") as f:
    json.dump(data, f, indent=2)
label = "Baseline saved" if "${SAVE_BASELINE}" == "true" else "No baseline existed — auto-saved initial baseline"
print(f"{label} to ${BASELINE_FILE}")
PYEOF
fi

if [[ "${REGRESSION}" == "true" ]]; then
  exit 1
fi
