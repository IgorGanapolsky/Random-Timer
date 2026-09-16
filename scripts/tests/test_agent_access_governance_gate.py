"""TDD: Agent Access Governance lite gate."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.agent_access_governance_gate import (
    HEALTH_SIGNALS,
    evaluate,
    evaluate_governance_claim,
)


def _scaffold(root: Path) -> None:
    (root / "docs").mkdir()
    (root / "docs" / "AGENT_ACCESS_GOVERNANCE.md").write_text(
        "\n".join(
            [
                "# Agent Access Governance",
                "least privilege policy mcp approval audit",
                "maturity inventory risk governance tool",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (root / "scripts").mkdir()
    (root / "scripts" / "agent_access_governance_gate.py").write_text("#\n")
    for sr in (".cursor/skills", ".claude/skills"):
        p = root / sr / "agent-access-governance-lite"
        p.mkdir(parents=True)
        (p / "SKILL.md").write_text("# agent-access-governance-lite\n")
    fixture = root / "marketing" / "data" / "code_health"
    fixture.mkdir(parents=True)
    (fixture / "agent_access_governance_discipline.json").write_text(
        json.dumps(
            {
                "least_privilege_agent_scopes": True,
                "role_attribute_policy_controls": True,
                "agent_mcp_api_inventory": True,
                "tool_call_policy_enforcement": True,
                "approval_gates_risky_ops": True,
                "immutable_audit_logs": True,
                "governance_maturity_model": True,
                "risk_reduction_not_generic_ai_security": True,
                "budget_gated_governance_saas": True,
                "budget": {"default_to_paid_governance_saas": False},
            }
        )
    )


class ClaimTests(unittest.TestCase):
    def test_health_signals(self) -> None:
        self.assertGreaterEqual(len(HEALTH_SIGNALS), 8)

    def test_unrestricted_blocked(self) -> None:
        d = evaluate_governance_claim({"action": "unrestricted_agent_tools"})
        self.assertFalse(d.ok)

    def test_inventory_incomplete(self) -> None:
        d = evaluate_governance_claim({"action": "inventory", "agents": True})
        self.assertFalse(d.ok)

    def test_inventory_ok(self) -> None:
        d = evaluate_governance_claim(
            {
                "action": "inventory",
                "agents": True,
                "mcp_servers": True,
                "apis": True,
                "service_accounts": True,
            }
        )
        self.assertTrue(d.ok)

    def test_risky_needs_approval(self) -> None:
        d = evaluate_governance_claim(
            {"action": "risky_op", "op": "payment", "audit_logged": True}
        )
        self.assertFalse(d.ok)

    def test_risky_ok(self) -> None:
        d = evaluate_governance_claim(
            {
                "action": "risky_op",
                "op": "payment",
                "human_approval": True,
                "audit_logged": True,
            }
        )
        self.assertTrue(d.ok)

    def test_generic_security_blocked(self) -> None:
        d = evaluate_governance_claim({"action": "generic_ai_security_pitch"})
        self.assertFalse(d.ok)


class PresenceTests(unittest.TestCase):
    def test_evaluate_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _scaffold(root)
            report = evaluate(root)
            self.assertTrue(report["ready"], report["blockers"])


if __name__ == "__main__":
    unittest.main()
