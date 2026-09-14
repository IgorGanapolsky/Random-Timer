"""TDD: AI employees (bounded workers), not open-ended agents."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.agent_ai_employees import (
    FLEET_MONTHLY_CAP_USD,
    MIN_ROI_MULTIPLE,
    apply_approval,
    evaluate_platform,
    evaluate_roi_gate,
    get_employee,
    list_employees,
    list_playbooks,
    load_memory,
    log_run,
    run_employee,
    save_memory,
    summarize_kpis,
)


class PlatformTests(unittest.TestCase):
    def test_ai_employees_platform_allowed(self) -> None:
        d = evaluate_platform(platform="ai_employees")
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_ai_employees")

    def test_multi_agent_swarm_blocked(self) -> None:
        d = evaluate_platform(platform="unbounded_multi_agent_swarm")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_multi_agent_swarm")

    def test_generic_research_agent_blocked(self) -> None:
        d = evaluate_platform(platform="generic_research_agent")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_generic_research_agent")


class RoleContractTests(unittest.TestCase):
    def test_exactly_two_seed_employees(self) -> None:
        employees = list_employees()
        self.assertEqual(len(employees), 2)
        ids = {e.employee_id for e in employees}
        self.assertEqual(ids, {"consulting_sales_engineer", "delivery_manager"})

    def test_each_employee_has_versioned_contract(self) -> None:
        for emp in list_employees():
            c = emp.contract
            self.assertTrue(c.version)
            self.assertTrue(c.inputs)
            self.assertTrue(c.permitted_tools)
            self.assertTrue(c.output_format)
            self.assertTrue(c.escalation_conditions)
            self.assertTrue(c.quality_bar)
            self.assertTrue(c.kpis)
            self.assertTrue(c.draft_only_actions)

    def test_unknown_employee_fails(self) -> None:
        with self.assertRaises(KeyError):
            get_employee("open_ended_agent")


class ApprovalGateTests(unittest.TestCase):
    def test_run_defaults_to_draft_pending_approval(self) -> None:
        result = run_employee(
            employee_id="consulting_sales_engineer",
            inputs={
                "prospect_name": "Acme AI Ops",
                "icp_fit_notes": "needs local-first automation",
                "offer": "AI employee setup sprint",
            },
            approve=False,
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.status, "draft_pending_approval")
        self.assertIn("outreach_sequence", result.outputs)
        self.assertIn("proposal_brief", result.outputs)

    def test_external_actions_require_explicit_approval(self) -> None:
        draft = run_employee(
            employee_id="consulting_sales_engineer",
            inputs={
                "prospect_name": "Acme AI Ops",
                "icp_fit_notes": "fit",
                "offer": "setup sprint",
            },
            approve=False,
        )
        denied = apply_approval(
            draft=draft,
            decision="send",
            approved=False,
        )
        self.assertFalse(denied.ok)
        self.assertEqual(denied.action, "block_unapproved_external_write")

        approved = apply_approval(
            draft=draft,
            decision="approve",
            approved=True,
        )
        self.assertTrue(approved.ok)
        self.assertEqual(approved.status, "approved")

    def test_delivery_manager_drafts_status_pack(self) -> None:
        result = run_employee(
            employee_id="delivery_manager",
            inputs={
                "meeting_notes": "Ship paywall fix; risk: Play bank verify",
                "github_activity": "PR #1916 merged",
                "stakeholder_messages": "Need weekly update",
            },
            approve=False,
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.status, "draft_pending_approval")
        for key in ("weekly_status", "risks", "decision_log", "next_actions"):
            self.assertIn(key, result.outputs)


class SystemsOfRecordTests(unittest.TestCase):
    def test_connectors_are_allowlisted_not_unbounded(self) -> None:
        sales = get_employee("consulting_sales_engineer")
        tools = set(sales.contract.permitted_tools)
        self.assertTrue({"gmail", "crm", "github", "calendar"} <= tools)
        self.assertNotIn("unbounded_browser", tools)
        self.assertNotIn("computer_control_all", tools)


class MemoryTests(unittest.TestCase):
    def test_durable_business_memory_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "memory.json"
            save_memory(
                path=path,
                record={
                    "clients": [{"name": "Acme"}],
                    "icp": "AI automation buyers",
                    "offers": ["setup sprint"],
                    "brand_voice": "direct evidence-first",
                    "pricing": {"setup_sprint_usd": 2500},
                    "decisions": ["prefer AI employees over agent swarms"],
                },
            )
            loaded = load_memory(path=path)
            self.assertEqual(loaded["icp"], "AI automation buyers")
            self.assertEqual(loaded["clients"][0]["name"], "Acme")


class ObservabilityTests(unittest.TestCase):
    def test_kpi_summary_tracks_outcomes_not_activity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "runs.jsonl"
            log_run(
                path=path,
                employee_id="consulting_sales_engineer",
                task_completed=True,
                accepted=True,
                edit_distance=0.1,
                factual_error=False,
                elapsed_sec=900,
                cost_usd=0.4,
                revenue_influenced_usd=2500.0,
            )
            log_run(
                path=path,
                employee_id="consulting_sales_engineer",
                task_completed=True,
                accepted=False,
                edit_distance=0.6,
                factual_error=True,
                elapsed_sec=1200,
                cost_usd=0.5,
                revenue_influenced_usd=0.0,
            )
            summary = summarize_kpis(path=path)
            self.assertEqual(summary["runs"], 2)
            self.assertAlmostEqual(summary["acceptance_rate"], 0.5)
            self.assertIn("avg_edit_distance", summary)
            self.assertIn("factual_error_rate", summary)
            self.assertIn("avg_elapsed_sec", summary)
            self.assertIn("avg_cost_usd", summary)
            self.assertIn("revenue_influenced_usd", summary)
            self.assertNotIn("tokens_generated", summary)


class RoiGateTests(unittest.TestCase):
    def test_kill_when_below_five_x(self) -> None:
        d = evaluate_roi_gate(
            engineering_and_tool_cost_usd=100.0,
            measured_value_usd=200.0,
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "kill_or_redesign")
        self.assertLess(d.score, MIN_ROI_MULTIPLE)

    def test_scale_when_at_least_five_x(self) -> None:
        d = evaluate_roi_gate(
            engineering_and_tool_cost_usd=100.0,
            measured_value_usd=600.0,
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "scale")
        self.assertGreaterEqual(d.score, MIN_ROI_MULTIPLE)

    def test_fleet_cap_constant(self) -> None:
        self.assertEqual(FLEET_MONTHLY_CAP_USD, 20.0)


class PlaybookTests(unittest.TestCase):
    def test_standard_playbooks_exist(self) -> None:
        ids = {p.playbook_id for p in list_playbooks()}
        self.assertTrue(
            {
                "discovery_to_sow",
                "meeting_to_execution",
                "lead_to_proposal",
            }
            <= ids
        )


if __name__ == "__main__":
    unittest.main()
