#!/usr/bin/env bash
# Sync obra/superpowers skills into Random Timer (local vendor, pin v6.3.0).
# Upstream: https://github.com/obra/superpowers
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PIN="${SUPERPOWERS_PIN:-v6.3.0}"
TMP="${TMPDIR:-/tmp}/obra-superpowers-${PIN}"
export SUPERPOWERS_DISABLE_TELEMETRY=1

if [[ ! -d "$TMP/.git" ]]; then
  rm -rf "$TMP"
  git clone --depth 1 --branch "$PIN" https://github.com/obra/superpowers.git "$TMP"
fi

export ROOT_ENV="$ROOT" PIN_ENV="$PIN" TMP_ENV="$TMP"
python3 - <<'PY'
import json, os, shutil
from pathlib import Path
root = Path(os.environ["ROOT_ENV"])
src = Path(os.environ["TMP_ENV"]) / "skills"
skip = {"writing-skills"}
required = [
    "using-superpowers",
    "verification-before-completion",
    "systematic-debugging",
    "test-driven-development",
    "using-git-worktrees",
    "subagent-driven-development",
    "brainstorming",
    "writing-plans",
    "executing-plans",
    "dispatching-parallel-agents",
    "requesting-code-review",
    "receiving-code-review",
    "finishing-a-development-branch",
]
for skill_dir in sorted(src.iterdir()):
    if not skill_dir.is_dir() or skill_dir.name in skip:
        continue
    for base in (root / ".cursor" / "skills", root / ".claude" / "skills"):
        dest = base / skill_dir.name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(skill_dir, dest)
missing = [n for n in required if not (root / ".cursor" / "skills" / n / "SKILL.md").is_file()]
if missing:
    raise SystemExit("missing after sync: " + ",".join(missing))
hook = root / ".cursor" / "hooks" / "superpowers-session-start.sh"
if not hook.is_file():
    raise SystemExit("missing session hook; restore from repo")
hp = root / ".cursor" / "hooks.json"
data = json.loads(hp.read_text(encoding="utf-8"))
ss = data.setdefault("hooks", {}).setdefault("sessionStart", [])
ss[:] = [e for e in ss if "superpowers-session-start" not in str(e.get("command", ""))]
entry = {"command": "bash .cursor/hooks/superpowers-session-start.sh", "timeout": 20}
idx = 0
for i, e in enumerate(ss):
    if "rose-lite-session" in str(e.get("command", "")):
        idx = i + 1
        break
ss.insert(idx, entry)
hp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
print("Synced Superpowers", os.environ["PIN_ENV"], "skills; hook wired.")
PY

echo "Gate: python3 scripts/superpowers_gate.py --json"
python3 scripts/superpowers_gate.py --json | python3 -c 'import sys,json; d=json.load(sys.stdin); print({k:d[k] for k in ("ready","pin","present_skill_count","blockers")})'
