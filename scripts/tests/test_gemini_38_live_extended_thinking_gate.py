"""TDD: Gemini 3.8 Live + Extended Thinking lite."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.gemini_38_live_extended_thinking_gate import (
    HEALTH_SIGNALS,
    evaluate,
    evaluate_live_claim,
    narration_plan,
    select_live_mode,
)


def _scaffold(root: Path) -> None:
    (root / "docs").mkdir()
    (root / "docs" / "GEMINI_38_LIVE_EXTENDED_THINKING.md").write_text(
        "\n".join(
            [
                "# Gemini 3.8 Live",
                "3.8 live extended thinking dual-mode",
                "background tools while speaking",
                "progress narration early verbal",
                "visual grounding",
                "barge-in friendly",
                "synthid watermark",
                "budget gated live api voice",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (root / "scripts").mkdir()
    (root / "scripts" / "gemini_38_live_extended_thinking_gate.py").write_text("#\n")
    for sr in (".cursor/skills", ".claude/skills"):
        p = root / sr / "gemini-38-live-extended-thinking-lite"
        p.mkdir(parents=True)
        (p / "SKILL.md").write_text("# gemini-38-live-extended-thinking-lite\n")
    fixture = root / "marketing" / "data" / "code_health"
    fixture.mkdir(parents=True)
    (fixture / "gemini_38_live_extended_thinking_discipline.json").write_text(
        json.dumps(
            {
                "dual_mode_live_vs_extended_thinking": True,
                "early_verbal_ack_cues": True,
                "live_progress_narration": True,
                "background_tools_while_speaking": True,
                "visual_grounding_when_available": True,
                "barge_in_friendly": True,
                "synthid_audio_watermark_awareness": True,
                "budget_gated_live_api": True,
                "prefer_free_or_subscription_surfaces": True,
                "budget": {"default_to_paid_live_api": False},
            }
        )
    )


class SignalTests(unittest.TestCase):
    def test_health_signals(self) -> None:
        self.assertGreaterEqual(len(HEALTH_SIGNALS), 8)


class RouteTests(unittest.TestCase):
    def test_complex_routes_extended(self) -> None:
        self.assertEqual(
            select_live_mode(complexity="multi_step", cost_sensitive=True),
            "extended_thinking",
        )

    def test_simple_cost_sensitive_is_live(self) -> None:
        self.assertEqual(select_live_mode(complexity="simple"), "live")

    def test_narration_extended(self) -> None:
        plan = narration_plan(mode="extended_thinking", task="book flight")
        self.assertTrue(plan["progress_narration"])
        self.assertTrue(plan["speak_while_reasoning"])


class ClaimTests(unittest.TestCase):
    def test_paid_default_blocked(self) -> None:
        d = evaluate_live_claim({"action": "default_paid_live_api"})
        self.assertFalse(d.ok)

    def test_freeze_blocked(self) -> None:
        d = evaluate_live_claim({"action": "freeze_until_tools_done"})
        self.assertFalse(d.ok)

    def test_select_mode(self) -> None:
        d = evaluate_live_claim(
            {"action": "select_mode", "complexity": "agentic", "cost_sensitive": True}
        )
        self.assertTrue(d.ok)
        self.assertIn("extended_thinking", d.action)

    def test_live_api_needs_budget(self) -> None:
        d = evaluate_live_claim({"action": "use_live_api", "budget_remaining_usd": 0})
        self.assertFalse(d.ok)

    def test_synthid_required(self) -> None:
        d = evaluate_live_claim({"action": "emit_ai_audio"})
        self.assertFalse(d.ok)
        d2 = evaluate_live_claim({"action": "emit_ai_audio", "synthid_aware": True})
        self.assertTrue(d2.ok)


class PresenceTests(unittest.TestCase):
    def test_evaluate_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _scaffold(root)
            report = evaluate(root)
            self.assertTrue(report["ready"], report["blockers"])
            self.assertIn("blog.google", report["source"])


if __name__ == "__main__":
    unittest.main()
