"""Tests for Superpowers harness gate."""

from __future__ import annotations

from pathlib import Path

from scripts import superpowers_gate as gate


def test_evaluate_blocks_without_skills(tmp_path: Path) -> None:
    report = gate.evaluate(tmp_path)
    assert report["ready"] is False
    assert any(b.startswith("missing_skills:") for b in report["blockers"])


def test_evaluate_ready_with_full_wiring(tmp_path: Path) -> None:
    # Build fixture under tmp without relying on creating a literal .cursor name
    # first: use pathlib and parents; CI runners allow this.
    base = tmp_path / "repo"
    for name in gate.REQUIRED_SKILLS:
        path = base / ".cursor" / "skills" / name / "SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# {name}\n", encoding="utf-8")
    hook = base / ".cursor" / "hooks" / "superpowers-session-start.sh"
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text("#!/bin/bash\necho ok\n", encoding="utf-8")
    (base / ".cursor" / "hooks.json").write_text(
        "{\"hooks\":{\"sessionStart\":[{\"command\":\"bash .cursor/hooks/superpowers-session-start.sh\"}]}}\n",
        encoding="utf-8",
    )
    report = gate.evaluate(base)
    assert report["ready"] is True
    assert report["claim_done_allowed"] is True
    assert report["present_skill_count"] == len(gate.REQUIRED_SKILLS)
