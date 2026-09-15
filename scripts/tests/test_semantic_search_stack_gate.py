"""TDD: Semantic Search Stack lite — LinkedIn multi-stage retrieve→rank."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.semantic_search_stack_gate import (
    HEALTH_SIGNALS,
    evaluate,
    evaluate_search_claim,
    plan_search_stages,
    select_search_path,
)


def _scaffold(root: Path) -> None:
    (root / "docs").mkdir()
    (root / "docs" / "SEMANTIC_SEARCH_STACK.md").write_text(
        "\n".join(
            [
                "# Semantic Search Stack",
                "query understanding",
                "retrieve then rank",
                "ranking depth controller",
                "keyword vs semantic routing",
                "product policy eval",
                "golden grades",
                "score caching",
                "explainability snippets",
                "distill not always frontier",
                "context compression",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (root / "scripts").mkdir()
    (root / "scripts" / "semantic_search_stack_gate.py").write_text("#\n")
    for sr in (".cursor/skills", ".claude/skills"):
        p = root / sr / "semantic-search-stack-lite"
        p.mkdir(parents=True)
        (p / "SKILL.md").write_text("# semantic-search-stack-lite\n")
    fixture = root / "marketing" / "data" / "code_health"
    fixture.mkdir(parents=True)
    (fixture / "semantic_search_stack_discipline.json").write_text(
        json.dumps(
            {
                "query_understanding": True,
                "retrieve_then_rank": True,
                "ranking_depth_controller": True,
                "keyword_vs_semantic_routing": True,
                "product_policy_eval": True,
                "score_caching": True,
                "explainability_snippets": True,
                "distill_not_always_frontier": True,
                "context_compression": True,
                "budget": {"gpu_exhaustive_saas": False},
            }
        )
    )
    golden = root / "marketing" / "data" / "search"
    golden.mkdir(parents=True)
    (golden / "product_policy_golden.json").write_text(
        json.dumps(
            {
                "policy_id": "agent_repo_search_v1",
                "scale": [0, 1, 2, 3, 4],
                "kappa_target": 0.8,
                "examples": [
                    {
                        "query": "paywall attempt success",
                        "doc_id": "docs/OPERATIONAL_RELIABILITY.md",
                        "grade": 4,
                    }
                ],
            }
        )
    )


class SignalTests(unittest.TestCase):
    def test_health_signals(self) -> None:
        self.assertGreaterEqual(len(HEALTH_SIGNALS), 8)


class PathTests(unittest.TestCase):
    def test_precise_entity_uses_keyword(self) -> None:
        self.assertEqual(
            select_search_path(query="PR #1954", ambiguous=False, entity_lookup=True),
            "keyword",
        )

    def test_ambiguous_natural_language_uses_semantic(self) -> None:
        self.assertEqual(
            select_search_path(
                query="why don't users convert after seeing the paywall",
                ambiguous=True,
                entity_lookup=False,
            ),
            "semantic",
        )

    def test_mixed_uses_hybrid(self) -> None:
        self.assertEqual(
            select_search_path(
                query="WQTU north star timer_completed",
                ambiguous=True,
                entity_lookup=True,
            ),
            "hybrid",
        )


class StageTests(unittest.TestCase):
    def test_depth_controller_limits_rank_k(self) -> None:
        plan = plan_search_stages(corpus_size=10000, retrieve_k=200, max_rank_k=50)
        self.assertEqual(plan["retrieve_k"], 200)
        self.assertEqual(plan["rank_k"], 50)
        self.assertTrue(plan["ranking_depth_controlled"])

    def test_rank_k_cannot_exceed_retrieve_k(self) -> None:
        plan = plan_search_stages(corpus_size=100, retrieve_k=20, max_rank_k=50)
        self.assertEqual(plan["rank_k"], 20)


class ClaimTests(unittest.TestCase):
    def test_single_stage_frontier_blocked(self) -> None:
        d = evaluate_search_claim({"action": "rank_entire_corpus_with_frontier"})
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_single_stage_frontier")

    def test_no_policy_eval_blocked(self) -> None:
        d = evaluate_search_claim(
            {"action": "ship_ranking_change", "product_policy_eval": False}
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_without_product_policy_eval")

    def test_unlimited_rank_depth_blocked(self) -> None:
        d = evaluate_search_claim(
            {
                "action": "run_search",
                "retrieve_k": 500,
                "rank_k": 500,
                "depth_controlled": False,
            }
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_uncontrolled_rank_depth")

    def test_gpu_saas_blocked(self) -> None:
        d = evaluate_search_claim({"action": "buy_gpu_exhaustive_search_saas"})
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_paid_search_saas")

    def test_staged_search_allowed(self) -> None:
        d = evaluate_search_claim(
            {
                "action": "run_search",
                "path": "hybrid",
                "retrieve_k": 100,
                "rank_k": 20,
                "depth_controlled": True,
                "query_understanding": True,
                "score_cache": True,
            }
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_staged_search")

    def test_policy_eval_claim_allowed(self) -> None:
        d = evaluate_search_claim(
            {
                "action": "report_relevance",
                "product_policy_eval": True,
                "metrics": ["precision", "recall", "ndcg"],
                "golden_present": True,
            }
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_relevance_report")


class PresenceTests(unittest.TestCase):
    def test_evaluate_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _scaffold(root)
            report = evaluate(root)
            self.assertTrue(report["ready"], report["blockers"])
            self.assertEqual(report["framework"], "semantic-search-stack-lite")


if __name__ == "__main__":
    unittest.main()
