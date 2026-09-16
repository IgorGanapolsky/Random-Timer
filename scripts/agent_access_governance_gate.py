#!/usr/bin/env python3
"""Agent Access Governance lite — least privilege for real agent workflows.

Source thesis (podcast / YouTube Music):
  https://music.youtube.com/watch?v=II_xGPfDb6I

Highest ROI is not RBAC theory — it is products/services that govern what
agents can access and execute: inventory, least privilege, policy enforcement
on tool/MCP calls, approval gates for risky ops, immutable logs, and a
maturity path from pilots to operational workflows.

Under the $20/mo hard cap: encode governance discipline locally (ThumbGate /
hooks / gates). Do not default to a paid agent-security SaaS.
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

SOURCE = "https://music.youtube.com/watch?v=II_xGPfDb6I"

HEALTH_SIGNALS = (
    "least_privilege_agent_scopes",
    "role_attribute_policy_controls",
    "agent_mcp_api_inventory",
    "tool_call_policy_enforcement",
    "approval_gates_risky_ops",
    "immutable_audit_logs",
    "governance_maturity_model",
    "risk_reduction_not_generic_ai_security",
    "budget_gated_governance_saas",
)

RISKY_OPS = frozenset(
    {
        "payment",
        "customer_communication",
        "production_change",
        "export",
        "destructive",
        "credential_write",
        "secret_exfil",
    }
)

MATURITY_STAGES = (
    "ad_hoc",
    "inventoried",
    "least_privilege",
    "policy_enforced",
    "continuously_monitored",
)


def evaluate_governance_claim(claim: Mapping[str, object]) -> Decision:
    action = norm(claim.get("action"))

    if action in {
        "unrestricted_agent_tools",
        "shared_admin_service_account",
        "skip_approvals_for_payments",
        "generic_ai_security_pitch",
        "default_paid_governance_saas",
    }:
        return Decision(
            action="block_ungoverned_agent",
            ok=False,
            reason=(
                "governed agents need least privilege, policy on tool calls, "
                "approvals for risky ops — not unrestricted tools or generic AI security"
            ),
        )

    if action in {"inventory", "map_agents"}:
        required = ("agents", "mcp_servers", "apis", "service_accounts")
        missing = [k for k in required if not claim.get(k)]
        if missing:
            return Decision(
                action="block_incomplete_inventory",
                ok=False,
                reason=f"inventory missing: {','.join(missing)}",
            )
        return Decision(
            action="allow_inventory",
            ok=True,
            reason="agent/MCP/API/service-account inventory present",
        )

    if action in {"tool_call", "mcp_invoke", "policy_check"}:
        if claim.get("policy_evaluated") is not True:
            return Decision(
                action="block_unpolicied_tool_call",
                ok=False,
                reason="intercept tool/MCP calls with allow/deny policy before execute",
            )
        if claim.get("allowed") is False:
            return Decision(
                action="block_denied_by_policy",
                ok=False,
                reason="policy deny — do not execute",
            )
        return Decision(
            action="allow_policied_tool_call",
            ok=True,
            reason="policy allow with audit log",
        )

    if action in {"risky_op", "execute_risky"}:
        op = norm(claim.get("op")) or "unknown"
        if op in RISKY_OPS or claim.get("risky") is True:
            if claim.get("human_approval") is not True:
                return Decision(
                    action="block_risky_without_approval",
                    ok=False,
                    reason=(
                        "payments, customer comms, production changes, exports, "
                        "and destructive ops require human approval"
                    ),
                )
            if claim.get("audit_logged") is not True:
                return Decision(
                    action="block_risky_without_audit",
                    ok=False,
                    reason="risky ops require immutable audit log entry",
                )
        return Decision(
            action="allow_approved_risky_op",
            ok=True,
            reason=f"approved risky op={op}",
        )

    if action in {"maturity", "assess_maturity"}:
        stage = norm(claim.get("stage"))
        if stage not in MATURITY_STAGES:
            return Decision(
                action="block_unknown_maturity_stage",
                ok=False,
                reason=f"stage must be one of {','.join(MATURITY_STAGES)}",
            )
        return Decision(
            action=f"allow_maturity_{stage}",
            ok=True,
            reason=f"governance maturity stage={stage}",
        )

    if action in {"commercial_offer", "sell"}:
        offer = norm(claim.get("offer"))
        allowed = {
            "access_governance_audit",
            "mcp_policy_proxy",
            "permission_aware_templates",
            "continuous_monitoring",
            "maturity_assessment",
            "secure_agent_operations",
        }
        if offer not in allowed:
            return Decision(
                action="block_weak_commercial_offer",
                ok=False,
                reason="sell risk-reduction/enablement offers, not generic AI security",
            )
        return Decision(
            action="allow_commercial_offer",
            ok=True,
            reason=f"commercial offer={offer}",
        )

    return Decision(
        action="block_unknown_governance_action",
        ok=False,
        reason=(
            "declare action: inventory|tool_call|risky_op|maturity|"
            "commercial_offer|unrestricted_agent_tools"
        ),
    )


def evaluate(repo: Path) -> dict[str, Any]:
    blockers: list[str] = []
    if not (repo / "docs" / "AGENT_ACCESS_GOVERNANCE.md").is_file():
        blockers.append("missing_docs/AGENT_ACCESS_GOVERNANCE.md")
    if not (repo / "scripts" / "agent_access_governance_gate.py").is_file():
        blockers.append("missing_scripts/agent_access_governance_gate.py")
    blockers.extend(require_dual_skills(repo, "agent-access-governance-lite"))
    blockers.extend(
        require_docs_needles(
            repo / "docs" / "AGENT_ACCESS_GOVERNANCE.md",
            (
                "least privilege",
                "policy",
                "mcp",
                "approval",
                "audit",
                "maturity",
                "inventory",
                "risk",
                "governance",
                "tool",
            ),
        )
    )

    fixture = (
        repo
        / "marketing"
        / "data"
        / "code_health"
        / "agent_access_governance_discipline.json"
    )
    if not fixture.is_file():
        blockers.append(
            "missing_fixture:marketing/data/code_health/agent_access_governance_discipline.json"
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
                or budget.get("default_to_paid_governance_saas") is not False
            ):
                blockers.append(
                    "fixture_missing:budget.default_to_paid_governance_saas=false"
                )

    ready = len(blockers) == 0
    return {
        "framework": "agent-access-governance-lite",
        "source": SOURCE,
        "ready": ready,
        "blockers": blockers,
        "health_signals": list(HEALTH_SIGNALS),
        "anti_pattern": "unrestricted_tools_or_generic_ai_security_without_policy",
        "budget_note": (
            "local policy/approval/audit first; no paid agent-governance SaaS "
            "under $20/mo hard cap"
        ),
        "maturity_stages": list(MATURITY_STAGES),
        "pairs_with": [
            "docs/AI_OPERATING_MODEL.md",
            "docs/LLM_OBSERVABILITY.md",
            "docs/AGENT_INTEGRITY.md",
            "docs/GPT6_ASTRA_HARNESS.md",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    return run_presence_cli(
        description=__doc__ or "agent-access-governance-lite",
        evaluate=evaluate,
        claim_evaluator=evaluate_governance_claim,
        argv=argv,
    )


if __name__ == "__main__":
    raise SystemExit(main())
