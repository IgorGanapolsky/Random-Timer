"""TDD: AI tool bake-off — classify work, score candidates, ROI gate, productionize."""

from __future__ import annotations

import unittest

from scripts.agent_tool_bakeoff import (
    FLEET_MONTHLY_CAP_USD,
    MIN_HOURS_SAVED_PER_MONTH,
    bakeoff_compare,
    classify_work,
    evaluate_platform,
    evaluate_roi_gate,
    plan_bakeoff,
    productionize_ready,
    score_candidate,
)


class PlatformTests(unittest.TestCase):
    def test_local_bakeoff_allowed(self) -> None:
        d = evaluate_platform(platform="local_tool_bakeoff")
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_local_tool_bakeoff")

    def test_unbounded_tool_shopping_denied(self) -> None:
        d = evaluate_platform(platform="unbounded_tool_shopping")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_tool_shopping")


class ClassifyWorkTests(unittest.TestCase):
    def test_known_kinds_pass(self) -> None:
        for kind in ("reasoning", "coding", "research", "computer_use", "automation"):
            d = classify_work(kind=kind)
            self.assertTrue(d.ok, kind)
            self.assertEqual(d.action, "allow_work_class")

    def test_unknown_kind_fails(self) -> None:
        d = classify_work(kind="vibes")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_unknown_work_class")


class ScoreCandidateTests(unittest.TestCase):
    def test_usable_repeatable_candidate_scores(self) -> None:
        d = score_candidate(
            setup_minutes=20,
            usable_output_rate=0.8,
            human_correction_minutes=15,
            cost_usd_per_task=0.05,
            safely_repeatable=True,
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "candidate_viable")
        self.assertGreater(d.score, 0)

    def test_low_accuracy_fails(self) -> None:
        d = score_candidate(
            setup_minutes=10,
            usable_output_rate=0.2,
            human_correction_minutes=60,
            cost_usd_per_task=0.01,
            safely_repeatable=True,
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_low_usable_output")


class RoiGateTests(unittest.TestCase):
    def test_fleet_cap_constant(self) -> None:
        self.assertEqual(FLEET_MONTHLY_CAP_USD, 20.0)
        self.assertEqual(MIN_HOURS_SAVED_PER_MONTH, 2.0)

    def test_hours_saved_clears_gate(self) -> None:
        d = evaluate_roi_gate(
            hours_saved_per_month=3.0,
            quality_or_speed_improved=False,
            enables_chargeable_offer=False,
            month_to_date_spend_usd=1.0,
            incremental_tool_usd_per_month=0.5,
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "keep_winner")

    def test_under_hours_without_other_value_fails(self) -> None:
        d = evaluate_roi_gate(
            hours_saved_per_month=1.0,
            quality_or_speed_improved=False,
            enables_chargeable_offer=False,
            month_to_date_spend_usd=1.0,
            incremental_tool_usd_per_month=0.0,
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_roi_gate")

    def test_over_budget_fails(self) -> None:
        d = evaluate_roi_gate(
            hours_saved_per_month=10.0,
            quality_or_speed_improved=True,
            enables_chargeable_offer=True,
            month_to_date_spend_usd=19.5,
            incremental_tool_usd_per_month=2.0,
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_budget_cap")


class ProductionizeTests(unittest.TestCase):
    def test_incomplete_checklist_fails(self) -> None:
        d = productionize_ready(
            has_prompt_template=True,
            has_structured_io=True,
            has_output_validation=False,
            has_run_logging=True,
            requires_human_approval=True,
            has_manual_fallback=True,
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_not_production_ready")

    def test_complete_checklist_passes(self) -> None:
        d = productionize_ready(
            has_prompt_template=True,
            has_structured_io=True,
            has_output_validation=True,
            has_run_logging=True,
            requires_human_approval=True,
            has_manual_fallback=True,
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_productionize")


class BakeoffCompareTests(unittest.TestCase):
    def test_higher_score_wins(self) -> None:
        winner = bakeoff_compare(
            a={
                "id": "cursor",
                "setup_minutes": 15,
                "usable_output_rate": 0.85,
                "human_correction_minutes": 10,
                "cost_usd_per_task": 0.08,
                "safely_repeatable": True,
            },
            b={
                "id": "generic_chat",
                "setup_minutes": 5,
                "usable_output_rate": 0.4,
                "human_correction_minutes": 45,
                "cost_usd_per_task": 0.02,
                "safely_repeatable": False,
            },
        )
        self.assertEqual(winner["winner_id"], "cursor")
        self.assertTrue(winner["a"]["ok"])


class PlanBakeoffTests(unittest.TestCase):
    def test_plan_blocks_shopping_without_bottleneck(self) -> None:
        report = plan_bakeoff(
            platform="local_tool_bakeoff",
            bottleneck="",
            work_kind="coding",
            a={
                "id": "a",
                "setup_minutes": 10,
                "usable_output_rate": 0.9,
                "human_correction_minutes": 5,
                "cost_usd_per_task": 0.05,
                "safely_repeatable": True,
            },
            b={
                "id": "b",
                "setup_minutes": 20,
                "usable_output_rate": 0.7,
                "human_correction_minutes": 15,
                "cost_usd_per_task": 0.04,
                "safely_repeatable": True,
            },
            hours_saved_per_month=4.0,
            quality_or_speed_improved=True,
            enables_chargeable_offer=False,
            month_to_date_spend_usd=2.0,
            incremental_tool_usd_per_month=0.0,
            has_prompt_template=True,
            has_structured_io=True,
            has_output_validation=True,
            has_run_logging=True,
            requires_human_approval=True,
            has_manual_fallback=True,
        )
        self.assertFalse(report["ok"])
        self.assertEqual(report["bottleneck"]["action"], "block_missing_bottleneck")

    def test_plan_passes_bounded_coding_bakeoff(self) -> None:
        report = plan_bakeoff(
            platform="local_tool_bakeoff",
            bottleneck="bounded_github_issue_to_merge_ready_pr",
            work_kind="coding",
            a={
                "id": "cursor_agent",
                "setup_minutes": 15,
                "usable_output_rate": 0.85,
                "human_correction_minutes": 12,
                "cost_usd_per_task": 0.1,
                "safely_repeatable": True,
            },
            b={
                "id": "paste_into_chat",
                "setup_minutes": 5,
                "usable_output_rate": 0.35,
                "human_correction_minutes": 50,
                "cost_usd_per_task": 0.02,
                "safely_repeatable": False,
            },
            hours_saved_per_month=5.0,
            quality_or_speed_improved=True,
            enables_chargeable_offer=False,
            month_to_date_spend_usd=2.0,
            incremental_tool_usd_per_month=0.0,
            has_prompt_template=True,
            has_structured_io=True,
            has_output_validation=True,
            has_run_logging=True,
            requires_human_approval=True,
            has_manual_fallback=True,
        )
        self.assertTrue(report["ok"])
        self.assertEqual(report["bakeoff"]["winner_id"], "cursor_agent")
        self.assertEqual(report["roi"]["action"], "keep_winner")
        self.assertEqual(report["productionize"]["action"], "allow_productionize")


if __name__ == "__main__":
    unittest.main()
