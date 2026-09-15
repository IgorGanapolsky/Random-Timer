"""TDD: InfoQ when SDD pays off — targeting, staged governance, attributable drift."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.spec_governance_gate import (
    CONTROL_POINTS,
    classify_task,
    evaluate,
    evaluate_drift_review,
    evaluate_generation_mode,
    evaluate_targeting,
)


class TargetingTests(unittest.TestCase):
    def test_easy_task_skips_full_governance(self) -> None:
        d = evaluate_targeting(classify_task("rename a typo in README"))
        self.assertEqual(d.action, "allow_reason_first")
        self.assertTrue(d.ok)

    def test_hard_multi_constraint_requires_governance(self) -> None:
        d = evaluate_targeting(
            classify_task(
                "Play Billing catalog load with network failure telemetry and paywall gate"
            )
        )
        self.assertEqual(d.action, "require_spec_governance")
        self.assertTrue(d.ok)

    def test_claiming_spec_improves_recall_is_blocked(self) -> None:
        d = evaluate_targeting(
            {
                "hardness": "hard",
                "claim": "spec baseline raises bug recall",
            }
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_false_recall_claim")


class GenerationModeTests(unittest.TestCase):
    def test_inline_spec_prompt_fails_for_hard(self) -> None:
        d = evaluate_generation_mode(
            hardness="hard",
            mode="single_prompt_spec_then_code",
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_inline_spec_prompt")

    def test_staged_baseline_then_fresh_generate_passes(self) -> None:
        d = evaluate_generation_mode(
            hardness="hard",
            mode="staged_approved_baseline_then_generate",
            baseline_version="specs/004/v1",
        )
        self.assertTrue(d.ok)


class DriftAttributionTests(unittest.TestCase):
    def test_unattributed_findings_fail(self) -> None:
        d = evaluate_drift_review(
            findings=[
                {"note": "looks wrong", "invariant": ""},
                {"note": "maybe race", "invariant": None},
            ]
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_unattributed_drift")

    def test_named_invariants_pass(self) -> None:
        d = evaluate_drift_review(
            findings=[
                {
                    "note": "overdraft allowed",
                    "invariant": "transfer_atomic_on_fail",
                },
                {
                    "note": "double charge",
                    "invariant": "transfer_idempotent",
                },
            ],
            reconciler="cto-agent",
            accountable_human="ceo",
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_attributed_drift")

    def test_model_cannot_be_accountable(self) -> None:
        d = evaluate_drift_review(
            findings=[{"note": "x", "invariant": "assets_conserved"}],
            reconciler="model",
            accountable_human="claude-sonnet",
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_model_accountable")


class ControlPointsTests(unittest.TestCase):
    def test_five_control_points(self) -> None:
        self.assertEqual(
            list(CONTROL_POINTS),
            [
                "specification_authoring",
                "specification_review_gate",
                "guided_generation",
                "drift_detection",
                "reconciliation",
            ],
        )


class RepoPresenceTests(unittest.TestCase):
    def test_missing_docs_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = evaluate(Path(tmp))
            self.assertFalse(report["ready"])
            self.assertIn("missing_docs/SPEC_GOVERNANCE.md", report["blockers"])

    def test_wired_repo_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "SPEC_GOVERNANCE.md").write_text(
                "\n".join(
                    [
                        "# Spec Governance",
                        "Source InfoQ when SDD pays off",
                        "targeting rule hard multi-constraint",
                        "attribution named invariant",
                        "human accountable",
                        "control points",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            (root / "scripts").mkdir()
            (root / "scripts" / "spec_governance_gate.py").write_text("#\n", encoding="utf-8")
            for skill_root in (".cursor/skills", ".claude/skills"):
                p = root / skill_root / "spec-governance-lite"
                p.mkdir(parents=True)
                (p / "SKILL.md").write_text("# spec-governance-lite\n", encoding="utf-8")
            report = evaluate(root)
            self.assertTrue(report["ready"], msg=json.dumps(report, indent=2))


if __name__ == "__main__":
    unittest.main()
