"""TDD: Trust Reliability Loop lite — scope, eval, tiered inference, recommend-first."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.trust_reliability_loop_gate import (
    HEALTH_SIGNALS,
    INFERENCE_TIERS,
    evaluate,
    evaluate_ops_claim,
    select_inference_tier,
)


def _scaffold(root: Path) -> None:
    (root / "docs").mkdir()
    (root / "docs" / "TRUST_RELIABILITY_LOOP.md").write_text(
        "\n".join(
            [
                "# Trust Reliability Loop",
                "narrow workflow scope",
                "eval-first precision recall",
                "tiered inference ladder",
                "recommend-first read-only",
                "progressive autonomy",
                "explicit editable memory",
                "alert precision over coverage",
                "cost per retained",
                "event-driven not continuous",
                "provenance source links",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (root / "scripts").mkdir()
    (root / "scripts" / "trust_reliability_loop_gate.py").write_text("#\n")
    for sr in (".cursor/skills", ".claude/skills"):
        p = root / sr / "trust-reliability-loop-lite"
        p.mkdir(parents=True)
        (p / "SKILL.md").write_text("# trust-reliability-loop-lite\n")
    fixture = root / "marketing" / "data" / "code_health"
    fixture.mkdir(parents=True)
    (fixture / "trust_reliability_loop_discipline.json").write_text(
        json.dumps(
            {
                "narrow_workflow_scope": True,
                "eval_first_logging": True,
                "tiered_inference": True,
                "recommend_first": True,
                "progressive_autonomy": True,
                "explicit_editable_memory": True,
                "alert_precision_over_coverage": True,
                "cost_per_retained": True,
                "event_driven": True,
                "budget": {"continuous_always_on_reasoning": False},
            }
        )
    )
    workflows = root / "marketing" / "data" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ops_daily_brief.json").write_text(
        json.dumps(
            {
                "workflow_id": "ops_daily_brief",
                "owner": "CTO",
                "metric": "actionable_alert_precision",
                "mode": "recommend_first",
            }
        )
    )


class SignalTests(unittest.TestCase):
    def test_health_signals(self) -> None:
        self.assertGreaterEqual(len(HEALTH_SIGNALS), 7)

    def test_inference_tiers_ladder(self) -> None:
        self.assertEqual(
            list(INFERENCE_TIERS),
            ["rules", "classify", "extract", "premium", "confirm"],
        )


class SelectTierTests(unittest.TestCase):
    def test_metadata_only_rules(self) -> None:
        self.assertEqual(
            select_inference_tier(
                ambiguity=0.0, consequential=False, needs_synthesis=False
            ),
            "rules",
        )

    def test_cheap_classify(self) -> None:
        self.assertEqual(
            select_inference_tier(
                ambiguity=0.2, consequential=False, needs_synthesis=False
            ),
            "classify",
        )

    def test_extract_for_structured(self) -> None:
        self.assertEqual(
            select_inference_tier(
                ambiguity=0.4,
                consequential=False,
                needs_synthesis=False,
                needs_structured_fields=True,
            ),
            "extract",
        )

    def test_premium_for_ambiguous(self) -> None:
        self.assertEqual(
            select_inference_tier(
                ambiguity=0.8, consequential=False, needs_synthesis=True
            ),
            "premium",
        )

    def test_confirm_for_consequential(self) -> None:
        self.assertEqual(
            select_inference_tier(
                ambiguity=0.1, consequential=True, needs_synthesis=False
            ),
            "confirm",
        )


class ClaimTests(unittest.TestCase):
    def test_continuous_reasoning_blocked(self) -> None:
        d = evaluate_ops_claim({"action": "run_continuous_agent"})
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_continuous_reasoning")

    def test_autonomous_external_write_blocked(self) -> None:
        d = evaluate_ops_claim(
            {
                "action": "send_message",
                "user_confirmed": False,
                "autonomy_grant": None,
            }
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_unconfirmed_external_action")

    def test_open_ended_agent_blocked(self) -> None:
        d = evaluate_ops_claim({"action": "expand_general_purpose_chat"})
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_open_ended_scope")

    def test_alert_without_eval_log_blocked(self) -> None:
        d = evaluate_ops_claim(
            {
                "action": "emit_alert",
                "workflow_id": "paywall_failure_alert",
                "eval_logged": False,
            }
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_alert_without_eval")

    def test_alert_without_provenance_blocked(self) -> None:
        d = evaluate_ops_claim(
            {
                "action": "emit_alert",
                "workflow_id": "paywall_failure_alert",
                "eval_logged": True,
                "source_url": "",
            }
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_alert_without_provenance")

    def test_alert_over_budget_blocked(self) -> None:
        d = evaluate_ops_claim(
            {
                "action": "emit_alert",
                "workflow_id": "paywall_failure_alert",
                "eval_logged": True,
                "source_url": "https://example.test/run/1",
                "alert_budget_remaining": 0,
                "time_sensitive": False,
            }
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_alert_over_budget")

    def test_cost_claim_without_retained_metric_blocked(self) -> None:
        d = evaluate_ops_claim({"action": "claim_unit_economics", "cost_units": 1})
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_cost_without_retained_metric")

    def test_recommend_first_allowed(self) -> None:
        d = evaluate_ops_claim(
            {
                "action": "recommend",
                "workflow_id": "ops_daily_brief",
                "eval_logged": True,
                "source_url": "https://example.test/brief/1",
                "mode": "recommend_first",
            }
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_recommend_first")

    def test_confirmed_external_action_allowed(self) -> None:
        d = evaluate_ops_claim(
            {
                "action": "send_message",
                "user_confirmed": True,
                "autonomy_grant": "draft_school_replies",
                "eval_logged": True,
                "source_url": "https://example.test/msg/1",
            }
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_progressive_autonomy_action")

    def test_precision_claim_allowed(self) -> None:
        d = evaluate_ops_claim(
            {
                "action": "claim_alert_precision",
                "workflow_id": "paywall_failure_alert",
                "true_positives": 8,
                "false_positives": 2,
                "eval_logged": True,
            }
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_precision_claim")

    def test_unit_economics_allowed(self) -> None:
        d = evaluate_ops_claim(
            {
                "action": "claim_unit_economics",
                "cost_units": 3.5,
                "retained_users": 10,
                "cost_per_retained": 0.35,
                "window_days": 7,
            }
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_unit_economics_claim")


class PresenceTests(unittest.TestCase):
    def test_evaluate_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _scaffold(root)
            report = evaluate(root)
            self.assertTrue(report["ready"], report["blockers"])
            self.assertEqual(report["framework"], "trust-reliability-loop-lite")

    def test_evaluate_missing_doc(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _scaffold(root)
            (root / "docs" / "TRUST_RELIABILITY_LOOP.md").unlink()
            report = evaluate(root)
            self.assertFalse(report["ready"])
            self.assertTrue(any("TRUST_RELIABILITY_LOOP" in b for b in report["blockers"]))


if __name__ == "__main__":
    unittest.main()
