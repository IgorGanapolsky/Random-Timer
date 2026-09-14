#!/usr/bin/env bash
# Verify Compound Engineering lite (does NOT install EveryInc plugin).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
python3 -m pytest scripts/tests/test_compound_gate.py -q
python3 scripts/compound_gate.py --json --slug 003 | python3 -c 'import json,sys; r=json.load(sys.stdin); assert r["ready"] is True, r; print("compound_gate ready=true")'
echo "Compound Engineering lite OK"
