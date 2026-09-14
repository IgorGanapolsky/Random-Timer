"""TDD: local-first hybrid router (16GB selectively local, escalate when needed)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.agent_local_first_router import (
    FLEET_MONTHLY_CAP_USD,
    LOCAL_MODEL,
    classify_task,
    evaluate_hardware_upgrade,
    evaluate_platform,
    log_run,
    private_data_policy,
    route_local_first,
    summarize_acceptance,
    template_pipeline,
)


class PlatformTests(unittest.TestCase):
    def test_local_first_allowed(self) -> None:
        d = evaluate_platform(platform="local_first_hybrid")
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_local_first_hybrid")

    def test_always_cloud_denied(self) -> None:
        d = evaluate_platform(platform="always_cloud_everything")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_cloud_only_posture")


class ClassifyTaskTests(unittest.TestCase):
    def test_extraction_is_local_lane(self) -> None:
        d = classify_task(task_type="extraction")
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "prefer_local")
        self.assertEqual(d.lane, "local")

    def test_architecture_is_cloud_lane(self) -> None:
        d = classify_task(task_type="architecture")
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "prefer_cloud")
        self.assertEqual(d.lane, "cloud")

    def test_unknown_fails(self) -> None:
        d = classify_task(task_type="vibes")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_unknown_task_type")


class PrivateDataTests(unittest.TestCase):
    def test_private_forces_local(self) -> None:
        d = private_data_policy(contains_private_data=True, allow_cloud=True)
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "force_local_private_lane")
        self.assertEqual(d.lane, "local")

    def test_non_private_defers_to_router(self) -> None:
        d = private_data_policy(contains_private_data=False, allow_cloud=True)
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_router_decide")


class RouteTests(unittest.TestCase):
    def test_private_never_escalates(self) -> None:
        d = route_local_first(
            task_type="architecture",
            contains_private_data=True,
            confidence=0.1,
            complexity=0.99,
            month_to_date_spend_usd=1.0,
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "route_local")
        self.assertEqual(d.model, LOCAL_MODEL)

    def test_hard_public_escalates_to_cloud(self) -> None:
        d = route_local_first(
            task_type="hard_debugging",
            contains_private_data=False,
            confidence=0.2,
            complexity=0.9,
            month_to_date_spend_usd=2.0,
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "route_cloud")
        self.assertNotEqual(d.model, LOCAL_MODEL)

    def test_budget_exhausted_stays_local(self) -> None:
        d = route_local_first(
            task_type="architecture",
            contains_private_data=False,
            confidence=0.1,
            complexity=0.95,
            month_to_date_spend_usd=FLEET_MONTHLY_CAP_USD,
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "route_local_budget")
        self.assertEqual(d.model, LOCAL_MODEL)

    def test_simple_coding_stays_local(self) -> None:
        d = route_local_first(
            task_type="simple_coding",
            contains_private_data=False,
            confidence=0.8,
            complexity=0.2,
            month_to_date_spend_usd=1.0,
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "route_local")


class HardwareTests(unittest.TestCase):
    def test_no_upgrade_by_default(self) -> None:
        d = evaluate_hardware_upgrade(
            local_inference_is_daily_bottleneck=False,
            privacy_requires_larger_local=False,
            paid_work_blocked_by_ram=False,
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "keep_16gb_optimize_workflow")

    def test_upgrade_only_when_recurring_bottleneck(self) -> None:
        d = evaluate_hardware_upgrade(
            local_inference_is_daily_bottleneck=True,
            privacy_requires_larger_local=True,
            paid_work_blocked_by_ram=True,
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "consider_32gb_unified")


class InstrumentTests(unittest.TestCase):
    def test_log_and_summarize_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "runs.jsonl"
            log_run(
                path=path,
                model="local/hermes-cheap",
                task_type="extraction",
                tokens=100,
                cost_usd=0.0,
                latency_ms=200,
                accepted=True,
            )
            log_run(
                path=path,
                model="cloud/frontier",
                task_type="architecture",
                tokens=2000,
                cost_usd=0.05,
                latency_ms=3000,
                accepted=False,
            )
            summary = summarize_acceptance(path=path)
        self.assertEqual(summary["runs"], 2)
        self.assertAlmostEqual(summary["acceptance_rate"], 0.5)
        self.assertAlmostEqual(summary["total_cost_usd"], 0.05)


class TemplateTests(unittest.TestCase):
    def test_template_pipeline_private_summary(self) -> None:
        report = template_pipeline(
            task_type="private_summary",
            contains_private_data=True,
            confidence=0.7,
            complexity=0.3,
            month_to_date_spend_usd=1.0,
            human_approval_required=True,
        )
        self.assertTrue(report["ok"])
        self.assertEqual(report["route"]["action"], "route_local")
        self.assertEqual(report["steps"][0], "classify")
        self.assertIn("human_approval", report["steps"])


if __name__ == "__main__":
    unittest.main()
