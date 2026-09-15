"""TDD: Looped Flows — recurrent reasoning depth without parameter bloat."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.looped_flows_gate import (
    HEALTH_SIGNALS,
    evaluate,
    evaluate_loop_plan,
    evaluate_training_posture,
)


class SignalTests(unittest.TestCase):
    def test_health_signals(self) -> None:
        self.assertEqual(
            list(HEALTH_SIGNALS),
            [
                "reason_by_recurrence_not_params",
                "early_steps_set_up_later",
                "local_objectives_chain",
                "adaptive_compute_grid",
            ],
        )


class LoopPlanTests(unittest.TestCase):
    def test_bigger_model_instead_of_loops_blocked(self) -> None:
        d = evaluate_loop_plan(
            {
                "strategy": "add_parameters",
                "loops": 1,
                "claim": "upgrade to larger model for harder bug",
            }
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_params_over_recurrence")

    def test_single_shot_no_local_objectives_blocked(self) -> None:
        d = evaluate_loop_plan(
            {
                "strategy": "recurrent",
                "loops": 3,
                "local_objectives": False,
                "early_sets_up_later": True,
            }
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_untied_loops")

    def test_chained_recurrent_plan_allowed(self) -> None:
        d = evaluate_loop_plan(
            {
                "strategy": "recurrent",
                "loops": 3,
                "local_objectives": True,
                "early_sets_up_later": True,
                "adaptive_grid": True,
            }
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_looped_reasoning")


class TrainingPostureTests(unittest.TestCase):
    def test_last_step_only_blocked(self) -> None:
        d = evaluate_training_posture({"gradient_span": "last_one", "shared_noise": False})
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_last_step_only")

    def test_local_denoising_chain_ok(self) -> None:
        d = evaluate_training_posture(
            {"gradient_span": "local", "shared_noise": True, "decreasing_noise": True}
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_local_denoising_chain")


class RepoPresenceTests(unittest.TestCase):
    def test_missing_docs_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = evaluate(Path(tmp))
            self.assertFalse(report["ready"])
            self.assertIn("missing_docs/LOOPED_FLOWS.md", report["blockers"])

    def test_wired_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "LOOPED_FLOWS.md").write_text(
                "\n".join(
                    [
                        "# Looped Flows lite",
                        "recurrent reasoning without adding parameters",
                        "early steps set up later updates",
                        "local denoising objectives chain",
                        "adaptive compute finer time grid",
                        "gradients last step only is the failure mode",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            (root / "scripts").mkdir()
            (root / "scripts" / "looped_flows_gate.py").write_text("#\n")
            for sr in (".cursor/skills", ".claude/skills"):
                p = root / sr / "looped-flows-lite"
                p.mkdir(parents=True)
                (p / "SKILL.md").write_text("# looped-flows-lite\n")
            fixture = root / "marketing" / "data" / "code_health"
            fixture.mkdir(parents=True)
            (fixture / "looped_flows_discipline.json").write_text(
                json.dumps(
                    {
                        "name": "looped_flows_discipline",
                        "reason_by_recurrence_not_params": True,
                        "early_steps_set_up_later": "each verify loop carries state for the next",
                        "local_objectives_chain": "local checks with shared context across steps",
                        "adaptive_compute_grid": "more loops on harder failures",
                        "baseline": {
                            "paper": "Thinking with Looped Flows",
                            "arxiv": "2609.11801",
                            "source": "https://arxiv.org/abs/2609.11801",
                        },
                    }
                )
            )
            report = evaluate(root)
            self.assertTrue(report["ready"], msg=json.dumps(report, indent=2))


if __name__ == "__main__":
    unittest.main()
