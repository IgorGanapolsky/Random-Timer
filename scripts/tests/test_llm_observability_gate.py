"""TDD: LLM Observability lite gate."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.llm_observability_gate import (
    HEALTH_SIGNALS,
    evaluate,
    evaluate_llm_obs_claim,
)


def _scaffold(root: Path) -> None:
    (root / "docs").mkdir()
    (root / "docs" / "LLM_OBSERVABILITY.md").write_text(
        "\n".join(
            [
                "# LLM Observability",
                "latency token prompt injection pii quality",
                "trace cost budget datadog posthog",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (root / "scripts").mkdir()
    (root / "scripts" / "llm_observability_gate.py").write_text("#\n")
    for sr in (".cursor/skills", ".claude/skills"):
        p = root / sr / "llm-observability-lite"
        p.mkdir(parents=True)
        (p / "SKILL.md").write_text("# llm-observability-lite\n")
    fixture = root / "marketing" / "data" / "code_health"
    fixture.mkdir(parents=True)
    (fixture / "llm_observability_discipline.json").write_text(
        json.dumps(
            {
                "operational_perf_errors_latency_tokens": True,
                "prompt_injection_and_security_signals": True,
                "pii_scrub_or_detect": True,
                "functional_quality_evals": True,
                "end_to_end_chain_tracing": True,
                "cost_per_query_visibility": True,
                "alert_on_budget_and_errors": True,
                "prefer_free_local_or_posthog": True,
                "budget_gated_datadog_saas": True,
                "budget": {"default_to_paid_datadog": False},
            }
        )
    )


class ClaimTests(unittest.TestCase):
    def test_health_signals(self) -> None:
        self.assertGreaterEqual(len(HEALTH_SIGNALS), 8)

    def test_paid_datadog_blocked(self) -> None:
        d = evaluate_llm_obs_claim({"action": "default_paid_datadog"})
        self.assertFalse(d.ok)

    def test_ops_incomplete(self) -> None:
        d = evaluate_llm_obs_claim({"action": "claim_monitored", "errors_tracked": True})
        self.assertFalse(d.ok)

    def test_ops_ok(self) -> None:
        d = evaluate_llm_obs_claim(
            {
                "action": "claim_monitored",
                "errors_tracked": True,
                "latency_tracked": True,
                "tokens_or_cost_tracked": True,
            }
        )
        self.assertTrue(d.ok)

    def test_trace_required(self) -> None:
        d = evaluate_llm_obs_claim({"action": "trace"})
        self.assertFalse(d.ok)

    def test_cost_alert_ok(self) -> None:
        d = evaluate_llm_obs_claim(
            {
                "action": "cost_alert",
                "budget_remaining_usd": 12.0,
                "token_or_cost_metered": True,
            }
        )
        self.assertTrue(d.ok)


class PresenceTests(unittest.TestCase):
    def test_evaluate_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _scaffold(root)
            report = evaluate(root)
            self.assertTrue(report["ready"], report["blockers"])


if __name__ == "__main__":
    unittest.main()
