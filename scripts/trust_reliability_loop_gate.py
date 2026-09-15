#!/usr/bin/env python3
"""Trust Reliability Loop lite — scope, eval, tiered inference, recommend-first.

Source thesis (always-on consumer AI assistant economics):
  https://music.youtube.com/watch?v=Xa1jm2VWEHk

Episode constraint: long-running agents, evaluation, user trust, and flat-
subscription unit economics. Highest ROI is NOT more autonomy — it is tighter
scope, cheaper inference, and a measurable trust/reliability loop.

High-ROI steals for Random Timer agent ops ($20/mo hard cap):
  - Narrow to a few high-frequency, high-stakes workflows
  - Eval-first: log candidates, actions, corrections, outcomes; precision by workflow
  - Tiered inference: rules → classify → extract → premium → user confirm
  - Recommend-first / read-only default; progressive autonomy per action class
  - Explicit editable memory with provenance
  - Alert precision over coverage (budget, quiet hours, escalate only if time-sensitive)
  - Instrument cost per retained user / household; event-driven, not continuous reasoning
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

SOURCE = "https://music.youtube.com/watch?v=Xa1jm2VWEHk"

HEALTH_SIGNALS = (
    "narrow_workflow_scope",
    "eval_first_logging",
    "tiered_inference",
    "recommend_first",
    "progressive_autonomy",
    "explicit_editable_memory",
    "alert_precision_over_coverage",
    "cost_per_retained",
    "event_driven",
)

INFERENCE_TIERS = (
    "rules",
    "classify",
    "extract",
    "premium",
    "confirm",
)

NARROW_WORKFLOWS = frozenset(
    {
        "ops_daily_brief",
        "paywall_failure_alert",
        "wqtu_north_star_alert",
        "release_conflict_alert",
        "ci_precision_alert",
    }
)

CONTINUOUS_ACTIONS = frozenset(
    {
        "run_continuous_agent",
        "always_on_reasoning",
        "poll_without_event",
        "unbounded_background_think",
    }
)

OPEN_ENDED_ACTIONS = frozenset(
    {
        "expand_general_purpose_chat",
        "do_anything_agent",
        "unbounded_multi_agent_orchestration",
        "broad_integration_before_retention",
    }
)

EXTERNAL_WRITE_ACTIONS = frozenset(
    {
        "send_message",
        "alter_calendar",
        "make_purchase",
        "post_externally",
        "mutate_store_listing",
    }
)


def select_inference_tier(
    *,
    ambiguity: float,
    consequential: bool,
    needs_synthesis: bool,
    needs_structured_fields: bool = False,
) -> str:
    """Decision ladder: cheapest tier that can clear the quality bar."""
    if consequential:
        return "confirm"
    if needs_synthesis or ambiguity >= 0.7:
        return "premium"
    if needs_structured_fields or ambiguity >= 0.35:
        return "extract"
    if ambiguity >= 0.1:
        return "classify"
    return "rules"


def _precision(true_positives: object, false_positives: object) -> float | None:
    try:
        tp = float(true_positives)  # type: ignore[arg-type]
        fp = float(false_positives)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    denom = tp + fp
    if denom <= 0:
        return None
    return tp / denom


def evaluate_ops_claim(claim: Mapping[str, object]) -> Decision:
    action = norm(claim.get("action"))

    if action in CONTINUOUS_ACTIONS:
        return Decision(
            action="block_continuous_reasoning",
            ok=False,
            reason="event-driven ingest only — no continuous always-on reasoning under flat economics",
        )

    if action in OPEN_ENDED_ACTIONS:
        return Decision(
            action="block_open_ended_scope",
            ok=False,
            reason="narrow to measured high-frequency workflows; defer general-purpose do-anything agents",
        )

    if action in EXTERNAL_WRITE_ACTIONS:
        confirmed = claim.get("user_confirmed") is True
        grant = claim.get("autonomy_grant")
        if not confirmed and not grant:
            return Decision(
                action="block_unconfirmed_external_action",
                ok=False,
                reason="recommend-first: require user_confirmed or progressive autonomy_grant for external writes",
            )
        if claim.get("eval_logged") is not True:
            return Decision(
                action="block_external_without_eval",
                ok=False,
                reason="eval-first: log outcome before/with consequential external actions",
            )
        if not str(claim.get("source_url") or "").strip():
            return Decision(
                action="block_external_without_provenance",
                ok=False,
                reason="provenance required for consequential actions",
            )
        return Decision(
            action="allow_progressive_autonomy_action",
            ok=True,
            reason="confirmed or granted external action with eval + provenance",
        )

    if action in {"emit_alert", "surface_alert"}:
        workflow = norm(claim.get("workflow_id"))
        if workflow and workflow not in NARROW_WORKFLOWS:
            return Decision(
                action="block_unscoped_workflow",
                ok=False,
                reason="alerts must bind to a narrow measured workflow_id",
            )
        if claim.get("eval_logged") is not True:
            return Decision(
                action="block_alert_without_eval",
                ok=False,
                reason="eval-first: log candidate alert before emit",
            )
        if not str(claim.get("source_url") or "").strip():
            return Decision(
                action="block_alert_without_provenance",
                ok=False,
                reason="every alert needs source_url provenance",
            )
        budget = claim.get("alert_budget_remaining")
        time_sensitive = claim.get("time_sensitive") is True
        if budget is not None:
            try:
                remaining = float(budget)  # type: ignore[arg-type]
            except (TypeError, ValueError):
                remaining = -1.0
            if remaining <= 0 and not time_sensitive:
                return Decision(
                    action="block_alert_over_budget",
                    ok=False,
                    reason="alert precision over coverage: respect alert budget unless time_sensitive",
                )
        return Decision(
            action="allow_scoped_alert",
            ok=True,
            reason="scoped alert with eval log, provenance, and budget discipline",
        )

    if action in {"recommend", "propose_action", "daily_brief"}:
        if claim.get("eval_logged") is not True:
            return Decision(
                action="block_recommend_without_eval",
                ok=False,
                reason="eval-first: log recommend candidates",
            )
        if not str(claim.get("source_url") or "").strip():
            return Decision(
                action="block_recommend_without_provenance",
                ok=False,
                reason="provenance required on recommend-first surfaces",
            )
        mode = norm(claim.get("mode") or "recommend_first")
        if mode not in {"recommend_first", "read_only", "draft_only"}:
            return Decision(
                action="block_autonomous_recommend_mode",
                ok=False,
                reason="default recommend_first|read_only|draft_only — not silent apply",
            )
        return Decision(
            action="allow_recommend_first",
            ok=True,
            reason="recommend-first proposal with provenance",
        )

    if action in {"claim_alert_precision", "report_precision"}:
        if claim.get("eval_logged") is not True:
            return Decision(
                action="block_precision_without_eval",
                ok=False,
                reason="precision claims require eval_logged=true",
            )
        if not norm(claim.get("workflow_id")):
            return Decision(
                action="block_precision_without_workflow",
                ok=False,
                reason="optimize precision/recall by workflow_id, not generic agent quality",
            )
        prec = _precision(claim.get("true_positives"), claim.get("false_positives"))
        if prec is None:
            return Decision(
                action="block_precision_missing_counts",
                ok=False,
                reason="declare true_positives and false_positives",
            )
        return Decision(
            action="allow_precision_claim",
            ok=True,
            reason=f"workflow precision={prec:.3f}",
        )

    if action in {"claim_unit_economics", "report_cost_per_retained"}:
        if claim.get("cost_per_retained") is None and claim.get("retained_users") is None:
            return Decision(
                action="block_cost_without_retained_metric",
                ok=False,
                reason="instrument cost_per_retained (or retained_users) — not raw token spend alone",
            )
        if claim.get("cost_units") is None:
            return Decision(
                action="block_cost_missing_units",
                ok=False,
                reason="declare cost_units for the window",
            )
        return Decision(
            action="allow_unit_economics_claim",
            ok=True,
            reason="cost-per-retained claim has required fields",
        )

    if action in {"select_tier", "route_inference"}:
        tier = select_inference_tier(
            ambiguity=float(claim.get("ambiguity") or 0.0),
            consequential=bool(claim.get("consequential")),
            needs_synthesis=bool(claim.get("needs_synthesis")),
            needs_structured_fields=bool(claim.get("needs_structured_fields")),
        )
        return Decision(
            action=f"allow_tier_{tier}",
            ok=True,
            reason=f"selected inference tier: {tier}",
        )

    if action in {"edit_memory", "forget_memory", "show_memory_why"}:
        if not str(claim.get("memory_key") or "").strip():
            return Decision(
                action="block_opaque_memory",
                ok=False,
                reason="explicit memory requires memory_key + editable controls",
            )
        return Decision(
            action="allow_explicit_memory_control",
            ok=True,
            reason="editable memory with named key",
        )

    return Decision(
        action="block_unknown_trust_loop_action",
        ok=False,
        reason=(
            "declare action: recommend|emit_alert|send_message|select_tier|"
            "claim_alert_precision|claim_unit_economics|edit_memory"
        ),
    )


def evaluate(repo: Path) -> dict[str, Any]:
    blockers: list[str] = []
    if not (repo / "docs" / "TRUST_RELIABILITY_LOOP.md").is_file():
        blockers.append("missing_docs/TRUST_RELIABILITY_LOOP.md")
    if not (repo / "scripts" / "trust_reliability_loop_gate.py").is_file():
        blockers.append("missing_scripts/trust_reliability_loop_gate.py")
    blockers.extend(require_dual_skills(repo, "trust-reliability-loop-lite"))
    blockers.extend(
        require_docs_needles(
            repo / "docs" / "TRUST_RELIABILITY_LOOP.md",
            (
                "narrow",
                "eval-first",
                "tiered inference",
                "recommend-first",
                "progressive autonomy",
                "editable memory",
                "alert precision",
                "cost per retained",
                "event-driven",
                "provenance",
            ),
        )
    )

    fixture = (
        repo / "marketing" / "data" / "code_health" / "trust_reliability_loop_discipline.json"
    )
    if not fixture.is_file():
        blockers.append(
            "missing_fixture:marketing/data/code_health/trust_reliability_loop_discipline.json"
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
                or budget.get("continuous_always_on_reasoning") is not False
            ):
                blockers.append(
                    "fixture_missing:budget.continuous_always_on_reasoning=false"
                )

    workflow = repo / "marketing" / "data" / "workflows" / "ops_daily_brief.json"
    if not workflow.is_file():
        blockers.append("missing_fixture:marketing/data/workflows/ops_daily_brief.json")
    else:
        try:
            brief = json.loads(workflow.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            blockers.append(f"ops_daily_brief_invalid_json:{exc}")
        else:
            if brief.get("workflow_id") != "ops_daily_brief":
                blockers.append("ops_daily_brief_missing:workflow_id")
            if brief.get("mode") != "recommend_first":
                blockers.append("ops_daily_brief_missing:mode=recommend_first")
            if not brief.get("metric"):
                blockers.append("ops_daily_brief_missing:metric")

    ready = len(blockers) == 0
    return {
        "framework": "trust-reliability-loop-lite",
        "source": SOURCE,
        "ready": ready,
        "blockers": blockers,
        "health_signals": list(HEALTH_SIGNALS),
        "inference_tiers": list(INFERENCE_TIERS),
        "narrow_workflows": sorted(NARROW_WORKFLOWS),
        "kpis": [
            "weekly_retained_users",
            "actionable_alert_precision",
            "correction_rate",
            "cost_per_retained_user",
            "progressive_autonomy_grant_rate",
            "wqtu",
        ],
        "anti_pattern": "more_autonomy_without_eval_or_margins",
        "budget_note": (
            "local eval + tiered ladder + recommend-first; no always-on continuous "
            "reasoning SaaS under hard monthly cap"
        ),
    }


def main(argv: list[str] | None = None) -> int:
    return run_presence_cli(
        description=__doc__ or "trust-reliability-loop-lite",
        evaluate=evaluate,
        claim_evaluator=evaluate_ops_claim,
        argv=argv,
    )


if __name__ == "__main__":
    raise SystemExit(main())
