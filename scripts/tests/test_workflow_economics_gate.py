"""TDD: escape AI pilot purgatory — completion-loop workflow economics."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.workflow_economics_gate import (
    COMPLETION_STAGES,
    ECONOMIC_METRICS,
    evaluate,
    evaluate_pilot_claim,
    evaluate_workflow_charter,
)


class CompletionLoopTests(unittest.TestCase):
    def test_six_stages(self) -> None:
        self.assertEqual(
            list(COMPLETION_STAGES),
            [
                "trigger",
                "context_retrieval",
                "decision",
                "action",
                "verification",
                "audit_trail",
            ],
        )


class CharterTests(unittest.TestCase):
    def test_chatbot_without_owner_fails(self) -> None:
        d = evaluate_workflow_charter(
            {
                "name": "enterprise chatbot",
                "kind": "chatbot",
                "owner": "",
                "baseline": {},
                "metric": "usage",
                "stages": {},
            }
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_orphan_pilot")

    def test_complete_release_workflow_passes(self) -> None:
        d = evaluate_workflow_charter(
            {
                "name": "native_release_completion",
                "kind": "operational",
                "owner": "cto",
                "user_group": "release-ops",
                "baseline": {
                    "metric": "cycle_time_hours",
                    "value": 48,
                    "window": "pre-automation",
                },
                "metric": "cycle_time_hours",
                "system_of_record": "github_actions+stores",
                "stages": {
                    "trigger": "workflow_dispatch on release/v*",
                    "context_retrieval": "SHA signoffs + store metadata",
                    "decision": "production-signoff approve/deny",
                    "action": "upload Play + submit ASC",
                    "verification": "Publisher API + ASC state read-back",
                    "audit_trail": "Actions run logs + GitHub Release",
                },
                "approval_policy": "human_at_production_signoff_only",
            }
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_completion_workflow")


class PilotClaimTests(unittest.TestCase):
    def test_demo_interest_is_not_roi(self) -> None:
        d = evaluate_pilot_claim(
            {
                "evidence": "team likes the demo chatbot",
                "metric": "interest",
            }
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_interest_not_roi")

    def test_economic_metric_allowed(self) -> None:
        self.assertIn("automation_rate", ECONOMIC_METRICS)
        d = evaluate_pilot_claim(
            {
                "evidence": "automation_rate 0.62 cycle_time_hours 6",
                "metric": "automation_rate",
                "baseline_value": 0.1,
                "current_value": 0.62,
            }
        )
        self.assertTrue(d.ok)


class RepoPresenceTests(unittest.TestCase):
    def test_missing_docs_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = evaluate(Path(tmp))
            self.assertFalse(report["ready"])
            self.assertIn("missing_docs/WORKFLOW_ECONOMICS.md", report["blockers"])

    def test_wired_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "WORKFLOW_ECONOMICS.md").write_text(
                "\n".join(
                    [
                        "# Workflow Economics",
                        "escape pilot purgatory",
                        "completion loop trigger verification audit",
                        "accountable process owner",
                        "weekly economic metric",
                        "system of record",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            (root / "scripts").mkdir()
            (root / "scripts" / "workflow_economics_gate.py").write_text("#\n")
            for sr in (".cursor/skills", ".claude/skills"):
                p = root / sr / "workflow-economics-lite"
                p.mkdir(parents=True)
                (p / "SKILL.md").write_text("# workflow-economics-lite\n")
            fixture = root / "marketing" / "data" / "workflows"
            fixture.mkdir(parents=True)
            (fixture / "native_release_completion.json").write_text(
                json.dumps(
                    {
                        "name": "native_release_completion",
                        "kind": "operational",
                        "owner": "cto",
                        "user_group": "release-ops",
                        "baseline": {
                            "metric": "cycle_time_hours",
                            "value": 48,
                            "window": "pre-automation",
                        },
                        "metric": "cycle_time_hours",
                        "system_of_record": "github_actions+stores",
                        "stages": {
                            "trigger": "workflow_dispatch",
                            "context_retrieval": "signoffs",
                            "decision": "production-signoff",
                            "action": "upload",
                            "verification": "read-back",
                            "audit_trail": "Actions logs",
                        },
                        "approval_policy": "human_at_production_signoff_only",
                    }
                )
            )
            report = evaluate(root)
            self.assertTrue(report["ready"], msg=json.dumps(report, indent=2))


if __name__ == "__main__":
    unittest.main()
