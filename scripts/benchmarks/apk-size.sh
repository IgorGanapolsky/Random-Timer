#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
ANDROID_DIR="$PROJECT_DIR/native-android"
BASELINE_FILE="$SCRIPT_DIR/baselines/apk-size.json"
APK_PATH="$ANDROID_DIR/app/build/outputs/apk/debug/app-debug.apk"
cd "$ANDROID_DIR"
if [[ "$*" != *"--no-build"* ]]; then
  echo "Building debug APK..."
  ./gradlew assembleDebug > /dev/null 2>&1
fi
if [[ ! -f "$APK_PATH" ]]; then
  echo "ERROR: APK not found at $APK_PATH"; exit 1
fi
SIZE_BYTES=$(stat -f%z "$APK_PATH" 2>/dev/null || stat -c%s "$APK_PATH")
SIZE_MB=$(python3 -c "print(f'{${SIZE_BYTES} / 1048576:.2f}')")
echo "=== APK Size Benchmark ==="
echo "  Size: ${SIZE_MB} MB (${SIZE_BYTES} bytes)"
EXIT_CODE=0
if [[ -f "$BASELINE_FILE" && "$*" != *"--save-baseline"* ]]; then
  python3 -c "
import json, sys
with open('$BASELINE_FILE') as f:
    b = json.load(f)
prev = b['size_bytes']
delta_bytes = $SIZE_BYTES - prev
delta_mb = delta_bytes / 1048576
pct = (delta_bytes / prev) * 100 if prev else 0
sign = '+' if delta_bytes > 0 else ''
print(f'  Delta: {sign}{delta_mb:.2f} MB ({sign}{pct:.1f}%)')
if pct > 10:
    print('  WARNING: APK size regressed >10%!')
    sys.exit(1)
" || EXIT_CODE=1
else
  mkdir -p "$SCRIPT_DIR/baselines"
  python3 -c "
import json
data = {'size_bytes': $SIZE_BYTES, 'size_mb': $SIZE_MB}
with open('$BASELINE_FILE', 'w') as f:
    json.dump(data, f, indent=2)
print('  Baseline saved.')
"
fi
exit $EXIT_CODE
