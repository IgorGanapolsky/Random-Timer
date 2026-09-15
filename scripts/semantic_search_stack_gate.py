#!/usr/bin/env python3
"""Semantic Search Stack lite — LinkedIn multi-stage retrieve→rank discipline.

Source:
  https://www.linkedin.com/blog/engineering/search/reimagining-linkedins-search-stack

LinkedIn thesis (Fedor Borisyuk et al.): semantic search = query understanding →
embedding retrieval (broad candidates) → SLM cross-encoder ranking with a
ranking-depth controller, score caching, and continuous product-policy LLM
judges (golden PM grades, Kappa ≥ 0.8). Keyword path for precise entity lookups;
semantic for ambiguous natural language. Distill teachers → students; compress
long context; explain matches with snippets.

High-ROI steals for Random Timer ($20/mo hard cap — no GPU exhaustive SaaS):
  - Always retrieve-then-rank; never score the whole corpus with a frontier model
  - Rank-depth controller (rank_k << retrieve_k)
  - Route keyword vs semantic vs hybrid by query type
  - Product-policy golden set + continuous precision/recall/NDCG before claiming quality
  - Score cache + explainability snippets
  - Prefer local hybrid search (zvec/FTS) over paid semantic SaaS
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Mapping

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.lite_gate_common import (
    Decision,
    norm,
    require_docs_needles,
    require_dual_skills,
    run_presence_cli,
)

SOURCE = "https://www.linkedin.com/blog/engineering/search/reimagining-linkedins-search-stack"

HEALTH_SIGNALS = (
    "query_understanding",
    "retrieve_then_rank",
    "ranking_depth_controller",
    "keyword_vs_semantic_routing",
    "product_policy_eval",
    "score_caching",
    "explainability_snippets",
    "distill_not_always_frontier",
    "context_compression",
)

ENTITY_HINT = re.compile(
    r"\b(pr\s*#?\d+|sha\s*[0-9a-f]{7,}|run\s*\d+|issue\s*#?\d+|"
    r"com\.iganapolsky|versioncode|versionname)\b",
    re.I,
)


def select_search_path(
    *,
    query: str,
    ambiguous: bool = False,
    entity_lookup: bool | None = None,
) -> str:
    """Intelligent routing: keyword for precise entities, semantic for ambiguous NL."""
    q = (query or "").strip()
    if entity_lookup is None:
        entity_lookup = bool(ENTITY_HINT.search(q)) or (
            len(q.split()) <= 4 and not ambiguous
        )
    if entity_lookup and not ambiguous:
        return "keyword"
    if ambiguous and entity_lookup:
        return "hybrid"
    if ambiguous or len(q.split()) >= 6:
        return "semantic"
    return "hybrid"


def plan_search_stages(
    *,
    corpus_size: int,
    retrieve_k: int,
    max_rank_k: int,
) -> dict[str, Any]:
    """Ranking-depth controller: deep-rank only a controlled candidate subset."""
    retrieve_k = max(1, min(int(retrieve_k), max(1, int(corpus_size))))
    rank_k = max(1, min(int(max_rank_k), retrieve_k))
    return {
        "corpus_size": int(corpus_size),
        "retrieve_k": retrieve_k,
        "rank_k": rank_k,
        "ranking_depth_controlled": rank_k < retrieve_k or retrieve_k <= max_rank_k,
        "stages": ["query_understanding", "retrieve", "rank", "explain"],
        "source": SOURCE,
    }


def evaluate_search_claim(claim: Mapping[str, object]) -> Decision:
    action = norm(claim.get("action"))

    if action in {
        "rank_entire_corpus_with_frontier",
        "always_frontier_rank",
        "score_all_docs_with_llm",
    }:
        return Decision(
            action="block_single_stage_frontier",
            ok=False,
            reason="retrieve-then-rank: never score the full corpus with a frontier model",
        )

    if action in {
        "buy_gpu_exhaustive_search_saas",
        "subscribe_galene_cloud",
        "pay_for_exhaustive_knn_saas",
    }:
        return Decision(
            action="block_paid_search_saas",
            ok=False,
            reason="steal staging locally (zvec/FTS/hybrid); no GPU exhaustive search SaaS under hard cap",
        )

    if action in {"ship_ranking_change", "claim_search_quality"}:
        if claim.get("product_policy_eval") is not True:
            return Decision(
                action="block_without_product_policy_eval",
                ok=False,
                reason="LinkedIn-style product policy + golden grades required before quality claims",
            )
        return Decision(
            action="allow_policy_backed_change",
            ok=True,
            reason="change backed by product-policy eval",
        )

    if action in {"run_search", "retrieve_and_rank"}:
        try:
            retrieve_k = int(claim.get("retrieve_k") or 0)
            rank_k = int(claim.get("rank_k") or 0)
        except (TypeError, ValueError):
            return Decision(
                action="block_invalid_stage_sizes",
                ok=False,
                reason="declare integer retrieve_k and rank_k",
            )
        if retrieve_k <= 0 or rank_k <= 0:
            return Decision(
                action="block_invalid_stage_sizes",
                ok=False,
                reason="retrieve_k and rank_k must be > 0",
            )
        if rank_k > retrieve_k:
            return Decision(
                action="block_rank_exceeds_retrieve",
                ok=False,
                reason="rank_k must be <= retrieve_k",
            )
        if claim.get("depth_controlled") is not True and rank_k >= retrieve_k and retrieve_k > 25:
            return Decision(
                action="block_uncontrolled_rank_depth",
                ok=False,
                reason="ranking-depth controller required when deep-ranking large candidate sets",
            )
        if claim.get("query_understanding") is not True and norm(claim.get("path")) == "semantic":
            return Decision(
                action="block_semantic_without_understanding",
                ok=False,
                reason="semantic path requires query understanding / intent signals",
            )
        return Decision(
            action="allow_staged_search",
            ok=True,
            reason="staged retrieve→rank with depth control",
        )

    if action in {"report_relevance", "report_ndcg"}:
        metrics = claim.get("metrics") or []
        if claim.get("product_policy_eval") is not True:
            return Decision(
                action="block_relevance_without_policy",
                ok=False,
                reason="relevance reports need product_policy_eval=true",
            )
        if claim.get("golden_present") is not True:
            return Decision(
                action="block_relevance_without_golden",
                ok=False,
                reason="golden product-manager grades fixture required",
            )
        needed = {"precision", "recall", "ndcg"}
        have = {norm(m) for m in metrics} if isinstance(metrics, list) else set()
        if not needed.issubset(have):
            return Decision(
                action="block_relevance_missing_metrics",
                ok=False,
                reason="report precision, recall, and ndcg",
            )
        return Decision(
            action="allow_relevance_report",
            ok=True,
            reason="policy-backed relevance metrics",
        )

    if action in {"select_path"}:
        path = select_search_path(
            query=str(claim.get("query") or ""),
            ambiguous=bool(claim.get("ambiguous")),
            entity_lookup=claim.get("entity_lookup")
            if "entity_lookup" in claim
            else None,
        )
        return Decision(
            action=f"allow_path_{path}",
            ok=True,
            reason=f"selected search path: {path}",
        )

    return Decision(
        action="block_unknown_search_stack_action",
        ok=False,
        reason=(
            "declare action: run_search|select_path|ship_ranking_change|"
            "report_relevance"
        ),
    )


def evaluate(repo: Path) -> dict[str, Any]:
    blockers: list[str] = []
    if not (repo / "docs" / "SEMANTIC_SEARCH_STACK.md").is_file():
        blockers.append("missing_docs/SEMANTIC_SEARCH_STACK.md")
    if not (repo / "scripts" / "semantic_search_stack_gate.py").is_file():
        blockers.append("missing_scripts/semantic_search_stack_gate.py")
    blockers.extend(require_dual_skills(repo, "semantic-search-stack-lite"))
    blockers.extend(
        require_docs_needles(
            repo / "docs" / "SEMANTIC_SEARCH_STACK.md",
            (
                "query understanding",
                "retrieve",
                "rank",
                "depth",
                "keyword",
                "semantic",
                "product policy",
                "golden",
                "score caching",
                "explainability",
                "distill",
                "compression",
            ),
        )
    )

    fixture = (
        repo / "marketing" / "data" / "code_health" / "semantic_search_stack_discipline.json"
    )
    if not fixture.is_file():
        blockers.append(
            "missing_fixture:marketing/data/code_health/semantic_search_stack_discipline.json"
        )
    else:
        try:
            charter = json.loads(fixture.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            blockers.append(f"fixture_invalid_json:{exc}")
        else:
            for signal in HEALTH_SIGNALS:
                if not charter.get(signal):
                    blockers.append(f"fixture_missing:{signal}")
            budget = charter.get("budget") or {}
            if not isinstance(budget, dict) or budget.get("gpu_exhaustive_saas") is not False:
                blockers.append("fixture_missing:budget.gpu_exhaustive_saas=false")

    golden = repo / "marketing" / "data" / "search" / "product_policy_golden.json"
    if not golden.is_file():
        blockers.append("missing_fixture:marketing/data/search/product_policy_golden.json")
    else:
        try:
            g = json.loads(golden.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            blockers.append(f"golden_invalid_json:{exc}")
        else:
            if not g.get("examples"):
                blockers.append("golden_missing:examples")
            if float(g.get("kappa_target") or 0) < 0.8:
                blockers.append("golden_missing:kappa_target>=0.8")

    ready = len(blockers) == 0
    return {
        "framework": "semantic-search-stack-lite",
        "source": SOURCE,
        "ready": ready,
        "blockers": blockers,
        "health_signals": list(HEALTH_SIGNALS),
        "stages": ["query_understanding", "retrieve", "rank", "explain", "eval"],
        "anti_pattern": "single_stage_frontier_over_full_corpus",
        "budget_note": (
            "local hybrid retrieve→rank + product-policy golden eval; "
            "no GPU exhaustive search SaaS under hard monthly cap"
        ),
        "pairs_with": [
            "scripts/search_isolation.py",
            "docs/HYDRAFUSION_ROUTING.md",
            "docs/TRUST_RELIABILITY_LOOP.md",
            "docs/LLM_RESPONSE_CACHE.md",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    return run_presence_cli(
        description=__doc__ or "semantic-search-stack-lite",
        evaluate=evaluate,
        claim_evaluator=evaluate_search_claim,
        argv=argv,
    )


if __name__ == "__main__":
    raise SystemExit(main())
