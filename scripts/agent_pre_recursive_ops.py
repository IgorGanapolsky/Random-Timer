"""Pre-recursive agent ops: claim cards, HITL approval, application-layer wedges.

Themes from Dwarkesh RSI discussion (practical filter, not full RSI wait):
1. Capture claim → dependency → 12-month wedge → proof metric.
2. Prefer evaluation/verification tooling over unsupervised autonomy.
3. Compound loops: 2–5x engineer acceleration with humans in the loop.
4. Stay application-layer under FLEET_MONTHLY_CAP_USD ($20).

Episode URL (source framing only): https://music.youtube.com/watch?v=PrSf7IOYu-I
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

FLEET_MONTHLY_CAP_USD = 20.0

ALLOWED_PLATFORMS = frozenset(
    {
        "local_pre_recursive_ops",
        "agent_pre_recursive_ops",
        "local_rsi_wedge",
        "pre_recursive_ops",
    }
)
FOUNDATION_MARKERS = (
    "foundation_model",
    "foundation_lab",
    "pretrain",
    "pre_train",
    "lab_training",
    "cluster_training",
    "gpu_farm",
)

APPLICATION_BOTTLENECKS = frozenset(
    {
        "evaluation",
        "evals",
        "reliable_agents",
        "long_horizon",
        "data",
        "experiment_throughput",
        "human_review",
        "permissions",
        "coding_reliability",
        "browser_control",
    }
)

MIN_COMPOUND_SPEEDUP = 2.0
MAX_COMPOUND_SPEEDUP = 5.0


@dataclass(frozen=True)
class ControlDecision:
    action: str
    ok: bool
    reason: str
    score: float = 0.0


def _norm(value: str) -> str:
    return (
        (value or "")
        .strip()
        .lower()
        .replace("-", "_")
        .replace(".", "_")
        .replace(" ", "_")
    )


def evaluate_platform(*, platform: str) -> ControlDecision:
    name = _norm(platform)
    if name in ALLOWED_PLATFORMS:
        return ControlDecision(
            action="allow_local_pre_recursive_ops",
            ok=True,
            reason="local pre-recursive ops under operating cap",
        )
    if any(marker in name for marker in FOUNDATION_MARKERS):
        return ControlDecision(
            action="block_foundation_spend",
            ok=False,
            reason="foundation training/lab spend exceeds $20 fleet posture",
        )
    return ControlDecision(
        action="block_unknown_platform",
        ok=False,
        reason="unknown pre-recursive platform denied",
    )


def validate_claim_card(
    *,
    claim: str,
    dependency: str,
    wedge_12m: str,
    proof_metric: str,
) -> ControlDecision:
    fields = {
        "claim": (claim or "").strip(),
        "dependency": (dependency or "").strip(),
        "wedge_12m": (wedge_12m or "").strip(),
        "proof_metric": (proof_metric or "").strip(),
    }
    missing = [k for k, v in fields.items() if not v]
    if missing:
        return ControlDecision(
            action="block_incomplete_claim_card",
            ok=False,
            reason=f"missing fields: {', '.join(missing)}",
        )
    return ControlDecision(
        action="allow_claim_card",
        ok=True,
        reason="claim card complete (claim/dependency/wedge/proof)",
    )


def _wedge_score(row: Mapping[str, Any]) -> float:
    hours = float(row.get("hours_saved_per_week") or 0.0)
    effort = max(float(row.get("effort") or 1.0), 1.0)
    layer = _norm(str(row.get("layer") or ""))
    bottleneck = _norm(str(row.get("bottleneck") or ""))
    proof = (str(row.get("proof_metric") or "")).strip()
    score = hours / effort
    if layer == "application":
        score *= 3.0
    elif layer == "foundation":
        score *= 0.1
    if bottleneck in APPLICATION_BOTTLENECKS or any(
        b in bottleneck for b in ("eval", "agent", "review", "reliab")
    ):
        score *= 1.5
    if proof:
        score *= 1.25
    return score


def rank_wedges(*, cards: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    scored: list[tuple[float, dict[str, Any]]] = []
    for raw in cards:
        row = dict(raw)
        score = _wedge_score(row)
        row["score"] = score
        scored.append((score, row))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [row for _, row in scored]


def approval_gate(
    *,
    acceptance_met: bool,
    evidence_paths: Sequence[str],
    human_approved: bool,
    irreversible: bool,
) -> ControlDecision:
    if irreversible and not human_approved:
        return ControlDecision(
            action="block_irreversible_without_approval",
            ok=False,
            reason="irreversible actions require explicit human approval",
        )
    if human_approved and acceptance_met and evidence_paths:
        return ControlDecision(
            action="allow_human_approved",
            ok=True,
            reason="human approved with acceptance + evidence",
        )
    if acceptance_met and evidence_paths and not irreversible:
        return ControlDecision(
            action="allow_auto_with_evidence",
            ok=True,
            reason="reversible path cleared by acceptance + evidence",
        )
    return ControlDecision(
        action="require_human_review",
        ok=False,
        reason="incomplete acceptance/evidence — escalate to human review",
    )


def compound_loop_policy(
    *,
    target_speedup: float,
    human_in_loop: bool,
    replaces_engineer: bool,
) -> ControlDecision:
    if replaces_engineer or not human_in_loop:
        return ControlDecision(
            action="block_full_replacement",
            ok=False,
            reason="require human-in-the-loop acceleration, not full replacement",
        )
    if target_speedup < MIN_COMPOUND_SPEEDUP or target_speedup > MAX_COMPOUND_SPEEDUP:
        return ControlDecision(
            action="block_unrealistic_speedup",
            ok=False,
            reason=f"target speedup must be in [{MIN_COMPOUND_SPEEDUP}, {MAX_COMPOUND_SPEEDUP}]x",
        )
    return ControlDecision(
        action="allow_compound_loop",
        ok=True,
        reason="2–5x engineer acceleration with human review gate",
    )


def select_infra_posture(
    *,
    needs_foundation_training: bool,
    month_to_date_spend_usd: float,
    fleet_cap_usd: float = FLEET_MONTHLY_CAP_USD,
) -> ControlDecision:
    if needs_foundation_training:
        return ControlDecision(
            action="block_foundation_under_cap",
            ok=False,
            reason=f"foundation training incompatible with ${fleet_cap_usd:.0f}/mo fleet cap",
        )
    remaining = fleet_cap_usd - float(month_to_date_spend_usd or 0.0)
    if remaining < 0:
        return ControlDecision(
            action="block_budget_exhausted",
            ok=False,
            reason="fleet monthly cap already exceeded",
        )
    return ControlDecision(
        action="application_layer_automation",
        ok=True,
        reason="prefer application-layer agent ops with eval + approval",
        score=remaining,
    )


def plan_ops_wedge(
    *,
    platform: str,
    claim: str,
    dependency: str,
    wedge_12m: str,
    proof_metric: str,
    layer: str,
    bottleneck: str,
    hours_saved_per_week: float,
    effort: float,
    target_speedup: float,
    human_in_loop: bool,
    replaces_engineer: bool,
    acceptance_met: bool,
    evidence_paths: Sequence[str],
    human_approved: bool,
    irreversible: bool,
    needs_foundation_training: bool,
    month_to_date_spend_usd: float,
) -> dict[str, Any]:
    platform_d = evaluate_platform(platform=platform)
    claim_d = validate_claim_card(
        claim=claim,
        dependency=dependency,
        wedge_12m=wedge_12m,
        proof_metric=proof_metric,
    )
    ranked = rank_wedges(
        cards=(
            {
                "id": "candidate",
                "claim": claim,
                "dependency": dependency,
                "wedge_12m": wedge_12m,
                "proof_metric": proof_metric,
                "layer": layer,
                "bottleneck": bottleneck,
                "hours_saved_per_week": hours_saved_per_week,
                "effort": effort,
            },
        )
    )
    compound = compound_loop_policy(
        target_speedup=target_speedup,
        human_in_loop=human_in_loop,
        replaces_engineer=replaces_engineer,
    )
    approval = approval_gate(
        acceptance_met=acceptance_met,
        evidence_paths=evidence_paths,
        human_approved=human_approved,
        irreversible=irreversible,
    )
    infra = select_infra_posture(
        needs_foundation_training=needs_foundation_training,
        month_to_date_spend_usd=month_to_date_spend_usd,
    )
    ok = (
        platform_d.ok
        and claim_d.ok
        and compound.ok
        and approval.ok
        and infra.ok
        and float(ranked[0].get("score") or 0.0) > 0.0
    )
    return {
        "ok": ok,
        "fleet_monthly_cap_usd": FLEET_MONTHLY_CAP_USD,
        "platform": asdict(platform_d),
        "claim_card": asdict(claim_d),
        "ranked_wedge": ranked[0],
        "compound_loop": asdict(compound),
        "approval": asdict(approval),
        "infra": asdict(infra),
        "proxy_vs_ground_truth": {
            "note": (
                "hours_saved_per_week and speedup targets are planning proxies; "
                "verify with timed before/after evidence before claiming ROI."
            )
        },
    }


def main(argv: Sequence[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Pre-recursive agent ops planner")
    parser.add_argument("--platform", default="local_pre_recursive_ops")
    parser.add_argument("--claim", default="")
    parser.add_argument("--dependency", default="")
    parser.add_argument("--wedge", default="")
    parser.add_argument("--proof-metric", default="")
    parser.add_argument("--layer", default="application")
    parser.add_argument("--bottleneck", default="evaluation")
    parser.add_argument("--hours-saved", type=float, default=4.0)
    parser.add_argument("--effort", type=float, default=2.0)
    parser.add_argument("--speedup", type=float, default=3.0)
    parser.add_argument("--hitl", action="store_true", default=True)
    parser.add_argument("--no-hitl", action="store_true")
    parser.add_argument("--replace-engineer", action="store_true")
    parser.add_argument("--acceptance-met", action="store_true")
    parser.add_argument("--evidence", action="append", default=[])
    parser.add_argument("--human-approved", action="store_true")
    parser.add_argument("--irreversible", action="store_true")
    parser.add_argument("--foundation", action="store_true")
    parser.add_argument("--month-to-date-usd", type=float, default=0.0)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)

    report = plan_ops_wedge(
        platform=args.platform,
        claim=args.claim,
        dependency=args.dependency,
        wedge_12m=args.wedge,
        proof_metric=args.proof_metric,
        layer=args.layer,
        bottleneck=args.bottleneck,
        hours_saved_per_week=args.hours_saved,
        effort=args.effort,
        target_speedup=args.speedup,
        human_in_loop=not args.no_hitl,
        replaces_engineer=args.replace_engineer,
        acceptance_met=args.acceptance_met,
        evidence_paths=tuple(args.evidence or ()),
        human_approved=args.human_approved,
        irreversible=args.irreversible,
        needs_foundation_training=args.foundation,
        month_to_date_spend_usd=args.month_to_date_usd,
    )
    print(json.dumps(report, indent=2 if args.json else None))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
