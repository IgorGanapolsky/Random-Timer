#!/usr/bin/env bash
# BMAD-lite is vendored in-repo (no npx install). Verify gate + template.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
test -f templates/bmad/SPEC.md
test -f scripts/bmad_readiness_gate.py
python3 scripts/bmad_readiness_gate.py --json --feature 002 | python3 -c 'import sys,json; d=json.load(sys.stdin); assert d["ready"] is True; print({"ready": True, "flow": d["flow"]})'
echo "BMAD-lite OK"
