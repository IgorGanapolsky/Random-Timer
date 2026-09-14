"""TDD: Pi-style gated engineering harness (pi-yolo)."""

from __future__ import annotations

import unittest

from scripts.agent_pi_yolo import (
    FLEET_MONTHLY_CAP_USD,
    QUALITY_COMMANDS,
    build_evidence_package,
    evaluate_definition_of_done,
    evaluate_plan_gate,
    evaluate_platform,
    evaluate_task_class,
    record_kpi,
    validate_repo_rules,
)


class PlatformTests(unittest.TestCase):
    def test_local_pi_yolo_allowed(self) -> None:
        d = evaluate_platform(platform="local_pi_yolo")
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_local_pi_yolo")

    def test_unrestricted_multi_agent_company_denied(self) -> None:
        d = evaluate_platform(platform="autonomous_coding_company")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_overbroad_autonomy")


class TaskClassTests(unittest.TestCase):
    def test_issue_to_pr_allowed(self) -> None:
        d = evaluate_task_class(task_class="issue_to_pr")
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_task_class")

    def test_ambiguous_product_denied(self) -> None:
        d = evaluate_task_class(task_class="ambiguous_product_rewrite")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_ambiguous_task")


class PlanGateTests(unittest.TestCase):
    def test_requires_plan_and_approval_without_yolo(self) -> None:
        d = evaluate_plan_gate(
            has_plan=True,
            plan_approved=False,
            yolo=False,
            acceptance_criteria=("tests_green",),
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "require_plan_approval")

    def test_yolo_auto_approves_when_criteria_present(self) -> None:
        d = evaluate_plan_gate(
            has_plan=True,
            plan_approved=False,
            yolo=True,
            acceptance_criteria=("tests_green", "evidence_package"),
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_yolo_plan")

    def test_missing_plan_fails(self) -> None:
        d = evaluate_plan_gate(
            has_plan=False,
            plan_approved=True,
            yolo=True,
            acceptance_criteria=("tests_green",),
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_missing_plan")


class RepoRulesTests(unittest.TestCase):
    def test_blocks_secrets_and_unapproved_deps(self) -> None:
        d = validate_repo_rules(
            touches_secrets=True,
            production_change=False,
            adds_dependency=False,
            dependency_approved=False,
            uses_worktree=True,
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_secrets")

    def test_blocks_dependency_without_approval(self) -> None:
        d = validate_repo_rules(
            touches_secrets=False,
            production_change=False,
            adds_dependency=True,
            dependency_approved=False,
            uses_worktree=True,
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_unapproved_dependency")

    def test_allows_clean_worktree_change(self) -> None:
        d = validate_repo_rules(
            touches_secrets=False,
            production_change=False,
            adds_dependency=False,
            dependency_approved=False,
            uses_worktree=True,
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_repo_rules")


class DefinitionOfDoneTests(unittest.TestCase):
    def test_incomplete_dod_fails(self) -> None:
        d = evaluate_definition_of_done(
            files_changed=("a.py",),
            tests_run=(),
            tests_passed=False,
            risks_documented=True,
            rollback_notes=True,
            evidence_paths=(),
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_incomplete_dod")

    def test_complete_dod_passes(self) -> None:
        d = evaluate_definition_of_done(
            files_changed=("scripts/agent_pi_yolo.py",),
            tests_run=("scripts/tests/test_agent_pi_yolo.py",),
            tests_passed=True,
            risks_documented=True,
            rollback_notes=True,
            evidence_paths=("marketing/data/agent_pi_yolo.json",),
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_definition_of_done")


class EvidenceAndKpiTests(unittest.TestCase):
    def test_quality_commands_include_python_tests(self) -> None:
        self.assertIn("python3 -m pytest", " ".join(QUALITY_COMMANDS))
        self.assertEqual(FLEET_MONTHLY_CAP_USD, 20.0)

    def test_evidence_package_shape(self) -> None:
        pkg = build_evidence_package(
            files_changed=("a.py",),
            tests_run=("test_a.py",),
            tests_passed=True,
            risks=("none",),
            rollback_notes="revert commit",
            plan_summary="add harness",
        )
        self.assertEqual(pkg["files_changed"], ["a.py"])
        self.assertTrue(pkg["tests_passed"])

    def test_kpi_records_roi_inputs(self) -> None:
        row = record_kpi(
            task_id="t1",
            minutes_to_mergeable_pr=45.0,
            human_review_minutes=8.0,
            first_pass_tests=True,
            rework=False,
            usd_per_success=0.12,
        )
        self.assertEqual(row["task_id"], "t1")
        self.assertTrue(row["first_pass_tests"])
        self.assertAlmostEqual(row["usd_per_success"], 0.12)


if __name__ == "__main__":
    unittest.main()
