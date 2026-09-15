"""TDD: Multi-Teacher Distill lite — LinkedIn 8X offline distillation."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.multi_teacher_distill_gate import (
    HEALTH_SIGNALS,
    estimate_distill_speedup,
    evaluate,
    evaluate_distill_claim,
    plan_teacher_cache,
    select_distill_mode,
    select_phase_mode,
    stack_compound_speedups,
)


def _scaffold(root: Path) -> None:
    (root / "docs").mkdir()
    (root / "docs" / "MULTI_TEACHER_DISTILL.md").write_text(
        "\n".join(
            [
                "# Multi-Teacher Distill",
                "multi-teacher pluggable teachers",
                "offline distillation cache",
                "online distillation",
                "per-shard invalidation",
                "student iterate",
                "soft label and embedding signals",
                "8x faster amortized",
                "stream not full stage",
                "sglang async teacher serving",
                "stable teachers switch offline",
                "compound moderate gains",
                "fp8 rejected for small models",
                "structured pruning and compression",
                "ndcg ranking quality evidence",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (root / "scripts").mkdir()
    (root / "scripts" / "multi_teacher_distill_gate.py").write_text("#\n")
    for sr in (".cursor/skills", ".claude/skills"):
        p = root / sr / "multi-teacher-distill-lite"
        p.mkdir(parents=True)
        (p / "SKILL.md").write_text("# multi-teacher-distill-lite\n")
    fixture = root / "marketing" / "data" / "code_health"
    fixture.mkdir(parents=True)
    (fixture / "multi_teacher_distill_discipline.json").write_text(
        json.dumps(
            {
                "multi_teacher_pluggable": True,
                "offline_teacher_cache": True,
                "per_shard_invalidation": True,
                "student_iterate_without_teachers": True,
                "unified_online_offline": True,
                "stream_not_full_stage": True,
                "hard_plus_soft_labels": True,
                "compact_student_for_serving": True,
                "async_teacher_serving": True,
                "teacher_stability_mode_switch": True,
                "compound_moderate_gains": True,
                "reject_fp8_default_small": True,
                "prune_and_compress_serving": True,
                "ranking_quality_evidence": True,
                "budget": {"gpu_training_saas": False},
            }
        )
    )


class SignalTests(unittest.TestCase):
    def test_health_signals(self) -> None:
        self.assertGreaterEqual(len(HEALTH_SIGNALS), 12)


class ModeTests(unittest.TestCase):
    def test_student_only_reuses_cache(self) -> None:
        self.assertEqual(
            select_distill_mode(
                teachers_changed=False,
                data_changed=False,
                student_only_iteration=True,
                cache_hit_rate=0.9,
            ),
            "reuse_cache",
        )

    def test_teachers_and_data_changed_uses_online(self) -> None:
        self.assertEqual(
            select_distill_mode(
                teachers_changed=True,
                data_changed=True,
                student_only_iteration=False,
                cache_hit_rate=0.0,
            ),
            "online",
        )

    def test_data_changed_prefers_offline(self) -> None:
        self.assertEqual(
            select_distill_mode(
                teachers_changed=False,
                data_changed=True,
                student_only_iteration=False,
                cache_hit_rate=0.5,
            ),
            "offline",
        )

    def test_infoq_phase_online_while_exploring(self) -> None:
        self.assertEqual(
            select_phase_mode(teachers_stable=False, query_volume_high=False),
            "online",
        )

    def test_infoq_phase_offline_when_stable(self) -> None:
        self.assertEqual(
            select_phase_mode(teachers_stable=True, query_volume_high=True),
            "offline",
        )


class CacheTests(unittest.TestCase):
    def test_cache_key_and_per_shard(self) -> None:
        plan = plan_teacher_cache(
            model_version="relevance-v3",
            data_fingerprint="fp-abc",
            shards_changed=["shard-07"],
        )
        self.assertEqual(plan["cache_key"], "relevance-v3:fp-abc")
        self.assertEqual(plan["shards_to_regen"], ["shard-07"])
        self.assertTrue(plan["per_shard_invalidation"])
        self.assertFalse(plan["all_or_nothing"])


class SpeedupTests(unittest.TestCase):
    def test_linkedin_style_8x(self) -> None:
        report = estimate_distill_speedup(
            baseline_hours=45.0,
            offline_student_hours=5.0,
            cache_generation_hours=2.0,
            amortize_over_student_runs=10,
        )
        self.assertTrue(report["meets_8x_target"])
        self.assertGreaterEqual(report["speedup_x"], 8.0)

    def test_compound_stack(self) -> None:
        report = stack_compound_speedups([2.0, 1.2, 1.3, 1.3])
        self.assertTrue(report["is_compound"])
        self.assertGreaterEqual(report["compound_speedup_x"], 4.0)


class ClaimTests(unittest.TestCase):
    def test_gpu_saas_blocked(self) -> None:
        d = evaluate_distill_claim({"action": "buy_gpu_multi_node_saas"})
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_paid_training_saas")

    def test_always_rerun_teachers_blocked(self) -> None:
        d = evaluate_distill_claim({"action": "always_rerun_teachers"})
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_wasteful_teacher_rerun")

    def test_serve_teachers_live_blocked(self) -> None:
        d = evaluate_distill_claim({"action": "serve_teachers_at_query_time"})
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_serve_teachers_live")

    def test_offline_without_cache_blocked(self) -> None:
        d = evaluate_distill_claim(
            {"action": "run_offline_distill", "teacher_cache_present": False}
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_offline_without_cache")

    def test_offline_from_cache_allowed(self) -> None:
        d = evaluate_distill_claim(
            {
                "action": "train_student_from_cache",
                "teacher_cache_present": True,
                "per_shard_invalidation": True,
            }
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_offline_student_train")

    def test_pluggable_teacher_allowed(self) -> None:
        d = evaluate_distill_claim(
            {
                "action": "register_teacher",
                "role": "relevance",
                "pluggable": True,
            }
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_pluggable_teacher")

    def test_fp8_default_blocked(self) -> None:
        d = evaluate_distill_claim({"action": "default_fp8_small"})
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_default_fp8_small")

    def test_ndcg_required_for_quality_claim(self) -> None:
        d = evaluate_distill_claim({"action": "claim_ndcg"})
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_quality_without_ndcg")

    def test_ndcg_backed_claim_allowed(self) -> None:
        d = evaluate_distill_claim(
            {"action": "claim_ranking_quality", "ndcg_reported": True}
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_quality_backed_claim")

    def test_prune_compress_serving_allowed(self) -> None:
        d = evaluate_distill_claim(
            {
                "action": "serve_with_prune_compress",
                "structured_pruning": True,
                "context_compression": True,
            }
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_prune_compress_serving")

    def test_compound_gains_require_stack(self) -> None:
        d = evaluate_distill_claim({"action": "stack_gains", "gains": [2.0]})
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_single_trick_speedup")


class PresenceTests(unittest.TestCase):
    def test_evaluate_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _scaffold(root)
            report = evaluate(root)
            self.assertTrue(report["ready"], report["blockers"])
            self.assertEqual(report["framework"], "multi-teacher-distill-lite")
            self.assertIn("infoq.com", report["infoq_source"])


if __name__ == "__main__":
    unittest.main()
