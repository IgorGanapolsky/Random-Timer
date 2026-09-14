#!/usr/bin/env bash
# Steal Expo/Callstack PR-review pattern: capture agent-device runtime evidence locally.
# Green unit CI is not proof the mobile UI still works.
# Usage: ./scripts/device-tests/agent-device-pr-evidence.sh [bundle-id]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT_DIR="${AGENT_DEVICE_EVIDENCE_DIR:-$ROOT/native-ios/build/agent-device-pr-evidence}"
BUNDLE_ID="${1:-com.igorganapolsky.randomtimer}"
PLATFORM="${AGENT_DEVICE_PLATFORM:-ios}"
mkdir -p "$OUT_DIR"

AD=(npx -y agent-device)
if command -v agent-device >/dev/null 2>&1; then
  AD=(agent-device)
fi

TS="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
SCREENSHOT="$OUT_DIR/screenshot-${TS}.png"
SNAPSHOT="$OUT_DIR/snapshot-${TS}.json"
REPORT="$OUT_DIR/evidence-${TS}.json"

echo "doctor first"
python3 "$ROOT/scripts/agent_device_doctor.py" --json | tee "$OUT_DIR/doctor-${TS}.json"

echo "open $BUNDLE_ID"
"${AD[@]}" open "$BUNDLE_ID" --platform "$PLATFORM" --relaunch || {
  echo "open failed — install a Simulator build first" >&2
  exit 2
}

echo "screenshot → $SCREENSHOT"
"${AD[@]}" screenshot --platform "$PLATFORM" --path "$SCREENSHOT" || true

echo "snapshot → $SNAPSHOT"
"${AD[@]}" snapshot -i --platform "$PLATFORM" > "$SNAPSHOT" || true

"${AD[@]}" close "$BUNDLE_ID" --platform "$PLATFORM" || true

python3 - <<PY
import json
from pathlib import Path
report = {
  "generated_at": "$TS",
  "bundle_id": "$BUNDLE_ID",
  "platform": "$PLATFORM",
  "screenshot": "$SCREENSHOT",
  "snapshot": "$SNAPSHOT",
  "rule": "code_review_and_green_ci_do_not_prove_mobile_runtime",
  "source": "callstack_dispatch_2026-09",
}
Path("$REPORT").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
PY

echo "Evidence written under $OUT_DIR — attach paths in PR body before claiming UI done."
