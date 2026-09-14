#!/usr/bin/env bash
# Install OpenGSD gsd-core (Cursor, local, core profile) — zero-cost npm, no global required.
# Upstream: https://github.com/open-gsd/gsd-core
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
VERSION="${OPENGSD_GSD_CORE_VERSION:-1.14.0}"
echo "Installing @opengsd/gsd-core@${VERSION} for Cursor (local, profile=core)"
npx -y "@opengsd/gsd-core@${VERSION}" --cursor --local --profile=core
# Rewrite absolute hook paths to repo-relative (portable across worktrees)
python3 - <<'PY'
import json
from pathlib import Path
p = Path(".cursor/hooks.json")
data = json.loads(p.read_text(encoding="utf-8"))
for event, entries in (data.get("hooks") or {}).items():
    if not isinstance(entries, list):
        continue
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        cmd = entry.get("command", "")
        if "gsd-cursor-" in cmd and ".cursor/hooks/" in cmd:
            name = cmd.rsplit("/", 1)[-1].strip('"')
            entry["command"] = f"node .cursor/hooks/{name}"
            entry["type"] = "command"
            entry["gsd-managed"] = True
p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
print("hooks.json normalized to relative node paths")
PY
echo "Done. Mention gsd-phase / gsd-plan-phase / gsd-execute-phase skills in Cursor."
echo "Planning SSOT: .planning/STATE.md"
