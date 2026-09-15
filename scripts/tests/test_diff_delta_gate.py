"""TDD: GitClear Diff Delta — durable AI ROI, not token vanity."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.diff_delta_gate import (
    HEALTH_SIGNALS,
    evaluate,
    evaluate_roi_claim,
    evaluate_yield_stage,
)


class SignalTests(unittest.TestCase):
    def test_health_signals(self) -> None:
        self.assertEqual(
            list(HEALTH_SIGNALS),
            [
                "score_durable_diff_delta",
                "yield_to_production_not_tokens",
                "flag_ai_hotspot_dirs",
                "same_yardstick_human_llm",
            ],
        )


class RoiClaimTests(unittest.TestCase):
    def test_token_volume_claim_blocked(self) -> None:
        d = evaluate_roi_claim(
            {
                "metric": "tokens",
                "claim": "AI wrote 4x more code",
                "stage": "generated",
            }
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_token_vanity_roi")

    def test_loc_as_ai_roi_blocked(self) -> None:
        d = evaluate_roi_claim(
            {
                "metric": "lines_of_code",
                "claim": "model earned its license via volume",
                "stage": "committed",
            }
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_token_vanity_roi")

    def test_durable_delta_with_survival_allowed(self) -> None:
        d = evaluate_roi_claim(
            {
                "metric": "diff_delta",
                "claim": "durable change still present at 30d",
                "stage": "day_30",
                "surviving_share_pct": 70,
                "same_yardstick": True,
            }
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_durable_roi")

    def test_durable_without_same_yardstick_blocked(self) -> None:
        d = evaluate_roi_claim(
            {
                "metric": "diff_delta",
                "claim": "AI cohort faster",
                "stage": "day_30",
                "surviving_share_pct": 70,
                "same_yardstick": False,
            }
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_apples_oranges_cohort")


class YieldStageTests(unittest.TestCase):
    def test_pre_merge_leakage_not_roi(self) -> None:
        d = evaluate_yield_stage({"stage": "generated", "count_as_roi": True})
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_pre_merge_as_roi")

    def test_day_90_survival_ok(self) -> None:
        d = evaluate_yield_stage({"stage": "day_90", "count_as_roi": True})
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_post_merge_survival")


class RepoPresenceTests(unittest.TestCase):
    def test_missing_docs_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = evaluate(Path(tmp))
            self.assertFalse(report["ready"])
            self.assertIn("missing_docs/DIFF_DELTA.md", report["blockers"])

    def test_wired_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "DIFF_DELTA.md").write_text(
                "\n".join(
                    [
                        "# Diff Delta lite",
                        "durable Diff Delta beats tokens",
                        "yield to production not tokens",
                        "AI hotspot directories raise defect and duplication",
                        "same yardstick for human and LLM cohorts",
                        "moves renames reformatting keep lineage",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            (root / "scripts").mkdir()
            (root / "scripts" / "diff_delta_gate.py").write_text("#\n")
            for sr in (".cursor/skills", ".claude/skills"):
                p = root / sr / "diff-delta-lite"
                p.mkdir(parents=True)
                (p / "SKILL.md").write_text("# diff-delta-lite\n")
            fixture = root / "marketing" / "data" / "code_health"
            fixture.mkdir(parents=True)
            (fixture / "diff_delta_discipline.json").write_text(
                json.dumps(
                    {
                        "name": "diff_delta_discipline",
                        "score_durable_diff_delta": True,
                        "yield_to_production_not_tokens": "generated→merged→day_30/90",
                        "flag_ai_hotspot_dirs": "defect Δ + duplication Δ vs baseline",
                        "same_yardstick_human_llm": "Diff Delta for both cohorts",
                        "baseline": {
                            "industry_dup_block_multiplier": 8,
                            "industry_ai_churn_multiplier": 9,
                            "source": "https://www.gitclear.com/",
                        },
                    }
                )
            )
            report = evaluate(root)
            self.assertTrue(report["ready"], msg=json.dumps(report, indent=2))


if __name__ == "__main__":
    unittest.main()
