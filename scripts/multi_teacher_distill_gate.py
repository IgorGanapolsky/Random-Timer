#!/usr/bin/env python3
"""Multi-Teacher Distill lite — LinkedIn 8X faster distillation discipline.

Sources:
  https://www.linkedin.com/blog/engineering/infrastructure/the-training-infrastructure-behind-ai-powered-job-search-eight-x-faster-multi-teacher-distillation
  https://www.infoq.com/news/2026/09/linkedin-ai-multi-teacher/

LinkedIn thesis: multi-specialized teachers (relevance / engagement / embeddings)
feed a compact student SLM under a hard serving latency budget. Biggest win is
**offline distillation** — cache teacher soft labels + embeddings keyed by model
version and data fingerprint (per-shard), then iterate the student without
re-running teachers. Online path co-locates teachers (SGLang-style async serving);
unified framework shares plumbing. ~45h → <5h (~8X) with no quality loss.

InfoQ digest adds: online while teachers change → offline when stable + volume
rises; compound moderate gains (not one trick); FP8 no win under ~8B; structured
pruning + context compression for serving throughput; NDCG evidence before claims.

High-ROI steals for Random Timer ($20/mo hard cap — no GPU training SaaS):
  - Prefer student iteration over re-running expensive teachers/frontiers
  - Cache teacher signals (pairs with LLM Response Cache); invalidate per-shard
  - Treat teachers as pluggable (relevance / engagement / embedding / policy)
  - Distill into compact artifacts (skills, gates, fixtures) — do not serve
    multi-teacher fleets at query time
  - Stream/chunk context; do not stage the whole corpus every run
  - Switch online→offline by teacher stability; stack moderate local gains
  - Prune + compress for serving; demand ranking-quality evidence (e.g. NDCG)
"""

from __future__ import annotations

import json
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

SOURCE = (
    "https://www.linkedin.com/blog/engineering/infrastructure/"
    "the-training-infrastructure-behind-ai-powered-job-search-"
    "eight-x-faster-multi-teacher-distillation"
)
INFOQ_SOURCE = "https://www.infoq.com/news/2026/09/linkedin-ai-multi-teacher/"

HEALTH_SIGNALS = (
    "multi_teacher_pluggable",
    "offline_teacher_cache",
    "per_shard_invalidation",
    "student_iterate_without_teachers",
    "unified_online_offline",
    "stream_not_full_stage",
    "hard_plus_soft_labels",
    "compact_student_for_serving",
    "async_teacher_serving",
    "teacher_stability_mode_switch",
    "compound_moderate_gains",
    "reject_fp8_default_small",
    "prune_and_compress_serving",
    "ranking_quality_evidence",
)

TEACHER_ROLES = frozenset(
    {"relevance", "engagement", "embedding", "policy", "click", "critic"}
)


def select_distill_mode(
    *,
    teachers_changed: bool,
    data_changed: bool,
    student_only_iteration: bool,
    cache_hit_rate: float = 0.0,
) -> str:
    """Online vs offline vs reuse-cache — LinkedIn's biggest lever was offline."""
    if student_only_iteration and not teachers_changed and not data_changed:
        return "reuse_cache" if cache_hit_rate >= 0.5 else "offline"
    if teachers_changed or (data_changed and cache_hit_rate < 0.3):
        return "online" if teachers_changed and data_changed else "offline"
    if cache_hit_rate >= 0.8:
        return "reuse_cache"
    return "offline"


def plan_teacher_cache(
    *,
    model_version: str,
    data_fingerprint: str,
    shards_changed: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Per-teacher cache keyed by model version + data fingerprint; per-shard invalidation."""
    version = (model_version or "").strip()
    fingerprint = (data_fingerprint or "").strip()
    changed = [str(s).strip() for s in (shards_changed or []) if str(s).strip()]
    return {
        "cache_key": f"{version}:{fingerprint}" if version and fingerprint else "",
        "model_version": version,
        "data_fingerprint": fingerprint,
        "shards_to_regen": changed,
        "all_or_nothing": False,
        "per_shard_invalidation": True,
        "source": SOURCE,
    }


def estimate_distill_speedup(
    *,
    baseline_hours: float,
    offline_student_hours: float,
    cache_generation_hours: float = 0.0,
    amortize_over_student_runs: int = 1,
) -> dict[str, Any]:
    """Report amortized speedup vs full re-run (LinkedIn: ~45h → <5h ≈ 8X)."""
    baseline = max(0.01, float(baseline_hours))
    student = max(0.01, float(offline_student_hours))
    cache_cost = max(0.0, float(cache_generation_hours))
    runs = max(1, int(amortize_over_student_runs))
    amortized = student + (cache_cost / runs)
    speedup = baseline / amortized
    return {
        "baseline_hours": baseline,
        "amortized_hours": round(amortized, 4),
        "speedup_x": round(speedup, 2),
        "meets_8x_target": speedup >= 8.0,
        "source": SOURCE,
    }


def select_phase_mode(
    *,
    teachers_stable: bool,
    query_volume_high: bool = False,
) -> str:
    """InfoQ guidance: online while exploring teachers; offline once stable + volume rises."""
    if teachers_stable and query_volume_high:
        return "offline"
    if teachers_stable:
        return "offline"
    return "online"


def stack_compound_speedups(gains: list[float] | tuple[float, ...] | None) -> dict[str, Any]:
    """InfoQ: 8X is stacked moderate gains (LiGer / multi-node / FSDP2 / GPU gen), not one trick."""
    factors = [float(g) for g in (gains or []) if float(g) > 0]
    product = 1.0
    for g in factors:
        product *= g
    return {
        "factors": factors,
        "compound_speedup_x": round(product, 2),
        "is_compound": len(factors) >= 2,
        "source": INFOQ_SOURCE,
    }


def evaluate_distill_claim(claim: Mapping[str, object]) -> Decision:
    action = norm(claim.get("action"))

    if action in {
        "buy_gpu_multi_node_saas",
        "subscribe_fsdp_cloud",
        "rent_h200_cluster",
        "pay_for_multi_teacher_training_saas",
    }:
        return Decision(
            action="block_paid_training_saas",
            ok=False,
            reason="steal offline cache + pluggable teachers locally; no GPU training SaaS under hard cap",
        )

    if action in {
        "always_rerun_teachers",
        "full_pipeline_every_student_iter",
        "invalidate_all_teacher_cache",
    }:
        return Decision(
            action="block_wasteful_teacher_rerun",
            ok=False,
            reason="offline distill: iterate student from cached soft labels; invalidate per-shard only",
        )

    if action in {"serve_teachers_at_query_time", "serve_multi_billion_teachers"}:
        return Decision(
            action="block_serve_teachers_live",
            ok=False,
            reason="serving constraint: distill into compact student/skill; do not serve teacher fleets live",
        )

    if action in {"hardcode_single_teacher", "assume_fixed_teacher_set"}:
        return Decision(
            action="block_fixed_teacher_assumption",
            ok=False,
            reason="teachers must be pluggable components (relevance|engagement|embedding|policy|…)",
        )

    if action in {
        "default_fp8_small",
        "always_fp8",
        "force_fp8_under_8b",
    }:
        return Decision(
            action="block_default_fp8_small",
            ok=False,
            reason="InfoQ: FP8 casting overhead outweighed savings under ~8B — do not default to FP8",
        )

    if action in {"frontier_llm_every_rank_request", "always_frontier_rank_inference"}:
        return Decision(
            action="block_frontier_per_request",
            ok=False,
            reason="InfoQ: avoid frontier-LLM inference for every ranking request — distill to compact student",
        )

    if action in {"select_mode", "choose_distill_mode"}:
        mode = select_distill_mode(
            teachers_changed=bool(claim.get("teachers_changed")),
            data_changed=bool(claim.get("data_changed")),
            student_only_iteration=bool(claim.get("student_only_iteration")),
            cache_hit_rate=float(claim.get("cache_hit_rate") or 0.0),
        )
        return Decision(
            action=f"allow_mode_{mode}",
            ok=True,
            reason=f"selected distill mode: {mode}",
        )

    if action in {"select_phase", "phase_mode"}:
        mode = select_phase_mode(
            teachers_stable=bool(claim.get("teachers_stable")),
            query_volume_high=bool(claim.get("query_volume_high")),
        )
        return Decision(
            action=f"allow_phase_{mode}",
            ok=True,
            reason=f"InfoQ phase mode: {mode} (online while exploring; offline when stable)",
        )

    if action in {"stack_gains", "compound_speedups"}:
        gains = claim.get("gains") or []
        if not isinstance(gains, list) or len(gains) < 2:
            return Decision(
                action="block_single_trick_speedup",
                ok=False,
                reason="InfoQ: 8X is compound moderate gains — declare >=2 stacked factors",
            )
        report = stack_compound_speedups(gains)
        return Decision(
            action="allow_compound_speedup",
            ok=True,
            reason=f"compound speedup {report['compound_speedup_x']}X from {len(report['factors'])} factors",
        )

    if action in {"claim_ranking_quality", "claim_ndcg", "ship_distilled_ranker"}:
        if claim.get("ranking_quality_evidence") is not True and claim.get(
            "ndcg_reported"
        ) is not True:
            return Decision(
                action="block_quality_without_ndcg",
                ok=False,
                reason="InfoQ: report ranking quality evidence (e.g. NDCG@k) before claiming distill wins",
            )
        return Decision(
            action="allow_quality_backed_claim",
            ok=True,
            reason="ranking quality evidence present",
        )

    if action in {"serve_with_prune_compress", "optimize_student_serving"}:
        if claim.get("structured_pruning") is not True and claim.get(
            "context_compression"
        ) is not True:
            return Decision(
                action="block_serving_without_prune_or_compress",
                ok=False,
                reason="InfoQ: apply structured pruning and/or context compression for student serving throughput",
            )
        return Decision(
            action="allow_prune_compress_serving",
            ok=True,
            reason="prune and/or compress enabled for serving",
        )

    if action in {"run_offline_distill", "train_student_from_cache"}:
        if claim.get("teacher_cache_present") is not True:
            return Decision(
                action="block_offline_without_cache",
                ok=False,
                reason="offline distill requires teacher soft-label/embedding cache",
            )
        if claim.get("per_shard_invalidation") is not True and claim.get(
            "all_or_nothing_invalidate"
        ) is True:
            return Decision(
                action="block_all_or_nothing_invalidation",
                ok=False,
                reason="use per-shard cache invalidation, not all-or-nothing",
            )
        return Decision(
            action="allow_offline_student_train",
            ok=True,
            reason="student training from cached teacher signals",
        )

    if action in {"register_teacher", "add_teacher"}:
        role = norm(claim.get("role") or claim.get("teacher_role"))
        if role not in TEACHER_ROLES:
            return Decision(
                action="block_unknown_teacher_role",
                ok=False,
                reason="teacher role must be relevance|engagement|embedding|policy|click|critic",
            )
        if claim.get("pluggable") is not True:
            return Decision(
                action="block_non_pluggable_teacher",
                ok=False,
                reason="onboard teachers as pluggable components (no hardcoded architecture)",
            )
        return Decision(
            action="allow_pluggable_teacher",
            ok=True,
            reason=f"registered pluggable teacher role: {role}",
        )

    if action in {"claim_speedup", "report_distill_speedup"}:
        try:
            baseline = float(claim.get("baseline_hours") or 0)
            offline = float(claim.get("offline_student_hours") or 0)
        except (TypeError, ValueError):
            return Decision(
                action="block_invalid_speedup_inputs",
                ok=False,
                reason="declare numeric baseline_hours and offline_student_hours",
            )
        if baseline <= 0 or offline <= 0:
            return Decision(
                action="block_invalid_speedup_inputs",
                ok=False,
                reason="baseline_hours and offline_student_hours must be > 0",
            )
        report = estimate_distill_speedup(
            baseline_hours=baseline,
            offline_student_hours=offline,
            cache_generation_hours=float(claim.get("cache_generation_hours") or 0),
            amortize_over_student_runs=int(claim.get("amortize_over_student_runs") or 1),
        )
        if claim.get("require_8x") is True and not report["meets_8x_target"]:
            return Decision(
                action="block_speedup_below_8x",
                ok=False,
                reason=f"reported speedup {report['speedup_x']}X below LinkedIn 8X target",
            )
        return Decision(
            action="allow_speedup_report",
            ok=True,
            reason=f"amortized speedup {report['speedup_x']}X",
        )

    return Decision(
        action="block_unknown_distill_action",
        ok=False,
        reason=(
            "declare action: select_mode|select_phase|run_offline_distill|"
            "register_teacher|claim_speedup|stack_gains|claim_ranking_quality|"
            "serve_with_prune_compress"
        ),
    )


def evaluate(repo: Path) -> dict[str, Any]:
    blockers: list[str] = []
    if not (repo / "docs" / "MULTI_TEACHER_DISTILL.md").is_file():
        blockers.append("missing_docs/MULTI_TEACHER_DISTILL.md")
    if not (repo / "scripts" / "multi_teacher_distill_gate.py").is_file():
        blockers.append("missing_scripts/multi_teacher_distill_gate.py")
    blockers.extend(require_dual_skills(repo, "multi-teacher-distill-lite"))
    blockers.extend(
        require_docs_needles(
            repo / "docs" / "MULTI_TEACHER_DISTILL.md",
            (
                "multi-teacher",
                "offline",
                "online",
                "cache",
                "shard",
                "student",
                "pluggable",
                "soft label",
                "embedding",
                "8x",
                "stream",
                "sglang",
                "async",
                "stable",
                "compound",
                "fp8",
                "pruning",
                "compression",
                "ndcg",
            ),
        )
    )

    fixture = (
        repo
        / "marketing"
        / "data"
        / "code_health"
        / "multi_teacher_distill_discipline.json"
    )
    if not fixture.is_file():
        blockers.append(
            "missing_fixture:marketing/data/code_health/multi_teacher_distill_discipline.json"
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
            if (
                not isinstance(budget, dict)
                or budget.get("gpu_training_saas") is not False
            ):
                blockers.append("fixture_missing:budget.gpu_training_saas=false")

    ready = len(blockers) == 0
    return {
        "framework": "multi-teacher-distill-lite",
        "source": SOURCE,
        "infoq_source": INFOQ_SOURCE,
        "ready": ready,
        "blockers": blockers,
        "health_signals": list(HEALTH_SIGNALS),
        "modes": ["online", "offline", "reuse_cache"],
        "teacher_roles": sorted(TEACHER_ROLES),
        "anti_pattern": "full_teacher_rerun_on_every_student_iteration",
        "budget_note": (
            "offline teacher-signal cache + pluggable teachers + compact student; "
            "no GPU multi-node training SaaS under hard monthly cap"
        ),
        "pairs_with": [
            "docs/SEMANTIC_SEARCH_STACK.md",
            "docs/HYDRAFUSION_ROUTING.md",
            "docs/LLM_RESPONSE_CACHE.md",
            "docs/TRUST_RELIABILITY_LOOP.md",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    return run_presence_cli(
        description=__doc__ or "multi-teacher-distill-lite",
        evaluate=evaluate,
        claim_evaluator=evaluate_distill_claim,
        argv=argv,
    )


if __name__ == "__main__":
    raise SystemExit(main())
