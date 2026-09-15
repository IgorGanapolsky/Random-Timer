"""TDD for InfoQ Rohrer value-center / VSM fitness (agency + coherence)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.value_center_gate import (
    VSM_QUESTIONS,
    classify_dependency,
    evaluate,
    evaluate_charter,
    evaluate_vsm_answers,
)


class VsmQuestionContractTests(unittest.TestCase):
    def test_five_questions_match_rohrer(self) -> None:
        self.assertEqual(
            list(VSM_QUESTIONS),
            [
                "what_value",
                "how_coordinate",
                "how_fit_together",
                "whats_out_there",
                "who_are_we",
            ],
        )


class CharterTests(unittest.TestCase):
    def test_charter_requires_north_star_and_agency_coherence(self) -> None:
        bad = evaluate_charter(
            {
                "name": "timer team",
                "value": "ship features",
                "mode": "autonomous",
            }
        )
        self.assertFalse(bad.ok)
        self.assertEqual(bad.action, "block_product_not_value")

        good = evaluate_charter(
            {
                "name": "random-timer value center",
                "value": "Grow WQTU and paywall attempt→success toward $100/day after-tax",
                "mode": "agency_and_coherence",
                "north_star": "WQTU",
                "coordination": "PR gates + internal-signoff SHA binding",
            }
        )
        self.assertTrue(good.ok)
        self.assertEqual(good.action, "allow_value_center")


class VsmAnswerTests(unittest.TestCase):
    def test_incomplete_answers_fail(self) -> None:
        d = evaluate_vsm_answers(
            {
                "what_value": "WQTU",
                "how_coordinate": "PRs",
            }
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_incomplete_vsm")

    def test_complete_answers_pass(self) -> None:
        d = evaluate_vsm_answers(
            {
                "what_value": "WQTU >=3 timer_completed / 7d",
                "how_coordinate": "GitHub Actions env signoffs + PR checks",
                "how_fit_together": "Align store ship to WQTU funnel, not vanity installs",
                "whats_out_there": "App Review lag; Play CDN lag; $20/mo spend cap",
                "who_are_we": "CTO value center for Random Tactical Timer",
            }
        )
        self.assertTrue(d.ok)


class DependencyClassificationTests(unittest.TestCase):
    def test_essential_vs_accidental(self) -> None:
        self.assertEqual(
            classify_dependency("Play Billing catalog for Pro unlock"),
            "essential",
        )
        self.assertEqual(
            classify_dependency("Full BMAD Method plugin install for one SPEC"),
            "accidental",
        )
        self.assertEqual(
            classify_dependency("Paid Copilot code review SaaS"),
            "accidental",
        )


class RepoPresenceTests(unittest.TestCase):
    def test_evaluate_repo_requires_docs_and_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = evaluate(root)
            self.assertFalse(report["ready"])
            self.assertIn("missing_docs/VALUE_CENTER.md", report["blockers"])

    def test_evaluate_repo_ready_when_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "VALUE_CENTER.md").write_text(
                "\n".join([
                    "# Value Center",
                    "WQTU agency and coherence",
                    "What value am I delivering?",
                    "How do we coordinate?",
                    "How do we fit together?",
                    "What's out there for us?",
                    "Who are we?",
                    "",
                ]),
                encoding="utf-8",
            )
            for skill_root in (".cursor/skills", ".claude/skills"):
                p = root / skill_root / "value-center-lite"
                p.mkdir(parents=True)
                (p / "SKILL.md").write_text("# value-center-lite\n", encoding="utf-8")
            (root / "scripts").mkdir()
            (root / "scripts" / "value_center_gate.py").write_text("# stub\n", encoding="utf-8")
            report = evaluate(root)
            self.assertTrue(report["ready"], msg=json.dumps(report, indent=2))


if __name__ == "__main__":
    unittest.main()
