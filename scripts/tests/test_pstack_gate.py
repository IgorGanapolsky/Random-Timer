"""Tests for pstack lite gate."""

from __future__ import annotations

from pathlib import Path

from scripts import pstack_gate as gate


def _seed(root: Path, skill_roots: tuple[str, ...]) -> None:
    (root / "docs").mkdir(parents=True)
    (root / "docs" / "PSTACK.md").write_text("# pstack\n", encoding="utf-8")
    (root / "third_party" / "pstack").mkdir(parents=True)
    (root / "third_party" / "pstack" / "LICENSE").write_text("MIT\n", encoding="utf-8")
    for skill_root in skill_roots:
        base = root / skill_root
        base.mkdir(parents=True)
        for name in list(gate.REQUIRED_PRINCIPLES) + list(gate.REQUIRED_SKILLS):
            d = base / name
            d.mkdir(parents=True)
            (d / "SKILL.md").write_text(f"# {name}\n", encoding="utf-8")
    (root / skill_roots[0] / ".pstack-principles-version").write_text(gate.PIN + "\n", encoding="utf-8")


def test_evaluate_ready(tmp_path: Path, monkeypatch) -> None:
    roots = ("cursor_skills", "claude_skills")
    monkeypatch.setattr(gate, "SKILL_ROOTS", roots)
    _seed(tmp_path, roots)
    report = gate.evaluate(tmp_path)
    assert report["ready"] is True
    assert report["principle_count"] == 23


def test_evaluate_blocks_missing_principle(tmp_path: Path, monkeypatch) -> None:
    roots = ("cursor_skills", "claude_skills")
    monkeypatch.setattr(gate, "SKILL_ROOTS", roots)
    _seed(tmp_path, roots)
    skill = tmp_path / "cursor_skills" / "principle-prove-it-works" / "SKILL.md"
    skill.unlink()
    report = gate.evaluate(tmp_path)
    assert report["ready"] is False
    assert any("principle-prove-it-works" in b for b in report["blockers"])
