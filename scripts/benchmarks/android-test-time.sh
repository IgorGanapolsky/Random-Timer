#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
ANDROID_DIR="$PROJECT_DIR/native-android"
BASELINE_FILE="$SCRIPT_DIR/baselines/android-tests.json"
cd "$ANDROID_DIR"
echo "=== Android Test Time Benchmark ==="
echo ""
START=$(python3 -c 'import time; print(time.time())')
OUTPUT=$(./gradlew testDebugUnitTest 2>&1) || true
END=$(python3 -c 'import time; print(time.time())')
ELAPSED=$(python3 -c "print(f'{${END} - ${START}:.2f}')")
TEST_COUNT=$(echo "$OUTPUT" | grep -oE '[0-9]+ tests' | head -1 | grep -oE '[0-9]+' || echo "0")
FAILURES=$(echo "$OUTPUT" | grep -oE '[0-9]+ failures' | head -1 | grep -oE '[0-9]+' || echo "0")
if [[ "$TEST_COUNT" -gt 0 ]]; then
  TPS=$(python3 -c "print(f'{${TEST_COUNT} / ${ELAPSED}:.1f}')")
else
  TPS="0"
fi
echo "  Time:     ${ELAPSED}s"
echo "  Tests:    ${TEST_COUNT}"
echo "  Failures: ${FAILURES}"
echo "  Rate:     ${TPS} tests/sec"
if [[ -f "$BASELINE_FILE" && "$*" != *"--save-baseline"* ]]; then
  python3 -c "
import json
with open('$BASELINE_FILE') as f:
    b = json.load(f)
delta = $ELAPSED - b.get('time', 0)
sign = '+' if delta > 0 else ''
print(f'  vs baseline: {sign}{delta:.2f}s ({b.get(\"test_count\", \"?\")} tests in {b.get(\"time\", 0):.2f}s)')
"
else
  mkdir -p "$SCRIPT_DIR/baselines"
  python3 -c "
import json
data = {'time': $ELAPSED, 'test_count': $TEST_COUNT, 'failures': $FAILURES, 'tests_per_sec': $TPS}
with open('$BASELINE_FILE', 'w') as f:
    json.dump(data, f, indent=2)
print('  Baseline saved.')
"
fi
