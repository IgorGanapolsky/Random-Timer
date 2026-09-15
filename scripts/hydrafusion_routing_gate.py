#!/usr/bin/env python3
"""HydraFusion routing lite — Single / Cascade / Critique with cost accounting.

Source:
  https://www.infoq.com/news/2026/09/github-hydrafusion/

InfoQ / GitHub thesis: runtime multi-model orchestration (not one static frontier
model). Patterns: Single, Cascade (draft→gate→escalate), Critique (draft→
tool-less critic→one revision). Principles: complete cost accounting, bounded
execution, isolated review, fail-safe apply, validated routing.

High-ROI steals for Random Timer (hard monthly budget — no HydraFusion SaaS):
  - Prefer Cascade over always-frontier for feature work
  - Isolate critics (no tools)
  - Reject unvalidated patches
  - Account every workflow leg before claiming savings
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

SOURCE = "https://www.infoq.com/news/2026/09/github-hydrafusion/"

HEALTH_SIGNALS = (
    "complete_cost_accounting",
    "bounded_execution",
    "isolated_critique",
    "fail_safe_apply",
    "validated_routing",
)

PATTERNS = frozenset({"single", "cascade", "critique"})

COMPLEXITY_ORDER = {
    "trivial": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}

ACCOUNTABLE_LEGS = frozenset(
    {
        "draft",
        "critique",
        "revision",
        "escalate",
        "retry",
        "fallback",
        "gate",
    }
)


def select_pattern(
    *,
    complexity: str,
    needs_isolated_review: bool = False,
    cheap_draft_viable: bool = True,
) -> str:
    """Map task signals to HydraFusion pattern vocabulary."""
    level = COMPLEXITY_ORDER.get(norm(complexity), 2)
    if needs_isolated_review or level >= 3:
        return "critique"
    if cheap_draft_viable and level >= 1:
        return "cascade"
    return "single"


def evaluate_routing_claim(claim: Mapping[str, object]) -> Decision:
    action = norm(claim.get("action"))
    pattern = norm(claim.get("pattern") or claim.get("route"))

    if action in {"subscribe_hydrafusion", "buy_copilot_experimental"}:
        return Decision(
            action="block_paid_hydrafusion_saas",
            ok=False,
            reason="do not subscribe to HydraFusion/Copilot experimental under hard monthly cap — steal patterns locally",
        )

    if action in {"always_frontier", "always_opus", "skip_cascade"}:
        return Decision(
            action="block_always_frontier",
            ok=False,
            reason="anti-pattern: always-frontier without Single/Cascade/Critique routing",
        )

    if pattern and pattern not in PATTERNS and action in {
        "route",
        "select_pattern",
        "run_workflow",
    }:
        return Decision(
            action="block_unknown_pattern",
            ok=False,
            reason="pattern must be single|cascade|critique",
        )

    if pattern == "critique" or action in {"run_critique", "critique_pass"}:
        if claim.get("critic_has_tools") is True or claim.get("critic_can_mutate") is True:
            return Decision(
                action="block_tooling_critic",
                ok=False,
                reason="critique critic must be tool-less / read-only (isolated review)",
            )

    if action in {"apply_patch", "apply_diff", "land_change"}:
        if claim.get("validated") is not True:
            return Decision(
                action="block_unvalidated_apply",
                ok=False,
                reason="fail-safe: reject patches unless validated=true",
            )
        if claim.get("cancelled") is True:
            return Decision(
                action="block_cancelled_apply",
                ok=False,
                reason="fail-safe: reject patches when execution was cancelled",
            )

    if action in {"run_workflow", "route"} and claim.get("model_available") is False:
        return Decision(
            action="block_unvalidated_routing",
            ok=False,
            reason="validated routing: pre-check model availability before spend",
        )

    if action in {"run_workflow", "route"} and claim.get("timeout_seconds") in (None, 0, "", False):
        return Decision(
            action="block_unbounded_execution",
            ok=False,
            reason="bounded execution requires timeout_seconds > 0",
        )

    if action in {"claim_savings", "project_savings"}:
        legs = claim.get("legs_accounted") or claim.get("accounted_legs") or []
        if not isinstance(legs, list) or not legs:
            return Decision(
                action="block_unaccounted_savings",
                ok=False,
                reason="complete cost accounting: declare legs_accounted before savings claims",
            )
        unknown = [norm(x) for x in legs if norm(x) not in ACCOUNTABLE_LEGS]
        if unknown:
            return Decision(
                action="block_unknown_cost_leg",
                ok=False,
                reason="legs must be in draft|critique|revision|escalate|retry|fallback|gate",
            )
        if claim.get("total_cost_units") is None:
            return Decision(
                action="block_missing_total_cost",
                ok=False,
                reason="record total_cost_units across all workflow legs",
            )
        return Decision(
            action="allow_accounted_savings",
            ok=True,
            reason="savings claim has complete leg accounting",
        )

    if action in {
        "select_pattern",
        "route",
        "run_workflow",
        "apply_patch",
        "run_critique",
    }:
        if action == "select_pattern" or (pattern in PATTERNS and action in {"route", "run_workflow"}):
            if action in {"route", "run_workflow"}:
                try:
                    timeout = float(claim.get("timeout_seconds"))  # type: ignore[arg-type]
                except (TypeError, ValueError):
                    return Decision(
                        action="block_unbounded_execution",
                        ok=False,
                        reason="bounded execution requires timeout_seconds > 0",
                    )
                if timeout <= 0:
                    return Decision(
                        action="block_unbounded_execution",
                        ok=False,
                        reason="bounded execution requires timeout_seconds > 0",
                    )
                if claim.get("model_available") is not True:
                    return Decision(
                        action="block_unvalidated_routing",
                        ok=False,
                        reason="validated routing: require model_available=true",
                    )
            if action == "apply_patch":
                return Decision(
                    action="allow_fail_safe_apply",
                    ok=True,
                    reason="validated, non-cancelled patch apply",
                )
            if action == "run_critique":
                return Decision(
                    action="allow_isolated_critique",
                    ok=True,
                    reason="tool-less critique path",
                )
            if action == "select_pattern":
                chosen = select_pattern(
                    complexity=str(claim.get("complexity") or "medium"),
                    needs_isolated_review=bool(claim.get("needs_isolated_review")),
                    cheap_draft_viable=claim.get("cheap_draft_viable", True) is not False,
                )
                return Decision(
                    action=f"allow_pattern_{chosen}",
                    ok=True,
                    reason=f"selected HydraFusion pattern: {chosen}",
                )
            return Decision(
                action=f"allow_{pattern or 'routed'}_workflow",
                ok=True,
                reason="bounded, validated HydraFusion-style workflow",
            )
        if action == "apply_patch":
            return Decision(
                action="allow_fail_safe_apply",
                ok=True,
                reason="validated, non-cancelled patch apply",
            )
        if action == "run_critique":
            return Decision(
                action="allow_isolated_critique",
                ok=True,
                reason="tool-less critique path",
            )

    return Decision(
        action="block_unknown_hydrafusion_action",
        ok=False,
        reason=(
            "declare action: select_pattern|route|run_workflow|run_critique|"
            "apply_patch|claim_savings"
        ),
    )


def evaluate(repo: Path) -> dict[str, Any]:
    blockers: list[str] = []
    if not (repo / "docs" / "HYDRAFUSION_ROUTING.md").is_file():
        blockers.append("missing_docs/HYDRAFUSION_ROUTING.md")
    if not (repo / "docs" / "HYDRAFUSION_ORCHESTRATION.md").is_file():
        blockers.append("missing_docs/HYDRAFUSION_ORCHESTRATION.md")
    if not (repo / "scripts" / "hydrafusion_routing_gate.py").is_file():
        blockers.append("missing_scripts/hydrafusion_routing_gate.py")
    if not (repo / "scripts" / "hydrafusion_route.py").is_file():
        blockers.append("missing_scripts/hydrafusion_route.py")
    blockers.extend(require_dual_skills(repo, "hydrafusion-routing-lite"))
    blockers.extend(
        require_docs_needles(
            repo / "docs" / "HYDRAFUSION_ROUTING.md",
            (
                "single",
                "cascade",
                "critique",
                "cost accounting",
                "bounded",
                "fail-safe",
                "validated routing",
                "tool-less",
            ),
        )
    )

    fixture = (
        repo / "marketing" / "data" / "code_health" / "hydrafusion_routing_discipline.json"
    )
    if not fixture.is_file():
        blockers.append(
            "missing_fixture:marketing/data/code_health/hydrafusion_routing_discipline.json"
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
                or budget.get("subscribe_hydrafusion") is not False
            ):
                blockers.append("fixture_missing:budget.subscribe_hydrafusion=false")

    matching = repo / ".claude" / "rules" / "agent-model-matching.md"
    if not matching.is_file():
        blockers.append("missing:.claude/rules/agent-model-matching.md")

    ready = len(blockers) == 0
    return {
        "framework": "hydrafusion-routing-lite",
        "source": SOURCE,
        "ready": ready,
        "blockers": blockers,
        "health_signals": list(HEALTH_SIGNALS),
        "patterns": sorted(PATTERNS),
        "anti_pattern": "always_frontier_no_routing",
        "budget_note": "local Single/Cascade/Critique + accounting; no HydraFusion SaaS under hard cap",
    }


def main(argv: list[str] | None = None) -> int:
    return run_presence_cli(
        description=__doc__ or "hydrafusion-routing-lite",
        evaluate=evaluate,
        claim_evaluator=evaluate_routing_claim,
        argv=argv,
    )


if __name__ == "__main__":
    raise SystemExit(main())
