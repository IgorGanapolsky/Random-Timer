#!/usr/bin/env python3
"""pstack lite gate — vendored principles + poteto-mode + unslop.

Upstream: https://github.com/cursor/plugins/tree/main/pstack
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

PIN = "0.15.2"

REQUIRED_PRINCIPLES = (
    "principle-attack-the-premise",
    "principle-boundary-discipline",
    "principle-build-the-lever",
    "principle-encode-lessons-in-structure",
    "principle-exhaust-the-design-space",
    "principle-experience-first",
    "principle-fix-root-causes",
    "principle-foundational-thinking",
    "principle-guard-the-context-window",
    "principle-laziness-protocol",
    "principle-make-operations-idempotent",
    "principle-migrate-callers-then-delete-legacy-apis",
    "principle-minimize-reader-load",
    "principle-model-the-domain",
    "principle-never-block-on-the-human",
    "principle-outcome-oriented-execution",
    "principle-prove-it-works",
    "principle-redesign-from-first-principles",
    "principle-separate-before-serializing-shared-state",
    "principle-sequence-verifiable-units",
    "principle-subtract-before-you-add",
    "principle-test-behavior-not-implementation",
    "principle-type-system-discipline",
)

REQUIRED_SKILLS = ("poteto-mode", "unslop")
SKILL_ROOTS = (".cursor/skills", ".claude/skills")


def _skill_ok(root: Path, name: str) -> bool:
    return (root / name / "SKILL.md").is_file() and (root / name / "SKILL.md").stat().st_size > 0


def evaluate(repo: Path) -> dict[str, Any]:
    blockers: list[str] = []
    if not (repo / "docs" / "PSTACK.md").is_file():
        blockers.append("missing_docs/PSTACK.md")
    if not (repo / "third_party" / "pstack" / "LICENSE").is_file():
        blockers.append("missing_third_party/pstack/LICENSE")

    found: dict[str, list[str]] = {}
    for skill_root_rel in SKILL_ROOTS:
        skill_root = repo / skill_root_rel
        missing = [n for n in REQUIRED_PRINCIPLES if not _skill_ok(skill_root, n)]
        for name in REQUIRED_SKILLS:
            if not _skill_ok(skill_root, name):
                missing.append(name)
        found[skill_root_rel] = missing
        for m in missing:
            blockers.append(f"missing:{skill_root_rel}/{m}")

    # Version pin file (under either skill root)
    pin = None
    for skill_root_rel in SKILL_ROOTS:
        pin_path = repo / skill_root_rel / ".pstack-principles-version"
        if pin_path.is_file():
            pin = pin_path.read_text(encoding="utf-8").strip()
            break
    if pin != PIN:
        blockers.append(f"pin_mismatch:expected_{PIN}_got_{pin}")

    ready = len(blockers) == 0
    return {
        "source": "pstack-lite",
        "upstream": "cursor/plugins/pstack",
        "pin": PIN,
        "observed_pin": pin,
        "ready": ready,
        "claim_done_allowed": ready,
        "blockers": blockers,
        "principle_count": len(REQUIRED_PRINCIPLES),
        "missing_by_root": found,
        "bridges": {
            "stack_ssot": "docs/AGENT_CODING_STACK.md",
            "compound": "docs/COMPOUND_ENGINEERING.md",
            "superpowers": "docs/SUPERPOWERS.md",
            "pstack": "docs/PSTACK.md",
        },
        "skipped": [
            "full_marketplace_plugin_skills",
            "setup-pstack_model_panel_as_ci_dependency",
        ],
        "next_step": "use_poteto_mode" if ready else "vendor_missing_principles",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="pstack lite presence gate")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate(Path(args.repo_root).resolve())
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"ready={report['ready']} principles={report['principle_count']} blockers={report['blockers']}")
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
