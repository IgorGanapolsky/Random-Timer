#!/usr/bin/env bash
# android-test-time.sh — Measures Android unit test execution time and throughput.
# Saves baseline to scripts/benchmarks/baselines/android-tests.json
# Usage: ./scripts/benchmarks/android-test-time.sh [--save-baseline]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
ANDROID_DIR="${PROJECT_ROOT}/native-android"
BASELINES_DIR="${SCRIPT_DIR}/baselines"
BASELINE_FILE="${BASELINES_DIR}/android-tests.json"

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

if [[ ! -f "${ANDROID_DIR}/gradlew" ]]; then
  echo "ERROR: gradlew not found at ${ANDROID_DIR}/gradlew" >&2
  exit 1
fi

cd "${ANDROID_DIR}"

echo ""
echo "Android Test Time Benchmark"
separator
echo "Running: ./gradlew testDebugUnitTest --no-daemon"
echo ""

# ── Run tests ─────────────────────────────────────────────────────────────────

TEST_START=$(epoch_ms)
TEST_OUTPUT=$(./gradlew testDebugUnitTest --no-daemon 2>&1)
TEST_EXIT=$?
TEST_END=$(epoch_ms)
ELAPSED=$(seconds_between "$TEST_START" "$TEST_END")

# Print last 20 lines so the user sees the Gradle summary
echo "$TEST_OUTPUT" | tail -20

echo ""
separator

# ── Parse test counts from XML reports ────────────────────────────────────────

REPORT_DIR="${ANDROID_DIR}/app/build/test-results/testDebugUnitTest"
TOTAL_TESTS=0
TOTAL_FAILURES=0
TOTAL_ERRORS=0
TOTAL_SKIPPED=0

if [[ -d "${REPORT_DIR}" ]]; then
  # Sum attributes from all XML result files
  while IFS= read -r xml_file; do
    tests=$(python3 -c "
import xml.etree.ElementTree as ET
tree = ET.parse('${xml_file}')
root = tree.getroot()
print(root.get('tests', '0'))
" 2>/dev/null || echo "0")
    failures=$(python3 -c "
import xml.etree.ElementTree as ET
tree = ET.parse('${xml_file}')
root = tree.getroot()
print(root.get('failures', '0'))
" 2>/dev/null || echo "0")
    errors=$(python3 -c "
import xml.etree.ElementTree as ET
tree = ET.parse('${xml_file}')
root = tree.getroot()
print(root.get('errors', '0'))
" 2>/dev/null || echo "0")
    skipped=$(python3 -c "
import xml.etree.ElementTree as ET
tree = ET.parse('${xml_file}')
root = tree.getroot()
print(root.get('skipped', '0'))
" 2>/dev/null || echo "0")
    TOTAL_TESTS=$((TOTAL_TESTS + tests))
    TOTAL_FAILURES=$((TOTAL_FAILURES + failures))
    TOTAL_ERRORS=$((TOTAL_ERRORS + errors))
    TOTAL_SKIPPED=$((TOTAL_SKIPPED + skipped))
  done < <(find "${REPORT_DIR}" -name "*.xml" 2>/dev/null)
fi

# Fallback: parse Gradle output for test count
if [[ "${TOTAL_TESTS}" -eq 0 ]]; then
  TOTAL_TESTS=$(echo "$TEST_OUTPUT" | grep -oE '[0-9]+ tests?' | grep -oE '[0-9]+' | head -1 || echo "0")
fi

TESTS_PER_SECOND="N/A"
if [[ "${TOTAL_TESTS}" -gt 0 && "${ELAPSED}" != "0.00" ]]; then
  TESTS_PER_SECOND=$(echo "scale=1; ${TOTAL_TESTS} / ${ELAPSED}" | bc)
fi

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# ── Summary ────────────────────────────────────────────────────────────────────

echo ""
printf "%-35s %10s\n" "Metric" "Value"
separator
printf "%-35s %9ss\n"  "Total test run time" "${ELAPSED}"
printf "%-35s %10s\n"  "Tests executed" "${TOTAL_TESTS}"
printf "%-35s %10s\n"  "Failures" "${TOTAL_FAILURES}"
printf "%-35s %10s\n"  "Errors" "${TOTAL_ERRORS}"
printf "%-35s %10s\n"  "Skipped" "${TOTAL_SKIPPED}"
printf "%-35s %10s\n"  "Tests/second" "${TESTS_PER_SECOND}"
separator
echo ""

if [[ "${TEST_EXIT}" -ne 0 ]]; then
  echo "WARNING: Gradle exited with code ${TEST_EXIT} — some tests may have failed." >&2
fi

# ── Baseline comparison ────────────────────────────────────────────────────────

if [[ -f "${BASELINE_FILE}" ]]; then
  BASELINE_TIME=$(python3 -c "import json; d=json.load(open('${BASELINE_FILE}')); print(d['test_run_seconds'])")
  BASELINE_COUNT=$(python3 -c "import json; d=json.load(open('${BASELINE_FILE}')); print(d['total_tests'])")

  TIME_DELTA=$(echo "scale=2; ${ELAPSED} - ${BASELINE_TIME}" | bc)
  COUNT_DELTA=$((TOTAL_TESTS - BASELINE_COUNT))

  echo "Comparison against baseline (${BASELINE_FILE}):"
  printf "%-35s %+10ss\n" "Test run time delta" "${TIME_DELTA}"
  printf "%-35s %+10s\n"  "Test count delta" "${COUNT_DELTA}"
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
    "test_run_seconds": float("${ELAPSED}"),
    "total_tests": int("${TOTAL_TESTS}"),
    "failures": int("${TOTAL_FAILURES}"),
    "errors": int("${TOTAL_ERRORS}"),
    "skipped": int("${TOTAL_SKIPPED}"),
    "tests_per_second": "${TESTS_PER_SECOND}"
}
with open("${BASELINE_FILE}", "w") as f:
    json.dump(data, f, indent=2)
label = "Baseline saved" if "${SAVE_BASELINE}" == "true" else "No baseline existed — auto-saved initial baseline"
print(f"{label} to ${BASELINE_FILE}")
PYEOF
fi
