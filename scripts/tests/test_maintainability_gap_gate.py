"""TDD: GitClear maintainability gap — duplication up, refactoring down."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.maintainability_gap_gate import (
    HEALTH_SIGNALS,
    evaluate,
    evaluate_change_claim,
    evaluate_practice_posture,
)


class SignalTests(unittest.TestCase):
    def test_health_signals(self) -> None:
        self.assertEqual(
            list(HEALTH_SIGNALS),
            [
                "reject_loc_as_roi",
                "prefer_refactor_over_copy",
                "tests_refactor_are_the_work",
                "forklift_not_racecar",
            ],
        )


class ClaimTests(unittest.TestCase):
    def test_tenx_loc_claim_blocked(self) -> None:
        d = evaluate_change_claim(
            {
                "metric": "lines_of_code",
                "claim": "10x productivity with AI",
                "practice": "copy_paste",
            }
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_output_vanity_roi")

    def test_copy_without_reuse_search_blocked(self) -> None:
        d = evaluate_change_claim(
            {
                "metric": "cycle_time_hours",
                "claim": "added helper",
                "practice": "copy_paste",
                "searched_existing": False,
            }
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_copy_without_reuse_search")

    def test_refactor_with_tests_allowed(self) -> None:
        d = evaluate_change_claim(
            {
                "metric": "cycle_time_hours",
                "claim": "extracted shared gate helper",
                "practice": "refactor_move",
                "searched_existing": True,
                "tests_updated": True,
            }
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_maintainable_change")


class PracticeTests(unittest.TestCase):
    def test_side_quest_blocked(self) -> None:
        d = evaluate_practice_posture(
            {
                "tests": "side_quest",
                "refactor": "later",
            }
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_side_quest_practices")

    def test_mission_posture_ok(self) -> None:
        d = evaluate_practice_posture(
            {
                "tests": "required",
                "refactor": "required",
            }
        )
        self.assertTrue(d.ok)


class RepoPresenceTests(unittest.TestCase):
    def test_missing_docs_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = evaluate(Path(tmp))
            self.assertFalse(report["ready"])
            self.assertIn("missing_docs/MAINTAINABILITY_GAP.md", report["blockers"])

    def test_wired_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "MAINTAINABILITY_GAP.md").write_text(
                "\n".join(
                    [
                        "# Maintainability Gap",
                        "duplication rose 81 percent",
                        "refactoring moved code fell",
                        "tests and refactoring are the work not a side quest",
                        "forklift not racing car",
                        "lines of code is not roi",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            (root / "scripts").mkdir()
            (root / "scripts" / "maintainability_gap_gate.py").write_text("#\n")
            for sr in (".cursor/skills", ".claude/skills"):
                p = root / sr / "maintainability-gap-lite"
                p.mkdir(parents=True)
                (p / "SKILL.md").write_text("# maintainability-gap-lite\n")
            fixture = root / "marketing" / "data" / "code_health"
            fixture.mkdir(parents=True)
            (fixture / "agent_layer_discipline.json").write_text(
                json.dumps(
                    {
                        "name": "agent_layer_discipline",
                        "reject_loc_as_roi": True,
                        "prefer_refactor_over_copy": "extend existing gate pattern",
                        "tests_refactor_are_the_work": "TDD gate + stack wire required",
                        "forklift_not_racecar": "AI for large refactors across layers, not LOC races",
                        "baseline": {
                            "industry_dup_rise_pct": 81,
                            "industry_velocity_gain_pct": 25,
                            "moved_code_share_2026_pct": 3.8,
                        },
                    }
                )
            )
            report = evaluate(root)
            self.assertTrue(report["ready"], msg=json.dumps(report, indent=2))


if __name__ == "__main__":
    unittest.main()
