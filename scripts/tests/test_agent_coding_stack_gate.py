"""Tests for agent coding stack presence gate."""

from __future__ import annotations

from pathlib import Path
from unittest import mock

from scripts import agent_coding_stack_gate as gate


def _touch(root: Path, rel: str, body: str = "x\n") -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def test_evaluate_ready_when_docs_and_children_ok(tmp_path: Path) -> None:
    for rel in gate.REQUIRED_DOCS + gate.REQUIRED_SCRIPTS:
        if rel == "docs/AGENT_CODING_STACK.md":
            _touch(
                tmp_path,
                rel,
                "# stack\nDo **not** use archived gsd-build.\nUses open-gsd/gsd-core.\n",
            )
        else:
            _touch(tmp_path, rel)

    child_ok = {
        "scripts/superpowers_gate.py": {"ready": True},
        "scripts/bmad_readiness_gate.py": {"ready": True},
        "scripts/compound_gate.py": {"ready": True},
        "scripts/pstack_gate.py": {"ready": True},
        "scripts/value_center_gate.py": {"ready": True},
        "scripts/speckit_gate.py": {"constitution": {"ok": True}, "implement_ready": True},
        "scripts/gsd_phase_gate.py": {"source": "open-gsd/gsd-core", "ship_ready": False},
    }

    def fake_run(repo: Path, script: str, extra: list[str] | None = None) -> dict:
        return child_ok[script]

    with mock.patch.object(gate, "_run_json", side_effect=fake_run):
        report = gate.evaluate(tmp_path)
    assert report["ready"] is True
    assert report["children"]["gsd_ship_ready"] is False
    assert report["children"]["pstack_ready"] is True
    assert report["children"]["value_center_ready"] is True


def test_evaluate_blocks_missing_ssot_ban(tmp_path: Path) -> None:
    for rel in gate.REQUIRED_DOCS + gate.REQUIRED_SCRIPTS:
        _touch(tmp_path, rel, "# missing ban and successor\n")

    with mock.patch.object(
        gate,
        "_run_json",
        return_value={"ready": True, "constitution": {"ok": True}, "source": "open-gsd/gsd-core"},
    ):
        report = gate.evaluate(tmp_path)
    assert report["ready"] is False
    assert any("ssot_" in b for b in report["blockers"])
