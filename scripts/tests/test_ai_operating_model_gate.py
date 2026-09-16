"""TDD: AI Operating Model lite gate."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.ai_operating_model_gate import (
    HEALTH_SIGNALS,
    compute_roi,
    evaluate,
    evaluate_operating_model_claim,
    score_workflow_priority,
)


def _scaffold(root: Path) -> None:
    (root / "docs").mkdir()
    (root / "docs" / "AI_OPERATING_MODEL.md").write_text(
        "\n".join(
            [
                "# AI Operating Model",
                "operating-model change not tool rollout",
                "baseline before ai",
                "rebuild sop ai-native",
                "enablement before licenses",
                "weekly ritual",
                "measure behavior not logins",
                "roi includes total cost",
                "30-day pilot",
                "intake to delivery",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (root / "scripts").mkdir()
    (root / "scripts" / "ai_operating_model_gate.py").write_text("#\n")
    for sr in (".cursor/skills", ".claude/skills"):
        p = root / sr / "ai-operating-model-lite"
        p.mkdir(parents=True)
        (p / "SKILL.md").write_text("# ai-operating-model-lite\n")
    fixture = root / "marketing" / "data" / "code_health"
    fixture.mkdir(parents=True)
    (fixture / "ai_operating_model_discipline.json").write_text(
        json.dumps(
            {
                "operating_model_not_tool_rollout": True,
                "one_workflow_clear_owner": True,
                "baseline_before_ai": True,
                "rebuild_ai_native_sop": True,
                "enablement_before_tool_spend": True,
                "weekly_ai_operating_ritual": True,
                "measure_behavior_not_logins": True,
                "roi_includes_total_cost": True,
                "thirty_day_pilot_then_expand": True,
                "budget": {"prefer_enablement_over_licenses": True},
                "reference_pilot": {"workflow": "intake_to_delivery"},
            }
        )
    )


class ClaimTests(unittest.TestCase):
    def test_health_signals(self) -> None:
        self.assertGreaterEqual(len(HEALTH_SIGNALS), 8)

    def test_license_first_blocked(self) -> None:
        d = evaluate_operating_model_claim({"action": "buy_more_licenses_first"})
        self.assertFalse(d.ok)

    def test_prompt_count_blocked(self) -> None:
        d = evaluate_operating_model_claim({"action": "reward_prompt_count"})
        self.assertFalse(d.ok)

    def test_pick_workflow_needs_baseline(self) -> None:
        d = evaluate_operating_model_claim(
            {"action": "pick_workflow", "owner": "CTO", "workflow": "intake_to_delivery"}
        )
        self.assertFalse(d.ok)

    def test_pick_workflow_ok(self) -> None:
        d = evaluate_operating_model_claim(
            {
                "action": "pick_workflow",
                "owner": "CTO",
                "workflow": "intake_to_delivery",
                "baseline_captured": True,
            }
        )
        self.assertTrue(d.ok)

    def test_sop_incomplete(self) -> None:
        d = evaluate_operating_model_claim({"action": "rebuild_sop", "human_inputs": True})
        self.assertFalse(d.ok)

    def test_roi_requires_full_cost(self) -> None:
        d = evaluate_operating_model_claim(
            {
                "action": "compute_roi",
                "financial_value": 100,
                "total_cost": 20,
            }
        )
        self.assertFalse(d.ok)

    def test_roi_ok(self) -> None:
        d = evaluate_operating_model_claim(
            {
                "action": "compute_roi",
                "financial_value": 100,
                "total_cost": 20,
                "includes_labor_training_review": True,
            }
        )
        self.assertTrue(d.ok)
        self.assertIn("roi=4", d.reason)

    def test_compute_roi_math(self) -> None:
        r = compute_roi(financial_value=120, total_cost=20)
        self.assertTrue(r["ok"])
        self.assertEqual(r["roi"], 5.0)

    def test_priority_needs_manager(self) -> None:
        scored = score_workflow_priority(
            {
                "volume_score": 3,
                "labor_cost_score": 3,
                "low_error_after_qa": True,
                "fast_deploy": True,
                "manager_enforces": False,
            }
        )
        self.assertFalse(scored["pursue"])


class PresenceTests(unittest.TestCase):
    def test_evaluate_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _scaffold(root)
            report = evaluate(root)
            self.assertTrue(report["ready"], report["blockers"])


if __name__ == "__main__":
    unittest.main()
