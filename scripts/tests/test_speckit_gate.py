"""Tests for Spec Kit feature gate."""

from __future__ import annotations

from pathlib import Path

from scripts import speckit_gate as gate


def _write_constitution(root: Path, body: str | None = None) -> None:
    path = root / ".specify" / "memory" / "constitution.md"
    path.parent.mkdir(parents=True)
    text = body or (
        "# Random Timer Constitution\n\n### I. Evidence\nAlways cite commands.\n"
    )
    path.write_text(text, encoding="utf-8")
    (root / ".specify" / "init-options.json").write_text("{}", encoding="utf-8")


def test_constitution_rejects_placeholders(tmp_path: Path) -> None:
    path = tmp_path / "constitution.md"
    path.write_text("# [PROJECT_NAME] Constitution\n### [PRINCIPLE_1_NAME]\n", encoding="utf-8")
    result = gate.constitution_ok(path)
    assert result["ok"] is False
    assert result["reason"] == "placeholders"


def test_evaluate_blocks_without_plan(tmp_path: Path) -> None:
    _write_constitution(tmp_path)
    feature = tmp_path / "specs" / "001-demo"
    feature.mkdir(parents=True)
    (feature / "spec.md").write_text("# Spec\n", encoding="utf-8")
    (feature / "tasks.md").write_text("- [ ] do thing\n", encoding="utf-8")
    report = gate.evaluate(tmp_path, "001")
    assert report["implement_ready"] is False
    assert "missing_plan.md" in report["blockers"]
    assert report["next_step"] == "plan"


def test_evaluate_implement_ready_without_converge(tmp_path: Path) -> None:
    _write_constitution(tmp_path)
    feature = tmp_path / "specs" / "001-demo"
    feature.mkdir(parents=True)
    for name in ("spec.md", "plan.md", "tasks.md"):
        (feature / name).write_text(f"# {name}\n", encoding="utf-8")
    report = gate.evaluate(tmp_path)
    assert report["implement_ready"] is True
    assert report["converged"] is False
    assert report["claim_done_allowed"] is True
    assert report["next_step"] == "implement"


def test_evaluate_require_converge(tmp_path: Path) -> None:
    _write_constitution(tmp_path)
    feature = tmp_path / "specs" / "001-demo"
    feature.mkdir(parents=True)
    for name in ("spec.md", "plan.md", "tasks.md"):
        (feature / name).write_text(f"# {name}\n", encoding="utf-8")
    blocked = gate.evaluate(tmp_path, require_converge=True)
    assert blocked["claim_done_allowed"] is False
    assert "missing_CONVERGENCE.md" in blocked["blockers"]
    (feature / "CONVERGENCE.md").write_text("Status: Converged\n", encoding="utf-8")
    ok = gate.evaluate(tmp_path, require_converge=True)
    assert ok["converged"] is True
    assert ok["claim_done_allowed"] is True
    assert ok["next_step"] == "ship"
