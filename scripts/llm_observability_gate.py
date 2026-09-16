#!/usr/bin/env python3
"""LLM Observability lite — monitor, optimize, secure agent/LLM runs.

Source:
  https://lp.datadoghq.com/rs/875-UVY-685/images/eBook-LLMObservabilityBestPractices.pdf?version=1

Datadog thesis (steal practices, not the SaaS by default): (1) operational
performance — errors, latency, token/cost alerts; (2) prompt-injection and
security/PII exposures; (3) functional quality evals; (4) end-to-end chain/
agent tracing for faster MTTR; (5) cost control via token and cost-per-query.

Under the $20/mo hard cap: prefer free/local/PostHog/existing logs. Do not
default to paid Datadog Agent Observability.
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
    "https://lp.datadoghq.com/rs/875-UVY-685/images/"
    "eBook-LLMObservabilityBestPractices.pdf?version=1"
)

HEALTH_SIGNALS = (
    "operational_perf_errors_latency_tokens",
    "prompt_injection_and_security_signals",
    "pii_scrub_or_detect",
    "functional_quality_evals",
    "end_to_end_chain_tracing",
    "cost_per_query_visibility",
    "alert_on_budget_and_errors",
    "prefer_free_local_or_posthog",
    "budget_gated_datadog_saas",
)


def evaluate_llm_obs_claim(claim: Mapping[str, object]) -> Decision:
    action = norm(claim.get("action"))

    if action in {
        "default_paid_datadog",
        "buy_datadog_first",
        "fly_blind_no_traces",
        "ignore_token_cost",
    }:
        return Decision(
            action="block_blind_or_paid_default",
            ok=False,
            reason=(
                "instrument traces/quality/cost locally or via existing PostHog; "
                "do not default to paid Datadog under hard monthly cap"
            ),
        )

    if action in {"claim_monitored", "ops_ready"}:
        needed = ("errors_tracked", "latency_tracked", "tokens_or_cost_tracked")
        missing = [k for k in needed if claim.get(k) is not True]
        if missing:
            return Decision(
                action="block_incomplete_ops_monitoring",
                ok=False,
                reason=f"ops monitoring missing: {','.join(missing)}",
            )
        return Decision(
            action="allow_ops_monitoring",
            ok=True,
            reason="operational LLM metrics present",
        )

    if action in {"security_check", "prompt_injection"}:
        if claim.get("security_signals_enabled") is not True:
            return Decision(
                action="block_no_security_signals",
                ok=False,
                reason="track prompt injection / toxic / unauthorized behavior signals",
            )
        return Decision(
            action="allow_security_signals",
            ok=True,
            reason="security/privacy signals enabled",
        )

    if action in {"quality_eval", "evaluate_output"}:
        if claim.get("quality_checks") is not True:
            return Decision(
                action="block_no_quality_evals",
                ok=False,
                reason="functional quality checks required (answer failure, toxicity, etc.)",
            )
        return Decision(
            action="allow_quality_evals",
            ok=True,
            reason="functional quality evals present",
        )

    if action in {"trace", "debug_chain"}:
        if claim.get("end_to_end_trace") is not True:
            return Decision(
                action="block_no_e2e_trace",
                ok=False,
                reason="end-to-end chain/agent tracing required for MTTR",
            )
        return Decision(
            action="allow_e2e_trace",
            ok=True,
            reason="end-to-end LLM/agent trace available",
        )

    if action in {"cost_alert", "budget_alert"}:
        try:
            remaining = float(claim.get("budget_remaining_usd"))  # type: ignore[arg-type]
        except (TypeError, ValueError):
            remaining = -1.0
        if remaining < 0 or claim.get("token_or_cost_metered") is not True:
            return Decision(
                action="block_unmetered_llm_spend",
                ok=False,
                reason="meter tokens/cost-per-query and stay within remaining budget",
            )
        return Decision(
            action="allow_cost_alert_path",
            ok=True,
            reason="token/cost metering with budget remaining",
        )

    return Decision(
        action="block_unknown_llm_obs_action",
        ok=False,
        reason=(
            "declare action: claim_monitored|security_check|quality_eval|"
            "trace|cost_alert|default_paid_datadog"
        ),
    )


def evaluate(repo: Path) -> dict[str, Any]:
    blockers: list[str] = []
    if not (repo / "docs" / "LLM_OBSERVABILITY.md").is_file():
        blockers.append("missing_docs/LLM_OBSERVABILITY.md")
    if not (repo / "scripts" / "llm_observability_gate.py").is_file():
        blockers.append("missing_scripts/llm_observability_gate.py")
    blockers.extend(require_dual_skills(repo, "llm-observability-lite"))
    blockers.extend(
        require_docs_needles(
            repo / "docs" / "LLM_OBSERVABILITY.md",
            (
                "latency",
                "token",
                "prompt injection",
                "pii",
                "quality",
                "trace",
                "cost",
                "budget",
                "datadog",
                "posthog",
            ),
        )
    )

    fixture = (
        repo / "marketing" / "data" / "code_health" / "llm_observability_discipline.json"
    )
    if not fixture.is_file():
        blockers.append(
            "missing_fixture:marketing/data/code_health/llm_observability_discipline.json"
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
                or budget.get("default_to_paid_datadog") is not False
            ):
                blockers.append("fixture_missing:budget.default_to_paid_datadog=false")

    ready = len(blockers) == 0
    return {
        "framework": "llm-observability-lite",
        "source": SOURCE,
        "ready": ready,
        "blockers": blockers,
        "health_signals": list(HEALTH_SIGNALS),
        "anti_pattern": "flying_blind_or_paid_datadog_default",
        "budget_note": (
            "steal Datadog practices; prefer PostHog/local traces; "
            "budget-gate paid Datadog under $20/mo"
        ),
        "pairs_with": [
            "docs/AGENT_ACCESS_GOVERNANCE.md",
            "docs/TRUST_RELIABILITY_LOOP.md",
            "docs/LLM_RESPONSE_CACHE.md",
            "docs/WORKFLOW_ECONOMICS.md",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    return run_presence_cli(
        description=__doc__ or "llm-observability-lite",
        evaluate=evaluate,
        claim_evaluator=evaluate_llm_obs_claim,
        argv=argv,
    )


if __name__ == "__main__":
    raise SystemExit(main())
