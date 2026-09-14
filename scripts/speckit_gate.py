#!/usr/bin/env python3
"""Spec Kit feature gate — refuse done claims without constitution + SDD artifacts.

Bridges https://github.com/github/spec-kit with Random-Timer artifact GSD and OpenGSD.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

LOOP_STEPS = ("constitution", "specify", "plan", "tasks", "implement", "converge")
PLACEHOLDER_MARKERS = (
    "[PRINCIPLE_",
    "[PROJECT_NAME]",
    "[SECTION_2_NAME]",
    "[GOVERNANCE_RULES]",
    "[CONSTITUTION_VERSION]",
)
FEATURE_ARTIFACTS = ("spec.md", "plan.md", "tasks.md")
CONVERGE_NAMES = ("CONVERGENCE.md", "converge.md", "CONVERGE.md")


def constitution_ok(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size == 0:
        return {"ok": False, "path": str(path), "reason": "missing_or_empty"}
    text = path.read_text(encoding="utf-8")
    hits = [m for m in PLACEHOLDER_MARKERS if m in text]
    if hits:
        return {"ok": False, "path": str(path), "reason": "placeholders", "placeholders": hits}
    if "Random Timer" not in text and "RandomTimer" not in text:
        return {"ok": False, "path": str(path), "reason": "missing_project_identity"}
    return {"ok": True, "path": str(path), "bytes": path.stat().st_size}


def list_feature_dirs(specs_root: Path) -> list[Path]:
    if not specs_root.is_dir():
        return []
    dirs = [p for p in specs_root.iterdir() if p.is_dir()]
    # Prefer ###-name sequential dirs; fall back to any dir.
    numbered = [p for p in dirs if re.match(r"^\d{3,}-", p.name)]
    return sorted(numbered or dirs, key=lambda p: p.name)


def assess_feature_dir(feature_dir: Path) -> dict[str, Any]:
    present = {
        name: (feature_dir / name).is_file() and (feature_dir / name).stat().st_size > 0
        for name in FEATURE_ARTIFACTS
    }
    converge_path = None
    for name in CONVERGE_NAMES:
        candidate = feature_dir / name
        if candidate.is_file() and candidate.stat().st_size > 0:
            converge_path = str(candidate)
            break
    open_tasks = None
    tasks_path = feature_dir / "tasks.md"
    if present.get("tasks.md"):
        body = tasks_path.read_text(encoding="utf-8")
        open_tasks = len(re.findall(r"^\s*-\s*\[\s*\]\s+", body, flags=re.M))
    return {
        "feature_dir": str(feature_dir),
        "artifacts": present,
        "has_spec": present["spec.md"],
        "has_plan": present["plan.md"],
        "has_tasks": present["tasks.md"],
        "converge_path": converge_path,
        "open_checkbox_tasks": open_tasks,
    }


def evaluate(
    root: Path,
    feature: str | None = None,
    require_converge: bool = False,
) -> dict[str, Any]:
    specify = root / ".specify"
    constitution = constitution_ok(specify / "memory" / "constitution.md")
    specs_root = root / "specs"
    features = list_feature_dirs(specs_root)

    selected = None
    if feature:
        for p in features:
            if feature in p.name or p.name == feature:
                selected = p
                break
    elif features:
        selected = features[-1]

    feature_info = (
        assess_feature_dir(selected)
        if selected
        else {
            "feature_dir": None,
            "artifacts": {n: False for n in FEATURE_ARTIFACTS},
            "has_spec": False,
            "has_plan": False,
            "has_tasks": False,
            "converge_path": None,
            "open_checkbox_tasks": None,
        }
    )

    blockers: list[str] = []
    if not (specify / "init-options.json").is_file():
        blockers.append("missing_.specify_init")
    if not constitution["ok"]:
        blockers.append(f"constitution:{constitution.get('reason')}")
    if not feature_info["has_spec"]:
        blockers.append("missing_spec.md")
    if not feature_info["has_plan"]:
        blockers.append("missing_plan.md")
    if not feature_info["has_tasks"]:
        blockers.append("missing_tasks.md")

    implement_ready = len(blockers) == 0
    converge_blockers = list(blockers)
    if not feature_info.get("converge_path"):
        converge_blockers.append("missing_CONVERGENCE.md")
    converged = implement_ready and feature_info.get("converge_path") is not None

    if not constitution["ok"]:
        next_step = "constitution"
    elif not feature_info["has_spec"]:
        next_step = "specify"
    elif not feature_info["has_plan"]:
        next_step = "plan"
    elif not feature_info["has_tasks"]:
        next_step = "tasks"
    elif require_converge and not converged:
        next_step = "converge"
    elif implement_ready and not converged:
        next_step = "implement"
    else:
        next_step = "ship" if converged else "implement"

    claim_ok = converged if require_converge else implement_ready

    return {
        "source": "github/spec-kit",
        "cli_pin": "specify-cli==1.0.6",
        "implement_ready": implement_ready,
        "converged": converged,
        "claim_done_allowed": claim_ok,
        "blockers": blockers if not require_converge else converge_blockers,
        "next_step": next_step,
        "loop": LOOP_STEPS,
        "constitution": constitution,
        "feature": feature_info,
        "feature_count": len(features),
        "artifact_gsd_required": [
            "merge_sha_or_ci_url_or_marketing_data_json",
        ],
        "opengsd_bridge": "python3 scripts/gsd_phase_gate.py --json",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Spec Kit feature ship gate")
    parser.add_argument("--repo-root", default=".", help="Repository root")
    parser.add_argument("--feature", default=None, help="Feature dir substring, e.g. 001")
    parser.add_argument(
        "--require-converge",
        action="store_true",
        help="Require CONVERGENCE.md before claim_done_allowed",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate(Path(args.repo_root).resolve(), args.feature, args.require_converge)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(
            f"implement_ready={report['implement_ready']} converged={report['converged']} "
            f"next_step={report['next_step']} blockers={report['blockers']}"
        )
    return 0 if report["claim_done_allowed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
