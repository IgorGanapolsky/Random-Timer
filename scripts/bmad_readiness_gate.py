#!/usr/bin/env python3
"""BMAD-lite readiness gate — SPEC.md five-element contract before coding.

Inspired by https://sam-solutions.com/blog/spec-driven-development-with-bmad-method/
Bridges Spec Kit feature dirs under specs/ without installing full bmad-method.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

REQUIRED_SECTIONS = (
    "Why",
    "Capabilities",
    "Constraints",
    "Non-goals",
    "Success signal",
)
PLACEHOLDERS = (
    "[short name]",
    "[Business / user problem",
    "[###-feature-slug]",
    "List each capability",
)


def list_feature_dirs(specs_root: Path) -> list[Path]:
    if not specs_root.is_dir():
        return []
    dirs = [p for p in specs_root.iterdir() if p.is_dir()]
    numbered = [p for p in dirs if re.match(r"^\d{3,}-", p.name)]
    return sorted(numbered or dirs, key=lambda p: p.name)


def parse_sections(text: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current: str | None = None
    buf: list[str] = []
    for line in text.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            if current is not None:
                sections[current] = "\n".join(buf).strip()
            current = m.group(1).strip()
            buf = []
        else:
            buf.append(line)
    if current is not None:
        sections[current] = "\n".join(buf).strip()
    return sections


def assess_spec(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size == 0:
        return {
            "ok": False,
            "path": str(path),
            "missing_sections": list(REQUIRED_SECTIONS),
            "placeholder_hits": [],
            "reason": "missing_or_empty",
        }
    text = path.read_text(encoding="utf-8")
    sections = parse_sections(text)
    missing = [name for name in REQUIRED_SECTIONS if name not in sections or not sections[name]]
    placeholders = [p for p in PLACEHOLDERS if p in text]
    # Capabilities need at least one Success condition marker
    caps = sections.get("Capabilities", "")
    if "Success condition" not in caps and "success condition" not in caps.lower():
        if "missing_success_condition" not in missing:
            missing.append("Capabilities.success_condition")
    ok = not missing and not placeholders
    return {
        "ok": ok,
        "path": str(path),
        "missing_sections": missing,
        "placeholder_hits": placeholders,
        "section_keys": sorted(sections.keys()),
        "bytes": path.stat().st_size,
    }


def evaluate(root: Path, feature: str | None = None, require_spec_kit: bool = False) -> dict[str, Any]:
    features = list_feature_dirs(root / "specs")
    selected = None
    if feature:
        for p in features:
            if feature in p.name or p.name == feature:
                selected = p
                break
    elif features:
        selected = features[-1]

    blockers: list[str] = []
    if selected is None:
        blockers.append("missing_feature_dir")
        spec_info = {"ok": False, "path": None, "missing_sections": list(REQUIRED_SECTIONS)}
        kit = {"has_plan": False, "has_tasks": False}
    else:
        spec_info = assess_spec(selected / "SPEC.md")
        if not spec_info["ok"]:
            if spec_info.get("reason") == "missing_or_empty":
                blockers.append("missing_SPEC.md")
            if spec_info.get("missing_sections"):
                blockers.append("incomplete_SPEC:" + ",".join(spec_info["missing_sections"]))
            if spec_info.get("placeholder_hits"):
                blockers.append("SPEC_placeholders")
        kit = {
            "has_plan": (selected / "plan.md").is_file() and (selected / "plan.md").stat().st_size > 0,
            "has_tasks": (selected / "tasks.md").is_file() and (selected / "tasks.md").stat().st_size > 0,
        }
        if require_spec_kit:
            if not kit["has_plan"]:
                blockers.append("missing_plan.md")
            if not kit["has_tasks"]:
                blockers.append("missing_tasks.md")

    ready = len(blockers) == 0
    flow = "full" if require_spec_kit else "quick"
    return {
        "source": "bmad-lite",
        "article": "sam-solutions.com/blog/spec-driven-development-with-bmad-method",
        "flow": flow,
        "ready": ready,
        "claim_done_allowed": ready,
        "blockers": blockers,
        "feature_dir": str(selected) if selected else None,
        "spec": spec_info,
        "spec_kit": kit,
        "next_step": "implement" if ready else "complete_SPEC.md",
        "bridges": {
            "spec_kit": "docs/SPEC_KIT.md",
            "opengsd": "docs/GSD_OPENGSD.md",
            "superpowers": "docs/SUPERPOWERS.md",
            "bmad": "docs/BMAD.md",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="BMAD-lite implementation readiness gate")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--feature", default=None)
    parser.add_argument(
        "--require-spec-kit",
        action="store_true",
        help="Full flow: also require plan.md and tasks.md",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate(Path(args.repo_root).resolve(), args.feature, args.require_spec_kit)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"ready={report['ready']} flow={report['flow']} blockers={report['blockers']}")
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
