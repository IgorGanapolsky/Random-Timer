#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
ANDROID_DIR="$PROJECT_DIR/native-android"
BASELINE_FILE="$SCRIPT_DIR/baselines/android-build.json"
cd "$ANDROID_DIR"
measure() {
  local start end
  start=$(python3 -c 'import time; print(time.time())')
  "$@" > /dev/null 2>&1
  end=$(python3 -c 'import time; print(time.time())')
  python3 -c "print(f'{${end} - ${start}:.2f}')"
}
echo "=== Android Build Time Benchmark ==="
echo ""
echo "[1/3] Clean build..."
./gradlew clean > /dev/null 2>&1
CLEAN_TIME=$(measure ./gradlew assembleDebug)
echo "  Clean build: ${CLEAN_TIME}s"
echo "[2/3] Incremental build (no changes)..."
INCR_TIME=$(measure ./gradlew assembleDebug)
echo "  Incremental: ${INCR_TIME}s"
echo "[3/3] Cached build (after clean)..."
./gradlew clean > /dev/null 2>&1
CACHED_TIME=$(measure ./gradlew assembleDebug --build-cache)
echo "  Cached:      ${CACHED_TIME}s"
if [[ -f "$BASELINE_FILE" && "$*" != *"--save-baseline"* ]]; then
  echo ""
  echo "--- vs baseline ---"
  python3 -c "
import json
with open('$BASELINE_FILE') as f:
    b = json.load(f)
for label, cur in [('clean', $CLEAN_TIME), ('incremental', $INCR_TIME), ('cached', $CACHED_TIME)]:
    prev = b.get(label, 0)
    delta = cur - prev
    sign = '+' if delta > 0 else ''
    print(f'  {label}: {cur:.2f}s ({sign}{delta:.2f}s vs baseline {prev:.2f}s)')
"
else
  mkdir -p "$SCRIPT_DIR/baselines"
  python3 -c "
import json
data = {'clean': $CLEAN_TIME, 'incremental': $INCR_TIME, 'cached': $CACHED_TIME}
with open('$BASELINE_FILE', 'w') as f:
    json.dump(data, f, indent=2)
print('  Baseline saved.')
"
fi
