"""Shared helpers for lite agent-stack presence gates.

Extracted so new layers extend instead of copy-pasting Decision/_norm/_skill_ok
(see docs/MAINTAINABILITY_GAP.md — GitClear duplication signal).
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True)
class Decision:
    action: str
    ok: bool
    reason: str


def norm(value: object) -> str:
    return str(value or "").strip().lower()


def skill_ok(root: Path, name: str) -> bool:
    path = root / name / "SKILL.md"
    return path.is_file() and path.stat().st_size > 0


def require_dual_skills(repo: Path, skill_name: str) -> list[str]:
    blockers: list[str] = []
    for skill_root_rel in (".cursor/skills", ".claude/skills"):
        if not skill_ok(repo / skill_root_rel, skill_name):
            blockers.append(f"missing:{skill_root_rel}/{skill_name}")
    return blockers


def require_docs_needles(docs: Path, needles: tuple[str, ...]) -> list[str]:
    blockers: list[str] = []
    if not docs.is_file():
        return blockers
    text = docs.read_text(encoding="utf-8").lower()
    for needle in needles:
        if needle not in text:
            blockers.append(f"docs_missing:{needle.replace(' ', '_')}")
    return blockers


def run_presence_cli(
    *,
    description: str,
    evaluate: Callable[[Path], dict[str, Any]],
    claim_evaluator: Callable[[Mapping[str, object]], Decision] | None = None,
    claim_key: str = "claim",
    argv: list[str] | None = None,
) -> int:
    """Shared --repo/--json/--claim-json CLI for lite presence gates."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--claim-json", type=Path, default=None)
    args = parser.parse_args(argv)

    report = evaluate(args.repo.resolve())
    if claim_evaluator and args.claim_json and args.claim_json.is_file():
        claim = json.loads(args.claim_json.read_text(encoding="utf-8"))
        report[claim_key] = asdict(claim_evaluator(claim))
        report["ready"] = report["ready"] and report[claim_key]["ok"]

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("READY" if report["ready"] else "BLOCKED")
        for b in report["blockers"]:
            print(f"  - {b}")
    return 0 if report["ready"] else 1
