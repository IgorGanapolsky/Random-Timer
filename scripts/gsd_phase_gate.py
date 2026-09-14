#!/usr/bin/env python3
"""OpenGSD phase gate — refuse ship/done claims without planning + verify artifacts.

Bridges https://github.com/open-gsd/gsd-core phase loop with Random-Timer artifact GSD.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

REQUIRED_ROOT_FILES = ("STATE.md", "PROJECT.md", "ROADMAP.md")
LOOP_STEPS = ("discuss", "plan", "execute", "verify", "ship")


def parse_state_frontmatter(text: str) -> dict[str, Any]:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    block = text[3:end].strip()
    out: dict[str, Any] = {}
    for line in block.splitlines():
        if ":" not in line or line.strip().startswith("#"):
            continue
        key, _, raw = line.partition(":")
        key = key.strip()
        val = raw.strip().strip("'\"")
        if key in {"status", "milestone", "milestone_name", "next_action", "active_phase"}:
            out[key] = val if val not in {"null", ""} else None
    return out


def assess_phase_dir(phase_dir: Path) -> dict[str, Any]:
    context = phase_dir / "CONTEXT.md"
    plans = sorted(phase_dir.glob("PLAN*.md")) + sorted(phase_dir.glob("**/PLAN.md"))
    verification = phase_dir / "VERIFICATION.md"
    summary = phase_dir / "SUMMARY.md"
    return {
        "phase_dir": str(phase_dir),
        "has_context": context.is_file() and context.stat().st_size > 0,
        "plan_count": len([p for p in plans if p.is_file()]),
        "has_verification": verification.is_file() and verification.stat().st_size > 0,
        "has_summary": summary.is_file() and summary.stat().st_size > 0,
    }


def evaluate_ship_ready(root: Path, phase_id: str | None = None) -> dict[str, Any]:
    planning = root / ".planning"
    missing_root = [name for name in REQUIRED_ROOT_FILES if not (planning / name).is_file()]
    state_path = planning / "STATE.md"
    state = parse_state_frontmatter(state_path.read_text(encoding="utf-8")) if state_path.is_file() else {}

    phases_root = planning / "phases"
    phase_dirs = sorted(phases_root.glob("*")) if phases_root.is_dir() else []
    phase_dirs = [p for p in phase_dirs if p.is_dir()]

    selected = None
    if phase_id:
        for p in phase_dirs:
            if phase_id in p.name or p.name.startswith(f"{phase_id}-") or p.name.startswith(f"0{phase_id}-"):
                selected = p
                break
    elif phase_dirs:
        selected = phase_dirs[0]

    phase_info = assess_phase_dir(selected) if selected else {
        "phase_dir": None,
        "has_context": False,
        "plan_count": 0,
        "has_verification": False,
        "has_summary": False,
    }

    blockers: list[str] = []
    if missing_root:
        blockers.append(f"missing_planning_root:{','.join(missing_root)}")
    if not phase_info["has_context"]:
        blockers.append("missing_CONTEXT.md")
    if int(phase_info["plan_count"]) < 1:
        blockers.append("missing_PLAN")
    if not phase_info["has_verification"]:
        blockers.append("missing_VERIFICATION.md")

    ship_ready = len(blockers) == 0
    next_step = "ship" if ship_ready else (
        "discuss" if not phase_info["has_context"] else
        "plan" if int(phase_info["plan_count"]) < 1 else
        "verify" if not phase_info["has_verification"] else
        "execute"
    )

    return {
        "source": "open-gsd/gsd-core",
        "ship_ready": ship_ready,
        "blockers": blockers,
        "next_step": next_step,
        "loop": LOOP_STEPS,
        "state": state,
        "phase": phase_info,
        "artifact_gsd_required": [
            "merge_sha_or_ci_url_or_marketing_data_json",
        ],
        "claim_done_allowed": ship_ready,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="OpenGSD phase ship gate")
    parser.add_argument("--repo-root", default=".", help="Repository root")
    parser.add_argument("--phase", default=None, help="Phase id substring, e.g. 01 or 1")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate_ship_ready(Path(args.repo_root).resolve(), args.phase)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(
            f"ship_ready={report['ship_ready']} next_step={report['next_step']} "
            f"blockers={report['blockers']}"
        )
    return 0 if report["ship_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
