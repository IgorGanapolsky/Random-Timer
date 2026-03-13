#!/usr/bin/env bash
# android-build-time.sh — Measures clean and incremental Android debug build times.
# Saves baseline to scripts/benchmarks/baselines/android-build.json
# Usage: ./scripts/benchmarks/android-build-time.sh [--save-baseline]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
ANDROID_DIR="${PROJECT_ROOT}/native-android"
BASELINES_DIR="${SCRIPT_DIR}/baselines"
BASELINE_FILE="${BASELINES_DIR}/android-build.json"

SAVE_BASELINE=false
if [[ "${1:-}" == "--save-baseline" ]]; then
  SAVE_BASELINE=true
fi

# ── Helpers ────────────────────────────────────────────────────────────────────

epoch_ms() {
  # Portable: works on macOS (no %N) and Linux
  python3 -c "import time; print(int(time.time() * 1000))"
}

seconds_between() {
  local start_ms="$1"
  local end_ms="$2"
  echo "scale=2; ($end_ms - $start_ms) / 1000" | bc
}

separator() {
  printf '%0.s─' {1..60}
  printf '\n'
}

# ── Preflight ──────────────────────────────────────────────────────────────────

if [[ ! -f "${ANDROID_DIR}/gradlew" ]]; then
  echo "ERROR: gradlew not found at ${ANDROID_DIR}/gradlew" >&2
  exit 1
fi

cd "${ANDROID_DIR}"

echo ""
echo "Android Build Time Benchmark"
separator

# ── Clean build ────────────────────────────────────────────────────────────────

echo "Step 1/3: Clean build (./gradlew clean assembleDebug)"
echo ""

CLEAN_START=$(epoch_ms)
./gradlew clean assembleDebug --no-daemon --quiet 2>&1 | tail -5
CLEAN_END=$(epoch_ms)
CLEAN_SECONDS=$(seconds_between "$CLEAN_START" "$CLEAN_END")

echo ""
echo "  Clean build time: ${CLEAN_SECONDS}s"
separator

# ── First incremental build (no changes) ──────────────────────────────────────

echo "Step 2/3: Incremental build #1 (assembleDebug, no changes)"
echo ""

INC1_START=$(epoch_ms)
./gradlew assembleDebug --no-daemon --quiet 2>&1 | tail -3
INC1_END=$(epoch_ms)
INC1_SECONDS=$(seconds_between "$INC1_START" "$INC1_END")

echo ""
echo "  Incremental build #1 time: ${INC1_SECONDS}s"
separator

# ── Second incremental build (fully cached) ────────────────────────────────────

echo "Step 3/3: Incremental build #2 (assembleDebug, fully cached)"
echo ""

INC2_START=$(epoch_ms)
./gradlew assembleDebug --no-daemon --quiet 2>&1 | tail -3
INC2_END=$(epoch_ms)
INC2_SECONDS=$(seconds_between "$INC2_START" "$INC2_END")

echo ""
echo "  Incremental build #2 time: ${INC2_SECONDS}s"
separator

# ── Summary ────────────────────────────────────────────────────────────────────

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

echo ""
printf "%-35s %10s\n" "Metric" "Value"
separator
printf "%-35s %9ss\n" "Clean build time" "${CLEAN_SECONDS}"
printf "%-35s %9ss\n" "Incremental build #1 (no-op)" "${INC1_SECONDS}"
printf "%-35s %9ss\n" "Incremental build #2 (cached)" "${INC2_SECONDS}"
separator
echo ""

# ── Baseline comparison ────────────────────────────────────────────────────────

if [[ -f "${BASELINE_FILE}" ]]; then
  BASELINE_CLEAN=$(python3 -c "import json,sys; d=json.load(open('${BASELINE_FILE}')); print(d['clean_build_seconds'])")
  BASELINE_INC=$(python3 -c "import json,sys; d=json.load(open('${BASELINE_FILE}')); print(d['incremental_build_seconds'])")

  CLEAN_DELTA=$(echo "scale=2; ${CLEAN_SECONDS} - ${BASELINE_CLEAN}" | bc)
  INC_DELTA=$(echo "scale=2; ${INC1_SECONDS} - ${BASELINE_INC}" | bc)

  echo "Comparison against baseline (${BASELINE_FILE}):"
  printf "%-35s %+10ss\n" "Clean build delta" "${CLEAN_DELTA}"
  printf "%-35s %+10ss\n" "Incremental build delta" "${INC_DELTA}"
  separator
  echo ""
fi

# ── Save baseline ──────────────────────────────────────────────────────────────

if [[ "${SAVE_BASELINE}" == "true" ]]; then
  mkdir -p "${BASELINES_DIR}"
  python3 - <<PYEOF
import json, os
data = {
    "timestamp": "${TIMESTAMP}",
    "clean_build_seconds": float("${CLEAN_SECONDS}"),
    "incremental_build_seconds": float("${INC1_SECONDS}"),
    "incremental_cached_seconds": float("${INC2_SECONDS}")
}
with open("${BASELINE_FILE}", "w") as f:
    json.dump(data, f, indent=2)
print("Baseline saved to ${BASELINE_FILE}")
PYEOF
elif [[ ! -f "${BASELINE_FILE}" ]]; then
  # Auto-save on first run (no existing baseline)
  mkdir -p "${BASELINES_DIR}"
  python3 - <<PYEOF
import json
data = {
    "timestamp": "${TIMESTAMP}",
    "clean_build_seconds": float("${CLEAN_SECONDS}"),
    "incremental_build_seconds": float("${INC1_SECONDS}"),
    "incremental_cached_seconds": float("${INC2_SECONDS}")
}
with open("${BASELINE_FILE}", "w") as f:
    json.dump(data, f, indent=2)
print("No baseline existed — auto-saved initial baseline to ${BASELINE_FILE}")
PYEOF
fi
