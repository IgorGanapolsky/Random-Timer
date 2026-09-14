"""Tests for OpenGSD phase gate."""

from __future__ import annotations

from pathlib import Path

from scripts import gsd_phase_gate as gate


def test_parse_state_frontmatter() -> None:
    text = """---
gsd_state_version: '1.0'
status: planning
next_action: plan-phase
---

# body
"""
    parsed = gate.parse_state_frontmatter(text)
    assert parsed["status"] == "planning"
    assert parsed["next_action"] == "plan-phase"


def test_evaluate_ship_ready_blocks_without_verify(tmp_path: Path) -> None:
    planning = tmp_path / ".planning"
    planning.mkdir()
    (planning / "STATE.md").write_text("---\nstatus: executing\n---\n", encoding="utf-8")
    (planning / "PROJECT.md").write_text("x", encoding="utf-8")
    (planning / "ROADMAP.md").write_text("x", encoding="utf-8")
    phase = planning / "phases" / "01-demo"
    phase.mkdir(parents=True)
    (phase / "CONTEXT.md").write_text("decisions", encoding="utf-8")
    (phase / "PLAN-01.md").write_text("plan", encoding="utf-8")
    report = gate.evaluate_ship_ready(tmp_path, "01")
    assert report["ship_ready"] is False
    assert "missing_VERIFICATION.md" in report["blockers"]
    assert report["next_step"] == "verify"


def test_evaluate_ship_ready_passes_with_full_loop(tmp_path: Path) -> None:
    planning = tmp_path / ".planning"
    planning.mkdir()
    for name in ("STATE.md", "PROJECT.md", "ROADMAP.md"):
        (planning / name).write_text("---\nstatus: verifying\n---\n", encoding="utf-8")
    phase = planning / "phases" / "01-demo"
    phase.mkdir(parents=True)
    (phase / "CONTEXT.md").write_text("decisions", encoding="utf-8")
    (phase / "PLAN-01.md").write_text("plan", encoding="utf-8")
    (phase / "VERIFICATION.md").write_text("ok", encoding="utf-8")
    report = gate.evaluate_ship_ready(tmp_path)
    assert report["ship_ready"] is True
    assert report["next_step"] == "ship"
    assert report["claim_done_allowed"] is True
