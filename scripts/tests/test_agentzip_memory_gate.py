"""TDD: AgentZip memory lite — fanout caps, redundancy measurement, LLM-idle compress."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.agentzip_memory_gate import HEALTH_SIGNALS, evaluate, evaluate_fanout_claim


def _scaffold(root: Path) -> None:
    (root / "docs").mkdir()
    (root / "docs" / "AGENTZIP_MEMORY.md").write_text(
        "\n".join(
            [
                "# AgentZip",
                "share template not full forks",
                "compress during llm wait",
                "cap fanout before oom",
                "measure redundancy before scale",
                "8.7x vs linux prefetch",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (root / "scripts").mkdir()
    (root / "scripts" / "agentzip_memory_gate.py").write_text("#\n")
    for sr in (".cursor/skills", ".claude/skills"):
        p = root / sr / "agentzip-memory-lite"
        p.mkdir(parents=True)
        (p / "SKILL.md").write_text("# agentzip-memory-lite\n")
    fixture = root / "marketing" / "data" / "code_health"
    fixture.mkdir(parents=True)
    (fixture / "agentzip_memory_discipline.json").write_text(
        json.dumps(
            {
                "share_template_not_full_forks": True,
                "compress_during_llm_wait": "x",
                "cap_fanout_before_oom": "y",
                "measure_redundancy_before_scale": "z",
                "budget": {"subscribe_agentzip": False},
            }
        )
    )


class SignalTests(unittest.TestCase):
    def test_health_signals(self) -> None:
        self.assertEqual(len(HEALTH_SIGNALS), 4)


class ClaimTests(unittest.TestCase):
    def test_paid_blocked(self) -> None:
        d = evaluate_fanout_claim({"action": "buy_agentzip"})
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_paid_agentzip")

    def test_unmeasured_memory_claim_blocked(self) -> None:
        d = evaluate_fanout_claim({"action": "claim_memory_reduction"})
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_unmeasured_memory_claim")

    def test_fanout_without_budget_blocked(self) -> None:
        d = evaluate_fanout_claim(
            {"action": "spawn_parallel", "concurrent_sandboxes": 4, "validated": True}
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_unbounded_fanout")

    def test_compress_off_idle_blocked(self) -> None:
        d = evaluate_fanout_claim(
            {"action": "compress_on_llm_wait", "during_llm_idle": False}
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_compress_on_critical_path")

    def test_bounded_parallel_allowed(self) -> None:
        d = evaluate_fanout_claim(
            {
                "action": "spawn_parallel",
                "concurrent_sandboxes": 3,
                "memory_budget_ok": True,
                "validated": True,
            }
        )
        self.assertTrue(d.ok)

    def test_measured_claim_allowed(self) -> None:
        d = evaluate_fanout_claim(
            {
                "action": "claim_memory_reduction",
                "redundancy_pct": 80,
                "validated": True,
            }
        )
        self.assertTrue(d.ok)


class PresenceTests(unittest.TestCase):
    def test_missing_docs_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = evaluate(Path(tmp))
            self.assertFalse(report["ready"])
            self.assertIn("missing_docs/AGENTZIP_MEMORY.md", report["blockers"])

    def test_wired_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _scaffold(root)
            report = evaluate(root)
            self.assertTrue(report["ready"], msg=json.dumps(report, indent=2))


if __name__ == "__main__":
    unittest.main()
