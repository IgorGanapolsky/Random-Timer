"""Local-first hybrid router: selectively local on 16GB, escalate when needed.

Theme: “16GB Is All You Need for Serious AI” — do not chase hardware; route
private/repetitive/low-stakes work local and escalate hard public work to
frontier APIs under the $20 fleet cap.

Episode framing: https://music.youtube.com/watch?v=qILTuXLxfBM

Pipeline: classify → retrieve (caller) → local draft → cloud escalate on
confidence/complexity → human approval for consequential actions.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

FLEET_MONTHLY_CAP_USD = 20.0
LOCAL_MODEL = "local/hermes-cheap"
CLOUD_MODEL = "cloud/frontier"
COMPLEXITY_ESCALATE = 0.65
CONFIDENCE_ESCALATE = 0.45

ALLOWED_PLATFORMS = frozenset(
    {
        "local_first_hybrid",
        "agent_local_first_router",
        "local_first_router",
        "hybrid_local_cloud",
    }
)
CLOUD_ONLY_MARKERS = (
    "always_cloud",
    "cloud_only",
    "never_local",
    "wholesale_cloud",
)

LOCAL_TASKS = frozenset(
    {
        "routing",
        "classification",
        "extraction",
        "formatting",
        "summarization",
        "private_summary",
        "simple_coding",
        "test_generation",
        "draft_code",
    }
)
CLOUD_TASKS = frozenset(
    {
        "architecture",
        "hard_debugging",
        "agent_planning",
        "final_review",
        "long_context_coding",
    }
)


@dataclass(frozen=True)
class ControlDecision:
    action: str
    ok: bool
    reason: str
    lane: str = ""
    model: str = ""
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
            action="allow_local_first_hybrid",
            ok=True,
            reason="selectively local hybrid under fleet cap",
        )
    if any(marker in name for marker in CLOUD_ONLY_MARKERS):
        return ControlDecision(
            action="block_cloud_only_posture",
            ok=False,
            reason="reject wholesale cloud replacement of local workflow",
        )
    return ControlDecision(
        action="block_unknown_platform",
        ok=False,
        reason="unknown local-first platform denied",
    )


def classify_task(*, task_type: str) -> ControlDecision:
    name = _norm(task_type)
    if name in LOCAL_TASKS:
        return ControlDecision(
            action="prefer_local",
            ok=True,
            reason=f"{name} fits local small-model lane",
            lane="local",
            model=LOCAL_MODEL,
        )
    if name in CLOUD_TASKS:
        return ControlDecision(
            action="prefer_cloud",
            ok=True,
            reason=f"{name} fits frontier escalation lane",
            lane="cloud",
            model=CLOUD_MODEL,
        )
    return ControlDecision(
        action="block_unknown_task_type",
        ok=False,
        reason="classify task before selecting a model",
    )


def private_data_policy(
    *,
    contains_private_data: bool,
    allow_cloud: bool,
) -> ControlDecision:
    if contains_private_data:
        return ControlDecision(
            action="force_local_private_lane",
            ok=True,
            reason="private/client/credentials-adjacent data stays local",
            lane="local",
            model=LOCAL_MODEL,
        )
    if allow_cloud:
        return ControlDecision(
            action="allow_router_decide",
            ok=True,
            reason="non-private data may escalate under budget",
        )
    return ControlDecision(
        action="force_local_policy",
        ok=True,
        reason="cloud disabled by policy",
        lane="local",
        model=LOCAL_MODEL,
    )


def route_local_first(
    *,
    task_type: str,
    contains_private_data: bool,
    confidence: float,
    complexity: float,
    month_to_date_spend_usd: float,
    fleet_cap_usd: float = FLEET_MONTHLY_CAP_USD,
) -> ControlDecision:
    if contains_private_data:
        return ControlDecision(
            action="route_local",
            ok=True,
            reason="private-data lane forces local inference",
            lane="local",
            model=LOCAL_MODEL,
        )

    classified = classify_task(task_type=task_type)
    if not classified.ok:
        return classified

    remaining = fleet_cap_usd - float(month_to_date_spend_usd or 0.0)
    wants_cloud = classified.lane == "cloud" or (
        float(complexity) >= COMPLEXITY_ESCALATE
        and float(confidence) <= CONFIDENCE_ESCALATE
    )
    if wants_cloud and remaining <= 0:
        return ControlDecision(
            action="route_local_budget",
            ok=True,
            reason="fleet cap exhausted — stay local instead of escalating",
            lane="local",
            model=LOCAL_MODEL,
            score=remaining,
        )
    if wants_cloud:
        return ControlDecision(
            action="route_cloud",
            ok=True,
            reason="escalate hard/public work to frontier under fleet cap",
            lane="cloud",
            model=CLOUD_MODEL,
            score=remaining,
        )
    return ControlDecision(
        action="route_local",
        ok=True,
        reason="local small model sufficient for this task class",
        lane="local",
        model=LOCAL_MODEL,
        score=remaining,
    )


def evaluate_hardware_upgrade(
    *,
    local_inference_is_daily_bottleneck: bool,
    privacy_requires_larger_local: bool,
    paid_work_blocked_by_ram: bool,
) -> ControlDecision:
    if (
        local_inference_is_daily_bottleneck
        and privacy_requires_larger_local
        and paid_work_blocked_by_ram
    ):
        return ControlDecision(
            action="consider_32gb_unified",
            ok=True,
            reason="recurring paid/privacy bottleneck may justify 32GB unified memory",
        )
    return ControlDecision(
        action="keep_16gb_optimize_workflow",
        ok=True,
        reason="optimize routing before buying RAM; 16GB is enough for selective local",
    )


def log_run(
    *,
    path: Path,
    model: str,
    task_type: str,
    tokens: int,
    cost_usd: float,
    latency_ms: float,
    accepted: bool,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "model": model,
        "task_type": task_type,
        "tokens": int(tokens),
        "cost_usd": float(cost_usd),
        "latency_ms": float(latency_ms),
        "accepted": bool(accepted),
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row) + "\n")


def summarize_acceptance(*, path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {
            "runs": 0,
            "acceptance_rate": 0.0,
            "total_cost_usd": 0.0,
            "avg_latency_ms": 0.0,
        }
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    runs = len(rows)
    accepted = sum(1 for r in rows if r.get("accepted"))
    total_cost = sum(float(r.get("cost_usd") or 0.0) for r in rows)
    avg_latency = (
        sum(float(r.get("latency_ms") or 0.0) for r in rows) / runs if runs else 0.0
    )
    return {
        "runs": runs,
        "acceptance_rate": (accepted / runs) if runs else 0.0,
        "total_cost_usd": total_cost,
        "avg_latency_ms": avg_latency,
        "fleet_monthly_cap_usd": FLEET_MONTHLY_CAP_USD,
        "proxy_vs_ground_truth": (
            "acceptance_rate and cost_usd are run telemetry proxies; "
            "ledger cash remains separate."
        ),
    }


def template_pipeline(
    *,
    task_type: str,
    contains_private_data: bool,
    confidence: float,
    complexity: float,
    month_to_date_spend_usd: float,
    human_approval_required: bool,
) -> dict[str, Any]:
    platform = evaluate_platform(platform="local_first_hybrid")
    private = private_data_policy(
        contains_private_data=contains_private_data,
        allow_cloud=True,
    )
    route = route_local_first(
        task_type=task_type,
        contains_private_data=contains_private_data,
        confidence=confidence,
        complexity=complexity,
        month_to_date_spend_usd=month_to_date_spend_usd,
    )
    hardware = evaluate_hardware_upgrade(
        local_inference_is_daily_bottleneck=False,
        privacy_requires_larger_local=False,
        paid_work_blocked_by_ram=False,
    )
    steps = [
        "classify",
        "retrieve_context",
        "local_draft",
    ]
    if route.lane == "cloud":
        steps.append("cloud_escalate")
    if human_approval_required:
        steps.append("human_approval")
    steps.append("log_acceptance")
    ok = platform.ok and private.ok and route.ok
    return {
        "ok": ok,
        "fleet_monthly_cap_usd": FLEET_MONTHLY_CAP_USD,
        "platform": asdict(platform),
        "private_policy": asdict(private),
        "route": asdict(route),
        "hardware": asdict(hardware),
        "steps": steps,
        "local_model": LOCAL_MODEL,
        "cloud_model": CLOUD_MODEL,
    }


def main(argv: Sequence[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Local-first hybrid model router")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_route = sub.add_parser("route", help="route a task local vs cloud")
    p_route.add_argument("--task-type", required=True)
    p_route.add_argument("--private", action="store_true")
    p_route.add_argument("--confidence", type=float, default=0.7)
    p_route.add_argument("--complexity", type=float, default=0.3)
    p_route.add_argument("--month-to-date-usd", type=float, default=0.0)
    p_route.add_argument("--json", action="store_true")

    p_template = sub.add_parser("template", help="print local-first agent template")
    p_template.add_argument("--task-type", default="simple_coding")
    p_template.add_argument("--private", action="store_true")
    p_template.add_argument("--confidence", type=float, default=0.7)
    p_template.add_argument("--complexity", type=float, default=0.3)
    p_template.add_argument("--month-to-date-usd", type=float, default=0.0)
    p_template.add_argument("--hitl", action="store_true", default=True)
    p_template.add_argument("--json", action="store_true")

    p_sum = sub.add_parser("summary", help="summarize acceptance JSONL")
    p_sum.add_argument("--log", type=Path, required=True)
    p_sum.add_argument("--json", action="store_true")

    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.cmd == "route":
        d = route_local_first(
            task_type=args.task_type,
            contains_private_data=args.private,
            confidence=args.confidence,
            complexity=args.complexity,
            month_to_date_spend_usd=args.month_to_date_usd,
        )
        print(json.dumps(asdict(d), indent=2 if args.json else None))
        return 0 if d.ok else 2

    if args.cmd == "template":
        report = template_pipeline(
            task_type=args.task_type,
            contains_private_data=args.private,
            confidence=args.confidence,
            complexity=args.complexity,
            month_to_date_spend_usd=args.month_to_date_usd,
            human_approval_required=args.hitl,
        )
        print(json.dumps(report, indent=2 if args.json else None))
        return 0 if report["ok"] else 2

    summary = summarize_acceptance(path=args.log)
    print(json.dumps(summary, indent=2 if args.json else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
