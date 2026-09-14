#!/usr/bin/env bash
# Verify pstack lite (does NOT run /add-plugin).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
python3 -m pytest scripts/tests/test_pstack_gate.py -q
python3 scripts/pstack_gate.py --json | python3 -c 'import json,sys; r=json.load(sys.stdin); assert r["ready"] is True, r; print("pstack_gate ready=true principles=%s" % r["principle_count"])'
echo "pstack lite OK"
