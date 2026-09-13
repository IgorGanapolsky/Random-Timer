"""AI tool bake-off: classify work, score tools, ROI gate, productionize.

From “What to Use the Latest AI Tools For” (AI Breakdown) practical filter:
https://music.youtube.com/watch?v=Y2hE6kYZPg0

Do not tool-shop. Pick one bottleneck, classify the work, bake off two
candidates for 60–90 minutes, keep the winner only past the ROI gate, then
productionize with template + validation + logging + HITL + fallback.

Fleet cap: FLEET_MONTHLY_CAP_USD ($20).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

FLEET_MONTHLY_CAP_USD = 20.0
MIN_HOURS_SAVED_PER_MONTH = 2.0
MIN_USABLE_OUTPUT_RATE = 0.5

WORK_KINDS = frozenset(
    {
        "reasoning",
        "coding",
        "research",
        "computer_use",
        "automation",
    }
)

ALLOWED_PLATFORMS = frozenset(
    {
        "local_tool_bakeoff",
        "agent_tool_bakeoff",
        "ai_tool_bakeoff",
    }
)
SHOPPING_MARKERS = (
    "tool_shopping",
    "unbounded_tool",
    "demo_chasing",
    "hype_cycle",
)


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
            action="allow_local_tool_bakeoff",
            ok=True,
            reason="bounded bake-off under operating cap",
        )
    if any(marker in name for marker in SHOPPING_MARKERS):
        return ControlDecision(
            action="block_tool_shopping",
            ok=False,
            reason="reject unbounded tool shopping; pick one bottleneck first",
        )
    return ControlDecision(
        action="block_unknown_platform",
        ok=False,
        reason="unknown bake-off platform denied",
    )


def classify_work(*, kind: str) -> ControlDecision:
    name = _norm(kind)
    if name in WORK_KINDS:
        return ControlDecision(
            action="allow_work_class",
            ok=True,
            reason=f"work classified as {name}",
        )
    return ControlDecision(
        action="block_unknown_work_class",
        ok=False,
        reason="classify as reasoning|coding|research|computer_use|automation",
    )


def require_bottleneck(*, bottleneck: str) -> ControlDecision:
    if (bottleneck or "").strip():
        return ControlDecision(
            action="allow_bottleneck",
            ok=True,
            reason="bottleneck named",
        )
    return ControlDecision(
        action="block_missing_bottleneck",
        ok=False,
        reason="name one real bottleneck before selecting tools",
    )


def score_candidate(
    *,
    setup_minutes: float,
    usable_output_rate: float,
    human_correction_minutes: float,
    cost_usd_per_task: float,
    safely_repeatable: bool,
) -> ControlDecision:
    rate = float(usable_output_rate)
    if rate < MIN_USABLE_OUTPUT_RATE:
        return ControlDecision(
            action="block_low_usable_output",
            ok=False,
            reason=f"usable_output_rate {rate:.2f} < {MIN_USABLE_OUTPUT_RATE}",
        )
    if not safely_repeatable:
        return ControlDecision(
            action="block_not_repeatable",
            ok=False,
            reason="candidate cannot be safely repeated",
        )
    # Higher usable rate and lower correction/setup/cost → higher score
    friction = (
        max(float(setup_minutes), 0.0)
        + max(float(human_correction_minutes), 0.0)
        + max(float(cost_usd_per_task), 0.0) * 60.0
    )
    score = (rate * 100.0) / max(friction, 1.0)
    return ControlDecision(
        action="candidate_viable",
        ok=True,
        reason="usable, repeatable candidate",
        score=score,
    )


def evaluate_roi_gate(
    *,
    hours_saved_per_month: float,
    quality_or_speed_improved: bool,
    enables_chargeable_offer: bool,
    month_to_date_spend_usd: float,
    incremental_tool_usd_per_month: float,
    fleet_cap_usd: float = FLEET_MONTHLY_CAP_USD,
) -> ControlDecision:
    projected = float(month_to_date_spend_usd) + float(incremental_tool_usd_per_month)
    if projected > fleet_cap_usd:
        return ControlDecision(
            action="block_budget_cap",
            ok=False,
            reason=f"projected ${projected:.2f} exceeds ${fleet_cap_usd:.0f}/mo fleet cap",
        )
    clears = (
        float(hours_saved_per_month) >= MIN_HOURS_SAVED_PER_MONTH
        or quality_or_speed_improved
        or enables_chargeable_offer
    )
    if not clears:
        return ControlDecision(
            action="block_roi_gate",
            ok=False,
            reason=(
                f"need >={MIN_HOURS_SAVED_PER_MONTH:.0f}h/mo saved, "
                "quality/speed lift, or chargeable offer"
            ),
        )
    return ControlDecision(
        action="keep_winner",
        ok=True,
        reason="ROI gate cleared under fleet cap",
    )


def productionize_ready(
    *,
    has_prompt_template: bool,
    has_structured_io: bool,
    has_output_validation: bool,
    has_run_logging: bool,
    requires_human_approval: bool,
    has_manual_fallback: bool,
) -> ControlDecision:
    checks = {
        "prompt_template": has_prompt_template,
        "structured_io": has_structured_io,
        "output_validation": has_output_validation,
        "run_logging": has_run_logging,
        "human_approval": requires_human_approval,
        "manual_fallback": has_manual_fallback,
    }
    missing = [k for k, ok in checks.items() if not ok]
    if missing:
        return ControlDecision(
            action="block_not_production_ready",
            ok=False,
            reason=f"missing: {', '.join(missing)}",
        )
    return ControlDecision(
        action="allow_productionize",
        ok=True,
        reason="template, validation, logging, HITL, and fallback present",
    )


def bakeoff_compare(
    *,
    a: Mapping[str, Any],
    b: Mapping[str, Any],
) -> dict[str, Any]:
    scored_a = score_candidate(
        setup_minutes=float(a.get("setup_minutes") or 0),
        usable_output_rate=float(a.get("usable_output_rate") or 0),
        human_correction_minutes=float(a.get("human_correction_minutes") or 0),
        cost_usd_per_task=float(a.get("cost_usd_per_task") or 0),
        safely_repeatable=bool(a.get("safely_repeatable")),
    )
    scored_b = score_candidate(
        setup_minutes=float(b.get("setup_minutes") or 0),
        usable_output_rate=float(b.get("usable_output_rate") or 0),
        human_correction_minutes=float(b.get("human_correction_minutes") or 0),
        cost_usd_per_task=float(b.get("cost_usd_per_task") or 0),
        safely_repeatable=bool(b.get("safely_repeatable")),
    )
    a_id = str(a.get("id") or "a")
    b_id = str(b.get("id") or "b")
    if scored_a.ok and (not scored_b.ok or scored_a.score >= scored_b.score):
        winner = a_id
    elif scored_b.ok:
        winner = b_id
    else:
        winner = ""
    return {
        "winner_id": winner,
        "a": {"id": a_id, **asdict(scored_a)},
        "b": {"id": b_id, **asdict(scored_b)},
    }


def plan_bakeoff(
    *,
    platform: str,
    bottleneck: str,
    work_kind: str,
    a: Mapping[str, Any],
    b: Mapping[str, Any],
    hours_saved_per_month: float,
    quality_or_speed_improved: bool,
    enables_chargeable_offer: bool,
    month_to_date_spend_usd: float,
    incremental_tool_usd_per_month: float,
    has_prompt_template: bool,
    has_structured_io: bool,
    has_output_validation: bool,
    has_run_logging: bool,
    requires_human_approval: bool,
    has_manual_fallback: bool,
) -> dict[str, Any]:
    platform_d = evaluate_platform(platform=platform)
    bottleneck_d = require_bottleneck(bottleneck=bottleneck)
    work_d = classify_work(kind=work_kind)
    bakeoff = bakeoff_compare(a=a, b=b)
    roi = evaluate_roi_gate(
        hours_saved_per_month=hours_saved_per_month,
        quality_or_speed_improved=quality_or_speed_improved,
        enables_chargeable_offer=enables_chargeable_offer,
        month_to_date_spend_usd=month_to_date_spend_usd,
        incremental_tool_usd_per_month=incremental_tool_usd_per_month,
    )
    prod = productionize_ready(
        has_prompt_template=has_prompt_template,
        has_structured_io=has_structured_io,
        has_output_validation=has_output_validation,
        has_run_logging=has_run_logging,
        requires_human_approval=requires_human_approval,
        has_manual_fallback=has_manual_fallback,
    )
    ok = (
        platform_d.ok
        and bottleneck_d.ok
        and work_d.ok
        and bool(bakeoff.get("winner_id"))
        and roi.ok
        and prod.ok
    )
    return {
        "ok": ok,
        "fleet_monthly_cap_usd": FLEET_MONTHLY_CAP_USD,
        "min_hours_saved_per_month": MIN_HOURS_SAVED_PER_MONTH,
        "platform": asdict(platform_d),
        "bottleneck": asdict(bottleneck_d),
        "work": asdict(work_d),
        "bakeoff": bakeoff,
        "roi": asdict(roi),
        "productionize": asdict(prod),
        "proxy_vs_ground_truth": {
            "note": (
                "hours_saved_per_month and usable_output_rate are experiment proxies; "
                "verify with timed before/after runs before claiming production ROI."
            )
        },
    }


def main(argv: Sequence[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="AI tool bake-off planner")
    parser.add_argument("--platform", default="local_tool_bakeoff")
    parser.add_argument("--bottleneck", default="")
    parser.add_argument("--kind", default="coding")
    parser.add_argument("--a-id", default="tool_a")
    parser.add_argument("--b-id", default="tool_b")
    parser.add_argument("--a-setup", type=float, default=15.0)
    parser.add_argument("--b-setup", type=float, default=15.0)
    parser.add_argument("--a-usable", type=float, default=0.8)
    parser.add_argument("--b-usable", type=float, default=0.5)
    parser.add_argument("--a-correct", type=float, default=15.0)
    parser.add_argument("--b-correct", type=float, default=30.0)
    parser.add_argument("--a-cost", type=float, default=0.05)
    parser.add_argument("--b-cost", type=float, default=0.05)
    parser.add_argument("--a-repeatable", action="store_true", default=True)
    parser.add_argument("--b-repeatable", action="store_true", default=True)
    parser.add_argument("--b-not-repeatable", action="store_true")
    parser.add_argument("--hours-saved", type=float, default=3.0)
    parser.add_argument("--quality", action="store_true")
    parser.add_argument("--chargeable", action="store_true")
    parser.add_argument("--month-to-date-usd", type=float, default=0.0)
    parser.add_argument("--tool-usd", type=float, default=0.0)
    parser.add_argument("--template", action="store_true")
    parser.add_argument("--structured-io", action="store_true")
    parser.add_argument("--validation", action="store_true")
    parser.add_argument("--logging", action="store_true")
    parser.add_argument("--hitl", action="store_true")
    parser.add_argument("--fallback", action="store_true")
    parser.add_argument("--production-ready", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)

    prod_flags = bool(args.production_ready)
    report = plan_bakeoff(
        platform=args.platform,
        bottleneck=args.bottleneck,
        work_kind=args.kind,
        a={
            "id": args.a_id,
            "setup_minutes": args.a_setup,
            "usable_output_rate": args.a_usable,
            "human_correction_minutes": args.a_correct,
            "cost_usd_per_task": args.a_cost,
            "safely_repeatable": args.a_repeatable,
        },
        b={
            "id": args.b_id,
            "setup_minutes": args.b_setup,
            "usable_output_rate": args.b_usable,
            "human_correction_minutes": args.b_correct,
            "cost_usd_per_task": args.b_cost,
            "safely_repeatable": (not args.b_not_repeatable) and args.b_repeatable,
        },
        hours_saved_per_month=args.hours_saved,
        quality_or_speed_improved=args.quality or prod_flags,
        enables_chargeable_offer=args.chargeable,
        month_to_date_spend_usd=args.month_to_date_usd,
        incremental_tool_usd_per_month=args.tool_usd,
        has_prompt_template=args.template or prod_flags,
        has_structured_io=args.structured_io or prod_flags,
        has_output_validation=args.validation or prod_flags,
        has_run_logging=args.logging or prod_flags,
        requires_human_approval=args.hitl or prod_flags,
        has_manual_fallback=args.fallback or prod_flags,
    )
    print(json.dumps(report, indent=2 if args.json else None))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
