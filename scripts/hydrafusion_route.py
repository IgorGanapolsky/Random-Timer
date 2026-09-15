#!/usr/bin/env python3
"""HydraFusion-inspired multi-model orchestration router (zero-cost local).

Inspired by GitHub Project HydraFusion (2026-09-04):
https://github.blog/ai-and-ml/github-copilot/project-hydrafusion-frontier-quality-via-multi-model-orchestration/

Selects the least-complex workflow expected to clear the quality bar:

- single: one model solves the task directly
- cascade: efficient draft → quality gate → escalate if rejected
- critique: draft → isolated read-only critic (other model family) → revise once

This does NOT call paid Copilot HydraFusion. It emits an execution plan agents
must follow under the $20/mo operating budget (prefer Single/Cascade).
"""

from __future__ import annotations

import argparse
import json
import re
from typing import Any


SOURCE_URL = (
    "https://github.blog/ai-and-ml/github-copilot/"
    "project-hydrafusion-frontier-quality-via-multi-model-orchestration/"
)

INFOQ_SOURCE_URL = "https://www.infoq.com/news/2026/09/github-hydrafusion/"

# InfoQ reported ~65–67% estimated cost reduction vs always-frontier (Opus 5).
# Local proxy threshold for claiming "InfoQ-aligned savings" on Cascade sims.
INFOQ_SAVINGS_PROXY = 0.60

# Default relative costs (Quick draft vs frontier Deep/Opus-class units).
DEFAULT_DRAFT_COST = 1.0
DEFAULT_FRONTIER_COST = 10.0
DEFAULT_GATE_COST = 0.2
DEFAULT_CRITIC_COST = 1.5
DEFAULT_REVISION_COST = 4.0
DEFAULT_CASCADE_PASS_RATE = 0.75

CAPABILITY_ALIASES = {
    "reasoning": "multi_step_reasoning",
    "multi_step_reasoning": "multi_step_reasoning",
    "code_generation": "code_generation",
    "debugging": "structured_debugging",
    "structured_debugging": "structured_debugging",
    "tool_use": "advanced_tool_use",
    "advanced_tool_use": "advanced_tool_use",
}

# Category → model family (for isolated critique across families)
CATEGORY_FAMILY: dict[str, str] = {
    "Quick": "gemini",
    "Deep": "claude",
    "UltraBrain": "claude",
    "Visual": "gemini",
}

# Cursor Task / Claude Code category bindings (logical; resolve at runtime)
CATEGORY_MODELS: dict[str, dict[str, str]] = {
    "Quick": {
        "primary": "gemini-flash / composer-fast",
        "fallback": "claude-haiku",
    },
    "Deep": {
        "primary": "claude-opus-class / gpt-5-class",
        "fallback": "claude-sonnet-class",
    },
    "UltraBrain": {
        "primary": "claude-sonnet-class",
        "fallback": "gemini-pro-class",
    },
    "Visual": {
        "primary": "gemini-pro-multimodal",
        "fallback": "gpt-4o-class",
    },
}

HIGH_RISK_DOMAINS = frozenset(
    {
        "store_publishing",
        "billing",
        "security",
        "secrets",
        "payments",
        "release",
    }
)

CRITIQUE_KEYWORDS = re.compile(
    r"\b(security|privacy|publish|release|billing|iap|secret|credential|"
    r"store listing|app.?store|play console|review)\b",
    re.I,
)
CASCADE_KEYWORDS = re.compile(
    r"\b(implement|upgrade|refactor|fix|migrate|feature|test|"
    r"paywall|catalog|sdk)\b",
    re.I,
)


def _normalize_caps(raw: Any) -> set[str]:
    if not raw:
        return set()
    normalized: set[str] = set()
    for c in raw:
        key = str(c).strip().lower()
        if not key:
            continue
        normalized.add(CAPABILITY_ALIASES.get(key, key))
        # Keep short aliases for existing route heuristics.
        if key in {"reasoning", "debugging", "tool_use", "code_generation", "visual"}:
            normalized.add(key)
        if key in CAPABILITY_ALIASES:
            short = {
                "multi_step_reasoning": "reasoning",
                "structured_debugging": "debugging",
                "advanced_tool_use": "tool_use",
            }.get(CAPABILITY_ALIASES[key])
            if short:
                normalized.add(short)
    return normalized


def estimate_cascade_cost(
    *,
    draft_cost: float,
    frontier_cost: float,
    gate_cost: float = DEFAULT_GATE_COST,
    pass_rate: float = DEFAULT_CASCADE_PASS_RATE,
) -> dict[str, Any]:
    """Expected Cascade cost vs always-frontier (InfoQ economics proxy).

    E[cost] = pass_rate * (draft + gate) + (1 - pass_rate) * (draft + gate + frontier)
            = draft + gate + (1 - pass_rate) * frontier
    """
    if frontier_cost <= 0:
        raise ValueError("frontier_cost must be > 0")
    p = min(1.0, max(0.0, float(pass_rate)))
    expected = float(draft_cost) + float(gate_cost) + (1.0 - p) * float(frontier_cost)
    always = float(frontier_cost)
    savings = 1.0 - (expected / always)
    return {
        "pattern": "cascade",
        "source": INFOQ_SOURCE_URL,
        "draft_cost": float(draft_cost),
        "gate_cost": float(gate_cost),
        "frontier_cost": always,
        "pass_rate": p,
        "expected_cost": round(expected, 6),
        "always_frontier_cost": always,
        "savings_pct": round(savings, 6),
        "beats_always_frontier": expected < always,
        "meets_infoq_savings_proxy": savings >= INFOQ_SAVINGS_PROXY,
        "infoq_savings_proxy": INFOQ_SAVINGS_PROXY,
        "legs_accounted": ["draft", "gate", "escalate"],
        "complete_cost_accounting": True,
        "label": "local_estimate_not_terminalbench",
    }


def estimate_critique_cost(
    *,
    draft_cost: float,
    critic_cost: float,
    revision_cost: float,
    frontier_cost: float,
) -> dict[str, Any]:
    expected = float(draft_cost) + float(critic_cost) + float(revision_cost)
    always = float(frontier_cost)
    savings = 1.0 - (expected / always) if always > 0 else 0.0
    return {
        "pattern": "critique",
        "source": INFOQ_SOURCE_URL,
        "expected_cost": round(expected, 6),
        "always_frontier_cost": always,
        "savings_pct": round(savings, 6),
        "beats_always_frontier": expected < always,
        "legs_accounted": ["draft", "critique", "revision"],
        "complete_cost_accounting": True,
        "isolated_critique": True,
        "label": "local_estimate_not_checkpointbench",
    }


def run_cascade(payload: dict[str, Any]) -> dict[str, Any]:
    """Execute Cascade decision: draft → quality gate → accept or escalate."""
    cancelled = bool(payload.get("cancelled"))
    draft_cost = float(payload.get("draft_cost") or 0.0)
    gate_cost = float(payload.get("gate_cost") or DEFAULT_GATE_COST)
    escalate_cost = float(payload.get("escalate_cost") or DEFAULT_FRONTIER_COST)
    gate = evaluate_quality_gate(dict(payload.get("gate_signals") or {}))

    if cancelled:
        return {
            "pattern": "cascade",
            "accepted": False,
            "escalated": False,
            "apply_patch": False,
            "fail_safe": True,
            "total_cost": round(draft_cost + gate_cost, 6),
            "gate": gate,
            "reason": "cancelled — fail-safe rejects apply",
            "legs_accounted": ["draft", "gate"],
        }

    if gate["accepted"]:
        return {
            "pattern": "cascade",
            "accepted": True,
            "escalated": False,
            "apply_patch": True,
            "fail_safe": True,
            "total_cost": round(draft_cost + gate_cost, 6),
            "gate": gate,
            "artifact": payload.get("draft_artifact"),
            "legs_accounted": ["draft", "gate"],
        }

    return {
        "pattern": "cascade",
        "accepted": False,
        "escalated": True,
        "apply_patch": False,
        "fail_safe": True,
        "total_cost": round(draft_cost + gate_cost + escalate_cost, 6),
        "gate": gate,
        "legs_accounted": ["draft", "gate", "escalate"],
    }


def score_capability_signals(request: dict[str, Any]) -> dict[str, Any]:
    """InfoQ capability signals → pattern recommendation."""
    caps = _normalize_caps(request.get("capabilities"))
    infoq_caps = {
        "multi_step_reasoning",
        "code_generation",
        "structured_debugging",
        "advanced_tool_use",
    }
    matched = sorted(caps & infoq_caps)
    risk = str(request.get("risk") or "low").lower()
    files = int(request.get("files_touched_estimate") or 0)
    if risk == "high" or files >= 15:
        recommended = "critique"
    elif risk == "medium" or files >= 5 or len(matched) >= 2:
        recommended = "cascade"
    else:
        recommended = "single"
    return {
        "capability_count": len(matched),
        "matched_capabilities": matched,
        "recommended_pattern": recommended,
        "source": INFOQ_SOURCE_URL,
    }


def _default_cost_estimate(pattern: str) -> dict[str, Any]:
    if pattern == "cascade":
        return estimate_cascade_cost(
            draft_cost=DEFAULT_DRAFT_COST,
            frontier_cost=DEFAULT_FRONTIER_COST,
            gate_cost=DEFAULT_GATE_COST,
            pass_rate=DEFAULT_CASCADE_PASS_RATE,
        )
    if pattern == "critique":
        return estimate_critique_cost(
            draft_cost=DEFAULT_FRONTIER_COST * 0.8,
            critic_cost=DEFAULT_CRITIC_COST,
            revision_cost=DEFAULT_REVISION_COST,
            frontier_cost=DEFAULT_FRONTIER_COST,
        )
    return {
        "pattern": "single",
        "expected_cost": DEFAULT_DRAFT_COST,
        "always_frontier_cost": DEFAULT_FRONTIER_COST,
        "savings_pct": round(1.0 - (DEFAULT_DRAFT_COST / DEFAULT_FRONTIER_COST), 6),
        "beats_always_frontier": True,
        "legs_accounted": ["draft"],
        "complete_cost_accounting": True,
    }


def _leg(
    role: str,
    category: str,
    *,
    timeout_s: int,
    tool_less: bool = False,
    isolated: bool = False,
) -> dict[str, Any]:
    return {
        "role": role,
        "category": category,
        "family": CATEGORY_FAMILY[category],
        "models": CATEGORY_MODELS[category],
        "timeout_s": timeout_s,
        "tool_less": tool_less,
        "isolated": isolated,
        "cost_accounted": True,
    }


def route_task(request: dict[str, Any]) -> dict[str, Any]:
    """Return a validated HydraFusion-style execution plan for one task."""
    task = str(request.get("task") or "")
    caps = _normalize_caps(request.get("capabilities"))
    risk = str(request.get("risk") or "low").lower()
    files = int(request.get("files_touched_estimate") or 0)
    domain = str(request.get("domain") or "").lower().strip()

    task_l = task.lower()
    critique_signal = bool(CRITIQUE_KEYWORDS.search(task)) and any(
        token in task_l
        for token in (
            "publish",
            "privacy",
            "secret",
            "credential",
            "review",
            "store listing",
            "app store",
            "play console",
        )
    )
    wants_critique = (
        risk == "high"
        or domain in HIGH_RISK_DOMAINS
        or critique_signal
        or ("reasoning" in caps and files >= 10 and risk != "low")
    )
    wants_cascade = not wants_critique and (
        risk == "medium"
        or files >= 5
        or ("code_generation" in caps and files >= 3)
        or bool(CASCADE_KEYWORDS.search(task))
    )

    # Prefer Single for tiny utility / one-file edits.
    if risk == "low" and files <= 2 and caps <= {"tool_use"}:
        wants_cascade = False
        wants_critique = False
    if risk == "low" and files <= 1 and "debugging" not in caps and not critique_signal:
        wants_cascade = False
        wants_critique = False

    if wants_critique:
        pattern = "critique"
        draft_category = "Deep" if files >= 15 or "debugging" in caps else "UltraBrain"
        escalate_category = None
        # Isolated critic must be a different model family than the drafter.
        critic_category = (
            "Quick" if CATEGORY_FAMILY[draft_category] == "claude" else "Deep"
        )
        critic = {
            "category": critic_category,
            "family": CATEGORY_FAMILY[critic_category],
            "isolated": True,
            "tool_less": True,
            "models": CATEGORY_MODELS[critic_category],
        }
        revise_once = True
        legs = [
            _leg("draft", draft_category, timeout_s=900),
            _leg("critique", critic_category, timeout_s=300, tool_less=True, isolated=True),
            _leg("revise", draft_category, timeout_s=600),
        ]
    elif wants_cascade:
        pattern = "cascade"
        draft_category = "Quick"
        escalate_category = "Deep" if "debugging" in caps or files >= 10 else "UltraBrain"
        critic = None
        revise_once = False
        legs = [
            _leg("draft", draft_category, timeout_s=600),
            {
                "role": "quality_gate",
                "category": None,
                "family": None,
                "models": None,
                "timeout_s": 120,
                "tool_less": True,
                "isolated": True,
                "cost_accounted": True,
            },
            _leg("escalate", escalate_category, timeout_s=900),
        ]
    else:
        pattern = "single"
        draft_category = "Quick" if "tool_use" in caps or files <= 2 else "UltraBrain"
        if "visual" in caps or domain == "ui":
            draft_category = "Visual"
        escalate_category = None
        critic = None
        revise_once = False
        legs = [_leg("draft", draft_category, timeout_s=300)]

    plan: dict[str, Any] = {
        "source": SOURCE_URL,
        "pattern": pattern,
        "draft_category": draft_category,
        "draft_family": CATEGORY_FAMILY[draft_category],
        "escalate_category": escalate_category,
        "critic": critic,
        "revise_once": revise_once,
        "quality_gate": {
            "require_tests": pattern in {"cascade", "critique"},
            "require_evidence": True,
            "forbid_secrets": True,
            "require_patch_validation": pattern != "single",
            "accept_on": [
                "tests_passed",
                "evidence_present",
                "not secrets_leaked",
                "patch_validated" if pattern != "single" else "n/a",
            ],
        },
        "legs": legs,
        "principles": {
            "complete_accounting": True,
            "bounded_execution": True,
            "isolated_review": pattern == "critique",
            "fail_safe_application": True,
            "validated_routing": True,
        },
        "budget_note": (
            "Zero incremental SaaS spend. Prefer Single then Cascade. "
            "Critique only for high-risk/store/security work within existing seat limits."
        ),
        "task_echo": task[:240],
        "infoq_source": INFOQ_SOURCE_URL,
        "capability_signals": score_capability_signals(request),
        "cost_estimate": _default_cost_estimate(pattern),
    }
    errors = validate_plan(plan)
    if errors:
        raise ValueError(f"invalid plan: {errors}")
    return plan


def validate_plan(plan: dict[str, Any]) -> list[str]:
    """Validate workflow bindings before execution (HydraFusion principle)."""
    errors: list[str] = []
    pattern = plan.get("pattern")
    if pattern not in {"single", "cascade", "critique"}:
        errors.append(f"unknown pattern: {pattern}")
    draft = plan.get("draft_category")
    if draft not in CATEGORY_FAMILY:
        errors.append(f"unknown draft_category: {draft}")
    if pattern == "cascade" and not plan.get("escalate_category"):
        errors.append("cascade requires escalate_category")
    if pattern == "critique":
        critic = plan.get("critic") or {}
        if not critic.get("isolated") or not critic.get("tool_less"):
            errors.append("critique requires isolated tool-less critic")
        if critic.get("family") == plan.get("draft_family"):
            errors.append("critic must be a different model family than draft")
        if not plan.get("revise_once"):
            errors.append("critique requires revise_once")
    if pattern == "single" and plan.get("critic") is not None:
        errors.append("single must not include critic")
    principles = plan.get("principles") or {}
    for key in (
        "complete_accounting",
        "bounded_execution",
        "fail_safe_application",
        "validated_routing",
    ):
        if not principles.get(key):
            errors.append(f"principle missing: {key}")
    legs = plan.get("legs")
    if not isinstance(legs, list) or not legs:
        errors.append("legs must be a non-empty list")
    elif legs[0].get("role") != "draft":
        errors.append("first leg must be draft")
    for leg in legs or []:
        if not leg.get("cost_accounted"):
            errors.append(f"leg {leg.get('role')} missing cost accounting")
        if not isinstance(leg.get("timeout_s"), int) or leg["timeout_s"] <= 0:
            errors.append(f"leg {leg.get('role')} needs positive timeout_s")
    return errors


def evaluate_quality_gate(signals: dict[str, Any]) -> dict[str, Any]:
    """Cascade acceptance gate: accept draft or escalate."""
    tests_ok = bool(signals.get("tests_passed"))
    evidence_ok = bool(signals.get("evidence_present"))
    secrets_bad = bool(signals.get("secrets_leaked"))
    patch_ok = bool(signals.get("patch_validated"))
    accepted = tests_ok and evidence_ok and (not secrets_bad) and patch_ok
    return {
        "accepted": accepted,
        "escalate": not accepted,
        "reasons": [
            name
            for name, ok in (
                ("tests_passed", tests_ok),
                ("evidence_present", evidence_ok),
                ("no_secrets_leaked", not secrets_bad),
                ("patch_validated", patch_ok),
            )
            if not ok
        ],
        "fail_safe": True,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json",
        dest="json_payload",
        help="Task request JSON object",
    )
    parser.add_argument(
        "--task",
        help="Task description (alternative to --json)",
    )
    parser.add_argument("--risk", default="low")
    parser.add_argument("--files", type=int, default=0)
    parser.add_argument("--domain", default="")
    parser.add_argument(
        "--capabilities",
        default="",
        help="Comma-separated: reasoning,code_generation,debugging,tool_use",
    )
    parser.add_argument(
        "--evaluate-gate",
        dest="evaluate_gate",
        help="JSON signals for evaluate_quality_gate",
    )
    parser.add_argument(
        "--simulate-cost",
        dest="simulate_cost",
        help="JSON: pattern + draft/frontier/gate/pass_rate (or critique legs)",
    )
    parser.add_argument(
        "--run-cascade",
        dest="run_cascade_payload",
        help="JSON: draft_cost, escalate_cost, gate_cost, gate_signals, cancelled?",
    )
    args = parser.parse_args(argv)

    if args.evaluate_gate:
        print(json.dumps(evaluate_quality_gate(json.loads(args.evaluate_gate)), indent=2))
        return 0

    if args.simulate_cost:
        payload = json.loads(args.simulate_cost)
        pattern = str(payload.get("pattern") or "cascade").lower()
        if pattern == "critique":
            result = estimate_critique_cost(
                draft_cost=float(payload.get("draft_cost") or DEFAULT_FRONTIER_COST * 0.8),
                critic_cost=float(payload.get("critic_cost") or DEFAULT_CRITIC_COST),
                revision_cost=float(payload.get("revision_cost") or DEFAULT_REVISION_COST),
                frontier_cost=float(payload.get("frontier_cost") or DEFAULT_FRONTIER_COST),
            )
        else:
            result = estimate_cascade_cost(
                draft_cost=float(payload.get("draft_cost") or DEFAULT_DRAFT_COST),
                frontier_cost=float(payload.get("frontier_cost") or DEFAULT_FRONTIER_COST),
                gate_cost=float(payload.get("gate_cost") or DEFAULT_GATE_COST),
                pass_rate=float(payload.get("pass_rate") or DEFAULT_CASCADE_PASS_RATE),
            )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    if args.run_cascade_payload:
        print(json.dumps(run_cascade(json.loads(args.run_cascade_payload)), indent=2, sort_keys=True))
        return 0

    if args.json_payload:
        request = json.loads(args.json_payload)
    else:
        caps = [c.strip() for c in args.capabilities.split(",") if c.strip()]
        request = {
            "task": args.task or "",
            "risk": args.risk,
            "files_touched_estimate": args.files,
            "domain": args.domain,
            "capabilities": caps,
        }
    plan = route_task(request)
    print(json.dumps(plan, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
