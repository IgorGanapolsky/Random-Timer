#!/usr/bin/env python3
"""AI Operating Model lite — adoption as process change, not tool rollout.

Source thesis (podcast / YouTube Music summary):
  https://music.youtube.com/watch?v=c-u8E15Lj8s

Highest-ROI takeaway: treat AI adoption as an **operating-model change**, not a
model-license rollout. Invest in process redesign, manager-led habits, and
measurable behavior — before buying more seats or APIs. Under the $20/mo hard
cap that means enablement + SOP rebuild + weekly ritual beat another SaaS.

Pairs with `docs/WORKFLOW_ECONOMICS.md` (completion loop + economic metrics).
This gate owns the adoption playbook: one workflow, AI-native SOP, enablement
before spend, weekly ritual, outcome metrics, 30-day pilot, ROI with full cost.
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

SOURCE = "https://music.youtube.com/watch?v=c-u8E15Lj8s"

HEALTH_SIGNALS = (
    "operating_model_not_tool_rollout",
    "one_workflow_clear_owner",
    "baseline_before_ai",
    "rebuild_ai_native_sop",
    "enablement_before_tool_spend",
    "weekly_ai_operating_ritual",
    "measure_behavior_not_logins",
    "roi_includes_total_cost",
    "thirty_day_pilot_then_expand",
)

# High-leverage pilots for this repo (frequent, measurable, painful).
PREFERRED_WORKFLOWS = frozenset(
    {
        "intake_to_delivery",
        "native_release_completion",
        "paywall_attempt_success_ops",
        "engineering_ticket_spec",
        "store_support_triage",
        "internal_research",
    }
)


def score_workflow_priority(claim: Mapping[str, object]) -> dict[str, Any]:
    """Heuristic: high volume + labor + manager enforcement + fast deploy."""
    volume = float(claim.get("volume_score") or 0)
    labor = float(claim.get("labor_cost_score") or 0)
    qa_ok = claim.get("low_error_after_qa") is True
    fast = claim.get("fast_deploy") is True
    manager = claim.get("manager_enforces") is True
    score = volume + labor
    if qa_ok:
        score += 1.0
    if fast:
        score += 1.0
    if manager:
        score += 2.0
    return {
        "score": score,
        "pursue": score >= 5.0 and manager,
        "workflow": str(claim.get("workflow") or "").strip(),
    }


def compute_roi(*, financial_value: float, total_cost: float) -> dict[str, Any]:
    """ROI = (financial_value - total_cost) / total_cost — total_cost includes labor."""
    if total_cost <= 0:
        return {"ok": False, "roi": None, "reason": "total_cost_must_be_positive"}
    roi = (financial_value - total_cost) / total_cost
    return {"ok": True, "roi": roi, "reason": "roi_computed"}


def evaluate_operating_model_claim(claim: Mapping[str, object]) -> Decision:
    action = norm(claim.get("action"))

    if action in {
        "buy_more_licenses_first",
        "tool_rollout_without_sop",
        "expand_seats_before_enablement",
        "reward_prompt_count",
        "reward_seat_utilization",
    }:
        return Decision(
            action="block_tool_rollout_first",
            ok=False,
            reason=(
                "AI adoption is an operating-model change — redesign SOP, "
                "fund enablement, measure outcomes before more licenses"
            ),
        )

    if action in {"pick_workflow", "select_pilot"}:
        wf = norm(claim.get("workflow"))
        owner = str(claim.get("owner") or "").strip()
        if not owner:
            return Decision(
                action="block_missing_owner",
                ok=False,
                reason="one expensive repetitive workflow needs a clear owner",
            )
        if claim.get("baseline_captured") is not True:
            return Decision(
                action="block_missing_baseline",
                ok=False,
                reason="capture time/cost/quality/throughput baseline before AI",
            )
        return Decision(
            action="allow_workflow_pilot",
            ok=True,
            reason=f"pilot workflow={wf or 'unnamed'} owner={owner}",
        )

    if action in {"rebuild_sop", "ai_native_sop"}:
        required = (
            "human_inputs",
            "model_outputs",
            "mandatory_checks",
            "approvals",
            "logged_artifacts",
        )
        missing = [k for k in required if not claim.get(k)]
        if missing:
            return Decision(
                action="block_incomplete_sop",
                ok=False,
                reason=f"AI-native SOP missing: {','.join(missing)}",
            )
        return Decision(
            action="allow_ai_native_sop",
            ok=True,
            reason="AI-native SOP defined from scratch",
        )

    if action in {"weekly_ritual", "ai_ops_meeting"}:
        if claim.get("reviewed_metrics") is not True:
            return Decision(
                action="block_ritual_without_metrics",
                ok=False,
                reason="weekly ritual must review one workflow's metrics",
            )
        return Decision(
            action="allow_weekly_ritual",
            ok=True,
            reason="weekly AI operating ritual",
        )

    if action in {"compute_roi", "roi"}:
        try:
            fv = float(claim.get("financial_value"))  # type: ignore[arg-type]
            tc = float(claim.get("total_cost"))  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return Decision(
                action="block_invalid_roi_inputs",
                ok=False,
                reason="financial_value and total_cost must be numbers",
            )
        if claim.get("includes_labor_training_review") is not True:
            return Decision(
                action="block_incomplete_total_cost",
                ok=False,
                reason=(
                    "total_cost must include labor, integration, governance, "
                    "training, and review — not only API fees"
                ),
            )
        result = compute_roi(financial_value=fv, total_cost=tc)
        if not result["ok"]:
            return Decision(action="block_roi", ok=False, reason=result["reason"])
        return Decision(
            action="allow_roi",
            ok=True,
            reason=f"roi={result['roi']:.4f}",
        )

    if action in {"prioritize", "score_workflow"}:
        scored = score_workflow_priority(claim)
        if not scored["pursue"]:
            return Decision(
                action="block_low_priority_workflow",
                ok=False,
                reason=(
                    "need high volume/labor, QA after checks, fast deploy, "
                    "and a manager who enforces the new process"
                ),
            )
        return Decision(
            action="allow_priority_workflow",
            ok=True,
            reason=f"score={scored['score']} workflow={scored['workflow']}",
        )

    if action in {"expand_after_pilot", "scale_cohort"}:
        if claim.get("pilot_quantified") is not True:
            return Decision(
                action="block_premature_expand",
                ok=False,
                reason="quantify 30-day pilot before expanding to next cohort",
            )
        return Decision(
            action="allow_expand",
            ok=True,
            reason="pilot quantified; expand standardized winning SOP",
        )

    return Decision(
        action="block_unknown_operating_model_action",
        ok=False,
        reason=(
            "declare action: pick_workflow|rebuild_sop|weekly_ritual|"
            "compute_roi|prioritize|expand_after_pilot|buy_more_licenses_first"
        ),
    )


def evaluate(repo: Path) -> dict[str, Any]:
    blockers: list[str] = []
    if not (repo / "docs" / "AI_OPERATING_MODEL.md").is_file():
        blockers.append("missing_docs/AI_OPERATING_MODEL.md")
    if not (repo / "scripts" / "ai_operating_model_gate.py").is_file():
        blockers.append("missing_scripts/ai_operating_model_gate.py")
    blockers.extend(require_dual_skills(repo, "ai-operating-model-lite"))
    blockers.extend(
        require_docs_needles(
            repo / "docs" / "AI_OPERATING_MODEL.md",
            (
                "operating-model",
                "tool rollout",
                "baseline",
                "sop",
                "enablement",
                "weekly",
                "behavior",
                "roi",
                "30-day",
                "intake",
            ),
        )
    )

    fixture = (
        repo
        / "marketing"
        / "data"
        / "code_health"
        / "ai_operating_model_discipline.json"
    )
    if not fixture.is_file():
        blockers.append(
            "missing_fixture:marketing/data/code_health/ai_operating_model_discipline.json"
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
                or budget.get("prefer_enablement_over_licenses") is not True
            ):
                blockers.append(
                    "fixture_missing:budget.prefer_enablement_over_licenses=true"
                )
            pilot = charter.get("reference_pilot") or {}
            if not isinstance(pilot, dict) or not pilot.get("workflow"):
                blockers.append("fixture_missing:reference_pilot.workflow")
            elif norm(pilot.get("workflow")) not in PREFERRED_WORKFLOWS:
                blockers.append("fixture_missing:reference_pilot.preferred_workflow")

    ready = len(blockers) == 0
    return {
        "framework": "ai-operating-model-lite",
        "source": SOURCE,
        "ready": ready,
        "blockers": blockers,
        "health_signals": list(HEALTH_SIGNALS),
        "anti_pattern": "license_rollout_without_sop_ritual_or_outcome_metrics",
        "budget_note": (
            "fund enablement/templates/office hours before expanding AI "
            "subscriptions; stay under $20/mo hard cap"
        ),
        "pairs_with": [
            "docs/WORKFLOW_ECONOMICS.md",
            "docs/DIFF_DELTA.md",
            "docs/AGENT_INTEGRITY.md",
            "docs/NVIDIA_PAIR_LOCAL_ROUTER.md",
        ],
        "preferred_workflows": sorted(PREFERRED_WORKFLOWS),
    }


def main(argv: list[str] | None = None) -> int:
    return run_presence_cli(
        description=__doc__ or "ai-operating-model-lite",
        evaluate=evaluate,
        claim_evaluator=evaluate_operating_model_claim,
        argv=argv,
    )


if __name__ == "__main__":
    raise SystemExit(main())
