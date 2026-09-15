"""Shared helpers for lite agent-stack presence gates.

Extracted so new layers extend instead of copy-pasting Decision/_norm/_skill_ok
(see docs/MAINTAINABILITY_GAP.md — GitClear duplication signal).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


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
