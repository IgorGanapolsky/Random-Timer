#!/usr/bin/env bash
# run-all.sh — Runs all benchmarks, produces a summary table, and exits 1 if
# any metric regressed more than 10% against its baseline.
# Usage: ./scripts/benchmarks/run-all.sh [--save-baseline] [--skip-ios]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASELINES_DIR="${SCRIPT_DIR}/baselines"

SAVE_BASELINE=false
SKIP_IOS=false
for arg in "$@"; do
  case "$arg" in
    --save-baseline) SAVE_BASELINE=true ;;
    --skip-ios)      SKIP_IOS=true ;;
  esac
done

EXTRA_ARGS=""
if [[ "${SAVE_BASELINE}" == "true" ]]; then
  EXTRA_ARGS="--save-baseline"
fi

# ── Helpers ────────────────────────────────────────────────────────────────────

separator() {
  printf '%0.s═' {1..70}
  printf '\n'
}

thin_separator() {
  printf '%0.s─' {1..70}
  printf '\n'
}

OVERALL_START=$(python3 -c "import time; print(int(time.time() * 1000))")
REGRESSIONS=()
RESULTS=()   # Each entry: "label|value|status"

run_benchmark() {
  local name="$1"
  local script="$2"
  local extra="${3:-}"

  echo ""
  separator
  echo "  Running: ${name}"
  separator

  local start
  start=$(python3 -c "import time; print(int(time.time() * 1000))")

  set +e
  bash "${script}" ${extra}
  local exit_code=$?
  set -e

  local end
  end=$(python3 -c "import time; print(int(time.time() * 1000))")
  local elapsed
  elapsed=$(echo "scale=1; ($end - $start) / 1000" | bc)

  if [[ "${exit_code}" -eq 0 ]]; then
    RESULTS+=("${name}|${elapsed}s|PASS")
  else
    RESULTS+=("${name}|${elapsed}s|FAIL (regression or error)")
    REGRESSIONS+=("${name}")
  fi
}

# ── Run each benchmark ────────────────────────────────────────────────────────

run_benchmark "Android Build Time" "${SCRIPT_DIR}/android-build-time.sh" "${EXTRA_ARGS}"
run_benchmark "Android Test Time"  "${SCRIPT_DIR}/android-test-time.sh"  "${EXTRA_ARGS}"
run_benchmark "APK Size"           "${SCRIPT_DIR}/apk-size.sh"           "--no-build ${EXTRA_ARGS}"

if [[ "${SKIP_IOS}" == "false" ]] && command -v xcodebuild &>/dev/null; then
  run_benchmark "iOS Build Time" "${SCRIPT_DIR}/ios-build-time.sh" "${EXTRA_ARGS}"
else
  RESULTS+=("iOS Build Time|skipped|SKIP")
fi

# ── Summary table ─────────────────────────────────────────────────────────────

OVERALL_END=$(python3 -c "import time; print(int(time.time() * 1000))")
OVERALL_ELAPSED=$(echo "scale=1; (${OVERALL_END} - ${OVERALL_START}) / 1000" | bc)

echo ""
echo ""
separator
printf "  %-35s %-12s %s\n" "Benchmark" "Duration" "Status"
thin_separator

for result in "${RESULTS[@]}"; do
  IFS='|' read -r label duration status <<< "${result}"
  if [[ "${status}" == "PASS" ]]; then
    STATUS_DISPLAY="OK"
  elif [[ "${status}" == "SKIP" ]]; then
    STATUS_DISPLAY="SKIP"
  else
    STATUS_DISPLAY="FAIL"
  fi
  printf "  %-35s %-12s %s\n" "${label}" "${duration}" "${STATUS_DISPLAY}"
done

thin_separator
printf "  %-35s %-12s\n" "Total wall time" "${OVERALL_ELAPSED}s"
separator
echo ""

# ── Baselines location ────────────────────────────────────────────────────────

echo "Baselines stored in: ${BASELINES_DIR}/"
for f in "${BASELINES_DIR}"/*.json; do
  [[ -f "${f}" ]] || continue
  fname=$(basename "${f}")
  ts=$(python3 -c "import json; d=json.load(open('${f}')); print(d.get('timestamp','unknown'))" 2>/dev/null || echo "unknown")
  printf "  %-35s recorded %s\n" "${fname}" "${ts}"
done
echo ""

# ── Regression gate ───────────────────────────────────────────────────────────

if [[ "${#REGRESSIONS[@]}" -gt 0 ]]; then
  echo "REGRESSION DETECTED in the following benchmarks:" >&2
  for r in "${REGRESSIONS[@]}"; do
    echo "  - ${r}" >&2
  done
  echo "" >&2
  echo "Any metric that regressed >10% from baseline causes exit code 1." >&2
  exit 1
fi

echo "All benchmarks passed."
