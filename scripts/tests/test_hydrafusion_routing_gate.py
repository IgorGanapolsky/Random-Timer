"""TDD: HydraFusion routing lite — Single/Cascade/Critique + accounting."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.hydrafusion_routing_gate import (
    HEALTH_SIGNALS,
    evaluate,
    evaluate_routing_claim,
    select_pattern,
)


def _scaffold(root: Path) -> None:
    (root / "docs").mkdir()
    (root / "docs" / "HYDRAFUSION_ROUTING.md").write_text(
        "\n".join(
            [
                "# HydraFusion routing",
                "single cascade critique patterns",
                "complete cost accounting",
                "bounded execution timeouts",
                "fail-safe apply",
                "validated routing",
                "tool-less isolated critic",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (root / "docs" / "HYDRAFUSION_ORCHESTRATION.md").write_text(
        "# orchestration\nsingle cascade critique\n", encoding="utf-8"
    )
    (root / "scripts").mkdir()
    (root / "scripts" / "hydrafusion_routing_gate.py").write_text("#\n")
    (root / "scripts" / "hydrafusion_route.py").write_text("#\n")
    for sr in (".cursor/skills", ".claude/skills"):
        p = root / sr / "hydrafusion-routing-lite"
        p.mkdir(parents=True)
        (p / "SKILL.md").write_text("# hydrafusion-routing-lite\n")
    matching = root / ".claude" / "rules"
    matching.mkdir(parents=True)
    (matching / "agent-model-matching.md").write_text("# matching\n")
    fixture = root / "marketing" / "data" / "code_health"
    fixture.mkdir(parents=True)
    (fixture / "hydrafusion_routing_discipline.json").write_text(
        json.dumps(
            {
                "complete_cost_accounting": True,
                "bounded_execution": "x",
                "isolated_critique": "y",
                "fail_safe_apply": "z",
                "validated_routing": "w",
                "budget": {"subscribe_hydrafusion": False},
            }
        )
    )


class SignalTests(unittest.TestCase):
    def test_health_signals(self) -> None:
        self.assertEqual(len(HEALTH_SIGNALS), 5)


class SelectPatternTests(unittest.TestCase):
    def test_trivial_single(self) -> None:
        self.assertEqual(
            select_pattern(complexity="trivial", cheap_draft_viable=False),
            "single",
        )

    def test_medium_cascade(self) -> None:
        self.assertEqual(select_pattern(complexity="medium"), "cascade")

    def test_critical_critique(self) -> None:
        self.assertEqual(select_pattern(complexity="critical"), "critique")

    def test_isolated_review_forces_critique(self) -> None:
        self.assertEqual(
            select_pattern(complexity="low", needs_isolated_review=True),
            "critique",
        )


class ClaimTests(unittest.TestCase):
    def test_paid_saas_blocked(self) -> None:
        d = evaluate_routing_claim({"action": "subscribe_hydrafusion"})
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_paid_hydrafusion_saas")

    def test_always_frontier_blocked(self) -> None:
        d = evaluate_routing_claim({"action": "always_opus"})
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_always_frontier")

    def test_tooling_critic_blocked(self) -> None:
        d = evaluate_routing_claim(
            {"action": "run_critique", "pattern": "critique", "critic_has_tools": True}
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_tooling_critic")

    def test_unvalidated_apply_blocked(self) -> None:
        d = evaluate_routing_claim({"action": "apply_patch", "validated": False})
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_unvalidated_apply")

    def test_unbounded_execution_blocked(self) -> None:
        d = evaluate_routing_claim(
            {
                "action": "run_workflow",
                "pattern": "cascade",
                "model_available": True,
            }
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_unbounded_execution")

    def test_unaccounted_savings_blocked(self) -> None:
        d = evaluate_routing_claim({"action": "claim_savings"})
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_unaccounted_savings")

    def test_cascade_workflow_allowed(self) -> None:
        d = evaluate_routing_claim(
            {
                "action": "run_workflow",
                "pattern": "cascade",
                "model_available": True,
                "timeout_seconds": 120,
            }
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_cascade_workflow")

    def test_accounted_savings_allowed(self) -> None:
        d = evaluate_routing_claim(
            {
                "action": "claim_savings",
                "legs_accounted": ["draft", "gate", "escalate"],
                "total_cost_units": 42,
            }
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_accounted_savings")

    def test_select_pattern_action(self) -> None:
        d = evaluate_routing_claim(
            {"action": "select_pattern", "complexity": "high", "needs_isolated_review": True}
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_pattern_critique")


class PresenceTests(unittest.TestCase):
    def test_evaluate_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _scaffold(root)
            report = evaluate(root)
            self.assertTrue(report["ready"], report["blockers"])
            self.assertEqual(report["framework"], "hydrafusion-routing-lite")

    def test_evaluate_blocks_missing_matching_rule(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _scaffold(root)
            (root / ".claude" / "rules" / "agent-model-matching.md").unlink()
            report = evaluate(root)
            self.assertFalse(report["ready"])
            self.assertTrue(
                any("agent-model-matching" in b for b in report["blockers"]),
                report["blockers"],
            )


if __name__ == "__main__":
    unittest.main()
