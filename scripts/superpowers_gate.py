#!/usr/bin/env python3
"""Superpowers harness gate — required skills + session hook wiring.

Upstream: https://github.com/obra/superpowers (pinned v6.3.0)
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

REQUIRED_SKILLS = (
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
)
HOOK_REL = Path(".cursor/hooks/superpowers-session-start.sh")
PIN = "v6.3.0"


def skill_present(root: Path, name: str) -> bool:
    for base in (root / ".cursor" / "skills", root / ".claude" / "skills"):
        skill = base / name / "SKILL.md"
        if skill.is_file() and skill.stat().st_size > 0:
            return True
    return False


def evaluate(root: Path) -> dict[str, Any]:
    missing = [n for n in REQUIRED_SKILLS if not skill_present(root, n)]
    hook = root / HOOK_REL
    hook_ok = hook.is_file() and hook.stat().st_size > 0
    hooks_json = root / ".cursor" / "hooks.json"
    wired = False
    if hooks_json.is_file():
        text = hooks_json.read_text(encoding="utf-8")
        wired = "superpowers-session-start" in text
    blockers: list[str] = []
    if missing:
        blockers.append("missing_skills:" + ",".join(missing))
    if not hook_ok:
        blockers.append("missing_session_hook")
    if not wired:
        blockers.append("hooks_json_not_wired")
    ready = len(blockers) == 0
    return {
        "source": "obra/superpowers",
        "pin": PIN,
        "ready": ready,
        "claim_done_allowed": ready,
        "blockers": blockers,
        "required_skill_count": len(REQUIRED_SKILLS),
        "present_skill_count": len(REQUIRED_SKILLS) - len(missing),
        "missing_skills": missing,
        "hook_ok": hook_ok,
        "hooks_json_wired": wired,
        "telemetry": "SUPERPOWERS_DISABLE_TELEMETRY=1 (default in session hook)",
        "bridges": {
            "spec_kit": "docs/SPEC_KIT.md",
            "opengsd": "docs/GSD_OPENGSD.md",
            "superpowers": "docs/SUPERPOWERS.md",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Superpowers harness gate")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate(Path(args.repo_root).resolve())
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"ready={report['ready']} blockers={report['blockers']}")
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
