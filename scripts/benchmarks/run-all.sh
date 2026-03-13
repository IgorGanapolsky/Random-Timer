#!/usr/bin/env bash
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKIP_IOS=false
SAVE_BASELINE=false
for arg in "$@"; do
  case "$arg" in
    --skip-ios) SKIP_IOS=true ;;
    --save-baseline) SAVE_BASELINE=true ;;
  esac
done
BL_FLAG=""
[[ "$SAVE_BASELINE" == "true" ]] && BL_FLAG="--save-baseline"
FAILURES=0
echo "========================================"
echo "  Random Timer - Full Benchmark Suite"
echo "========================================"
echo ""
bash "$SCRIPT_DIR/android-build-time.sh" $BL_FLAG || ((FAILURES++))
echo ""
bash "$SCRIPT_DIR/android-test-time.sh" $BL_FLAG || ((FAILURES++))
echo ""
bash "$SCRIPT_DIR/apk-size.sh" --no-build $BL_FLAG || ((FAILURES++))
if [[ "$SKIP_IOS" != "true" ]]; then
  echo ""
  echo "=== iOS Build Time Benchmark ==="
  cd "$SCRIPT_DIR/../../native-ios"
  START=$(python3 -c 'import time; print(time.time())')
  xcodebuild -scheme RandomTimer -destination 'platform=iOS Simulator,name=iPhone 16 Pro Max' clean build > /dev/null 2>&1 || true
  END=$(python3 -c 'import time; print(time.time())')
  ELAPSED=$(python3 -c "print(f'{${END} - ${START}:.2f}')")
  echo "  Clean build: ${ELAPSED}s"
fi
echo ""
echo "========================================"
echo "  Summary: $FAILURES regression(s) detected"
echo "========================================"
exit $FAILURES
