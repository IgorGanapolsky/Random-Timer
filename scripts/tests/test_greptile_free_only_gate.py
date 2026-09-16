"""TDD: Greptile free-only gate."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.greptile_free_only_gate import (
    HEALTH_SIGNALS,
    evaluate,
    evaluate_greptile_claim,
)


def _scaffold(root: Path) -> None:
    (root / "docs").mkdir()
    (root / "docs" / "GREPTILE_FREE_ONLY.md").write_text(
        "\n".join(
            [
                "# Greptile free-only",
                "never pay free tier",
                "no payment method",
                "private repos disabled",
                "50 stars oss grant",
                "needs-greptile-review label",
                "no flex paid credits",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (root / "scripts").mkdir()
    (root / "scripts" / "greptile_free_only_gate.py").write_text("#\n")
    for sr in (".cursor/skills", ".claude/skills"):
        p = root / sr / "greptile-free-only"
        p.mkdir(parents=True)
        (p / "SKILL.md").write_text("# greptile-free-only\n")
    fixture = root / "marketing" / "data" / "code_health"
    fixture.mkdir(parents=True)
    (fixture / "greptile_free_only_discipline.json").write_text(
        json.dumps(
            {
                "free_tier_only": True,
                "no_payment_method": True,
                "disable_reviews_on_private_repos": True,
                "disable_reviews_on_public_under_50_stars": True,
                "label_filter_needs_greptile_review": True,
                "no_flex_paid_credits": True,
                "oss_grant_50_stars_osi_only": True,
                "budget": {"paid_greptile": False},
            }
        )
    )


class ClaimTests(unittest.TestCase):
    def test_health_signals(self) -> None:
        self.assertGreaterEqual(len(HEALTH_SIGNALS), 6)

    def test_payment_blocked(self) -> None:
        d = evaluate_greptile_claim({"action": "add_payment_method"})
        self.assertFalse(d.ok)

    def test_private_blocked(self) -> None:
        d = evaluate_greptile_claim({"action": "enable_reviews_private_repo"})
        self.assertFalse(d.ok)

    def test_low_stars_blocked(self) -> None:
        d = evaluate_greptile_claim(
            {"action": "review_public_under_50_stars", "stars": 12}
        )
        self.assertFalse(d.ok)

    def test_free_ok(self) -> None:
        d = evaluate_greptile_claim(
            {"action": "use_free_only", "payment_method_present": False}
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
