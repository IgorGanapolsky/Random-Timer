"""TDD: agent cost + reliability audit (lazy agents, budget reckoning, DuckDB/SQLite inspect)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.agent_cost_reliability_audit import (
    FLEET_MONTHLY_CAP_USD,
    audit_workflow,
    classify_laziness,
    evaluate_automation_roi,
    evaluate_platform,
    inspect_json_rows_with_sql,
    retry_policy,
    score_run_completion,
    summarize_tool_trace,
)


class PlatformTests(unittest.TestCase):
    def test_local_audit_allowed(self) -> None:
        d = evaluate_platform(platform="local_cost_reliability_audit")
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_local_audit")

    def test_managed_aws_agent_stack_denied_under_cap(self) -> None:
        d = evaluate_platform(platform="aws_bedrock_agents_managed")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_paid_agent_infra")


class LazyAgentTests(unittest.TestCase):
    def test_incomplete_without_acceptance_is_lazy(self) -> None:
        label = classify_laziness(
            acceptance_met=False,
            evidence_paths=(),
            stopped_at_diagnosis=False,
            asked_human_to_run_commands=False,
        )
        self.assertEqual(label, "incomplete_acceptance")

    def test_diagnosis_only_is_lazy(self) -> None:
        label = classify_laziness(
            acceptance_met=False,
            evidence_paths=("tmp/note.txt",),
            stopped_at_diagnosis=True,
            asked_human_to_run_commands=False,
        )
        self.assertEqual(label, "stopped_at_diagnosis")

    def test_babysitting_escalation_is_lazy(self) -> None:
        label = classify_laziness(
            acceptance_met=False,
            evidence_paths=(),
            stopped_at_diagnosis=False,
            asked_human_to_run_commands=True,
        )
        self.assertEqual(label, "babysitting_escalation")

    def test_complete_with_evidence_is_not_lazy(self) -> None:
        label = classify_laziness(
            acceptance_met=True,
            evidence_paths=("marketing/data/proof.json",),
            stopped_at_diagnosis=False,
            asked_human_to_run_commands=False,
        )
        self.assertEqual(label, "ok")

    def test_score_run_requires_criteria_and_evidence(self) -> None:
        bad = score_run_completion(
            acceptance_criteria=("banner_cleared", "json_updated"),
            criteria_met=("banner_cleared",),
            evidence_paths=(),
            tool_calls=3,
        )
        self.assertFalse(bad.ok)
        self.assertEqual(bad.action, "block_incomplete_run")

        good = score_run_completion(
            acceptance_criteria=("banner_cleared", "json_updated"),
            criteria_met=("banner_cleared", "json_updated"),
            evidence_paths=("marketing/data/android_developer_verification.json",),
            tool_calls=5,
        )
        self.assertTrue(good.ok)
        self.assertEqual(good.action, "allow_complete_run")
        self.assertAlmostEqual(good.completion_rate, 1.0)


class RetryPolicyTests(unittest.TestCase):
    def test_retry_then_escalate_only_on_exception(self) -> None:
        first = retry_policy(attempt=1, max_attempts=3, is_exception=False)
        self.assertEqual(first.action, "retry")
        last = retry_policy(attempt=3, max_attempts=3, is_exception=False)
        self.assertEqual(last.action, "fail_closed")
        escalate = retry_policy(attempt=2, max_attempts=3, is_exception=True)
        self.assertEqual(escalate.action, "escalate_human")


class BudgetReckoningTests(unittest.TestCase):
    def test_fleet_cap_constant(self) -> None:
        self.assertEqual(FLEET_MONTHLY_CAP_USD, 20.0)

    def test_high_frequency_clear_savings_passes(self) -> None:
        d = evaluate_automation_roi(
            monthly_frequency=40,
            human_minutes_per_run=30,
            human_usd_per_hour=50.0,
            model_usd_per_run=0.05,
            review_minutes_per_run=5,
            month_to_date_spend_usd=2.0,
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "automate")
        self.assertGreater(d.monthly_net_usd, 0)

    def test_rare_expensive_model_fails(self) -> None:
        d = evaluate_automation_roi(
            monthly_frequency=1,
            human_minutes_per_run=5,
            human_usd_per_hour=50.0,
            model_usd_per_run=3.0,
            review_minutes_per_run=10,
            month_to_date_spend_usd=18.0,
        )
        self.assertFalse(d.ok)
        self.assertIn(d.action, {"block_negative_roi", "block_budget_cap"})


class InspectSqlTests(unittest.TestCase):
    def test_inspect_json_rows_before_model(self) -> None:
        rows = [
            {"event": "paywall_viewed", "count": 10},
            {"event": "paywall_purchase_success", "count": 1},
            {"event": "timer_completed", "count": 50},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.json"
            path.write_text(json.dumps(rows), encoding="utf-8")
            result = inspect_json_rows_with_sql(
                path=path,
                sql="SELECT event, count FROM events WHERE count >= 10 ORDER BY count DESC",
            )
        self.assertTrue(result.ok)
        self.assertIn(result.engine, {"sqlite", "duckdb"})
        self.assertEqual(len(result.rows), 2)
        self.assertEqual(result.rows[0]["event"], "timer_completed")


class TraceSummaryTests(unittest.TestCase):
    def test_summarize_tool_trace_cost_per_success(self) -> None:
        summary = summarize_tool_trace(
            runs=(
                {"ok": True, "usd": 0.02, "failure": None},
                {"ok": False, "usd": 0.01, "failure": "tool_timeout"},
                {"ok": True, "usd": 0.03, "failure": None},
                {"ok": False, "usd": 0.02, "failure": "tool_timeout"},
                {"ok": False, "usd": 0.01, "failure": "missing_evidence"},
            )
        )
        self.assertEqual(summary.attempts, 5)
        self.assertEqual(summary.successes, 2)
        self.assertAlmostEqual(summary.completion_rate, 0.4)
        self.assertAlmostEqual(summary.cost_per_success_usd, 0.045)
        self.assertEqual(summary.top_failure, "tool_timeout")


class AuditWorkflowTests(unittest.TestCase):
    def test_audit_blocks_lazy_claim(self) -> None:
        report = audit_workflow(
            platform="local_cost_reliability_audit",
            acceptance_criteria=("pr_merged",),
            criteria_met=(),
            evidence_paths=(),
            tool_calls=2,
            stopped_at_diagnosis=True,
            asked_human_to_run_commands=False,
            monthly_frequency=10,
            human_minutes_per_run=20,
            human_usd_per_hour=40.0,
            model_usd_per_run=0.1,
            review_minutes_per_run=3,
            month_to_date_spend_usd=1.0,
            runs=({"ok": False, "usd": 0.1, "failure": "stopped_at_diagnosis"},),
        )
        self.assertFalse(report["ok"])
        self.assertEqual(report["laziness"], "stopped_at_diagnosis")

    def test_audit_passes_complete_economic_run(self) -> None:
        report = audit_workflow(
            platform="local_cost_reliability_audit",
            acceptance_criteria=("pr_merged", "ci_green"),
            criteria_met=("pr_merged", "ci_green"),
            evidence_paths=("marketing/data/agent_cost_reliability_audit.json",),
            tool_calls=8,
            stopped_at_diagnosis=False,
            asked_human_to_run_commands=False,
            monthly_frequency=20,
            human_minutes_per_run=25,
            human_usd_per_hour=50.0,
            model_usd_per_run=0.08,
            review_minutes_per_run=4,
            month_to_date_spend_usd=3.0,
            runs=(
                {"ok": True, "usd": 0.08, "failure": None},
                {"ok": True, "usd": 0.07, "failure": None},
            ),
        )
        self.assertTrue(report["ok"])
        self.assertEqual(report["laziness"], "ok")
        self.assertEqual(report["completion"]["action"], "allow_complete_run")


if __name__ == "__main__":
    unittest.main()
