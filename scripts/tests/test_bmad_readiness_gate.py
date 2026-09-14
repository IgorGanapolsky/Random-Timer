"""Tests for BMAD-lite readiness gate."""

from __future__ import annotations

from pathlib import Path

from scripts import bmad_readiness_gate as gate

COMPLETE_SPEC = """# SPEC.md

## Why

Users need a readiness gate so agents cannot invent product decisions.

## Capabilities

1. **Capability**: Validate SPEC sections
   **Success condition**: Given incomplete SPEC, When gate runs, Then ready is false

## Constraints

- Prefer zero-cost local tooling
- English-only docs

## Non-goals

- Full bmad-method framework install

## Success signal

`python3 scripts/bmad_readiness_gate.py --json` reports ready=true
"""


def test_assess_spec_rejects_placeholders(tmp_path: Path) -> None:
    path = tmp_path / "SPEC.md"
    path.write_text(
        "# SPEC\n## Why\n[Business / user problem in 2–4 sentences. Not a solution.]\n",
        encoding="utf-8",
    )
    result = gate.assess_spec(path)
    assert result["ok"] is False
    assert result["placeholder_hits"]


def test_evaluate_quick_flow_ready(tmp_path: Path) -> None:
    feature = tmp_path / "specs" / "002-demo"
    feature.mkdir(parents=True)
    (feature / "SPEC.md").write_text(COMPLETE_SPEC, encoding="utf-8")
    report = gate.evaluate(tmp_path, "002")
    assert report["ready"] is True
    assert report["flow"] == "quick"


def test_evaluate_full_flow_requires_spec_kit(tmp_path: Path) -> None:
    feature = tmp_path / "specs" / "002-demo"
    feature.mkdir(parents=True)
    (feature / "SPEC.md").write_text(COMPLETE_SPEC, encoding="utf-8")
    blocked = gate.evaluate(tmp_path, "002", require_spec_kit=True)
    assert blocked["ready"] is False
    assert "missing_plan.md" in blocked["blockers"]
    (feature / "plan.md").write_text("# plan\n", encoding="utf-8")
    (feature / "tasks.md").write_text("# tasks\n", encoding="utf-8")
    ok = gate.evaluate(tmp_path, "002", require_spec_kit=True)
    assert ok["ready"] is True
    assert ok["flow"] == "full"
