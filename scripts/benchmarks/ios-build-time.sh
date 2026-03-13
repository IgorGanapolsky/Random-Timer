#!/usr/bin/env bash
# ios-build-time.sh — Measures clean and incremental iOS simulator build times.
# Saves baseline to scripts/benchmarks/baselines/ios-build.json
# Usage: ./scripts/benchmarks/ios-build-time.sh [--save-baseline]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
IOS_DIR="${PROJECT_ROOT}/native-ios"
BASELINES_DIR="${SCRIPT_DIR}/baselines"
BASELINE_FILE="${BASELINES_DIR}/ios-build.json"

SCHEME="RandomTimer"
DESTINATION="platform=iOS Simulator,name=iPhone 16 Pro Max"

SAVE_BASELINE=false
if [[ "${1:-}" == "--save-baseline" ]]; then
  SAVE_BASELINE=true
fi

# ── Helpers ────────────────────────────────────────────────────────────────────

epoch_ms() {
  python3 -c "import time; print(int(time.time() * 1000))"
}

seconds_between() {
  echo "scale=2; ($2 - $1) / 1000" | bc
}

separator() {
  printf '%0.s─' {1..60}
  printf '\n'
}

# ── Preflight ──────────────────────────────────────────────────────────────────

if ! command -v xcodebuild &>/dev/null; then
  echo "ERROR: xcodebuild not found. Install Xcode Command Line Tools." >&2
  exit 1
fi

# Locate workspace or project
WORKSPACE="${IOS_DIR}/RandomTimer.xcworkspace"
XCPROJECT="${IOS_DIR}/RandomTimer.xcodeproj"

if [[ -d "${WORKSPACE}" ]]; then
  BUILD_ARGS=(-workspace "${WORKSPACE}" -scheme "${SCHEME}")
else
  BUILD_ARGS=(-project "${XCPROJECT}" -scheme "${SCHEME}")
fi

cd "${IOS_DIR}"

echo ""
echo "iOS Build Time Benchmark"
separator
echo "Scheme: ${SCHEME}"
echo "Destination: ${DESTINATION}"
separator

# ── Clean build ────────────────────────────────────────────────────────────────

echo ""
echo "Step 1/2: Clean build (xcodebuild clean build)"
echo ""

CLEAN_START=$(epoch_ms)
xcodebuild "${BUILD_ARGS[@]}" \
  -destination "${DESTINATION}" \
  -configuration Debug \
  clean build \
  CODE_SIGN_IDENTITY="" CODE_SIGNING_REQUIRED=NO \
  2>&1 | grep -E "(Build|error:|warning:|note:)" | grep -v "^note:" | tail -10
CLEAN_STATUS=${PIPESTATUS[0]}
CLEAN_END=$(epoch_ms)
CLEAN_SECONDS=$(seconds_between "$CLEAN_START" "$CLEAN_END")

if [[ "${CLEAN_STATUS}" -ne 0 ]]; then
  echo ""
  echo "ERROR: Clean build failed (exit ${CLEAN_STATUS}). Re-running with full output:" >&2
  xcodebuild "${BUILD_ARGS[@]}" \
    -destination "${DESTINATION}" \
    -configuration Debug \
    clean build \
    CODE_SIGN_IDENTITY="" CODE_SIGNING_REQUIRED=NO 2>&1 | tail -30
  exit "${CLEAN_STATUS}"
fi

echo ""
echo "  Clean build time: ${CLEAN_SECONDS}s"
separator

# ── Incremental build (no changes) ────────────────────────────────────────────

echo ""
echo "Step 2/2: Incremental build (build only, no changes)"
echo ""

INC_START=$(epoch_ms)
xcodebuild "${BUILD_ARGS[@]}" \
  -destination "${DESTINATION}" \
  -configuration Debug \
  build \
  CODE_SIGN_IDENTITY="" CODE_SIGNING_REQUIRED=NO \
  2>&1 | grep -E "(Build|error:)" | tail -5
INC_END=$(epoch_ms)
INC_SECONDS=$(seconds_between "$INC_START" "$INC_END")

echo ""
echo "  Incremental build time: ${INC_SECONDS}s"
separator

# ── Summary ────────────────────────────────────────────────────────────────────

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

echo ""
printf "%-35s %10s\n" "Metric" "Value"
separator
printf "%-35s %9ss\n" "Clean build time" "${CLEAN_SECONDS}"
printf "%-35s %9ss\n" "Incremental build time" "${INC_SECONDS}"
separator
echo ""

# ── Baseline comparison ────────────────────────────────────────────────────────

if [[ -f "${BASELINE_FILE}" ]]; then
  BASELINE_CLEAN=$(python3 -c "import json; d=json.load(open('${BASELINE_FILE}')); print(d['clean_build_seconds'])")
  BASELINE_INC=$(python3 -c "import json; d=json.load(open('${BASELINE_FILE}')); print(d['incremental_build_seconds'])")

  CLEAN_DELTA=$(echo "scale=2; ${CLEAN_SECONDS} - ${BASELINE_CLEAN}" | bc)
  INC_DELTA=$(echo "scale=2; ${INC_SECONDS} - ${BASELINE_INC}" | bc)

  echo "Comparison against baseline (${BASELINE_FILE}):"
  printf "%-35s %+10ss\n" "Clean build delta" "${CLEAN_DELTA}"
  printf "%-35s %+10ss\n" "Incremental build delta" "${INC_DELTA}"
  separator
  echo ""
fi

# ── Save baseline ──────────────────────────────────────────────────────────────

if [[ "${SAVE_BASELINE}" == "true" ]] || [[ ! -f "${BASELINE_FILE}" ]]; then
  mkdir -p "${BASELINES_DIR}"
  python3 - <<PYEOF
import json
data = {
    "timestamp": "${TIMESTAMP}",
    "scheme": "${SCHEME}",
    "destination": "${DESTINATION}",
    "clean_build_seconds": float("${CLEAN_SECONDS}"),
    "incremental_build_seconds": float("${INC_SECONDS}")
}
with open("${BASELINE_FILE}", "w") as f:
    json.dump(data, f, indent=2)
label = "Baseline saved" if "${SAVE_BASELINE}" == "true" else "No baseline existed — auto-saved initial baseline"
print(f"{label} to ${BASELINE_FILE}")
PYEOF
fi
