"""TDD: pre-recursive agent ops (claim→dependency→wedge→proof + HITL eval gates)."""

from __future__ import annotations

import unittest

from scripts.agent_pre_recursive_ops import (
    FLEET_MONTHLY_CAP_USD,
    approval_gate,
    compound_loop_policy,
    evaluate_platform,
    plan_ops_wedge,
    rank_wedges,
    select_infra_posture,
    validate_claim_card,
)


class PlatformTests(unittest.TestCase):
    def test_local_pre_recursive_ops_allowed(self) -> None:
        d = evaluate_platform(platform="local_pre_recursive_ops")
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_local_pre_recursive_ops")

    def test_foundation_lab_training_denied_under_cap(self) -> None:
        d = evaluate_platform(platform="foundation_model_lab_training")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_foundation_spend")


class ClaimCardTests(unittest.TestCase):
    def test_incomplete_card_fails(self) -> None:
        d = validate_claim_card(
            claim="agents can speed up software R&D",
            dependency="",
            wedge_12m="repo maintenance bots",
            proof_metric="hours_saved",
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_incomplete_claim_card")

    def test_complete_card_passes(self) -> None:
        d = validate_claim_card(
            claim="agents can materially speed up software R&D",
            dependency="coding_reliability + evals + human_review",
            wedge_12m="PR CI triage with acceptance checklist",
            proof_metric="hours_saved_per_week",
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_claim_card")


class RankWedgeTests(unittest.TestCase):
    def test_application_eval_wedge_ranks_above_foundation(self) -> None:
        ranked = rank_wedges(
            cards=(
                {
                    "id": "foundation",
                    "claim": "train a better base model",
                    "dependency": "compute",
                    "wedge_12m": "fine-tune in cloud lab",
                    "proof_metric": "benchmark_points",
                    "layer": "foundation",
                    "bottleneck": "compute",
                    "hours_saved_per_week": 2.0,
                    "effort": 10.0,
                },
                {
                    "id": "eval_ops",
                    "claim": "evals make agent output deployable",
                    "dependency": "acceptance_criteria + evidence",
                    "wedge_12m": "CI failure triage with proof metric",
                    "proof_metric": "tickets_closed",
                    "layer": "application",
                    "bottleneck": "evaluation",
                    "hours_saved_per_week": 8.0,
                    "effort": 2.0,
                },
            )
        )
        self.assertEqual(ranked[0]["id"], "eval_ops")
        self.assertGreater(ranked[0]["score"], ranked[1]["score"])


class ApprovalGateTests(unittest.TestCase):
    def test_requires_human_when_incomplete(self) -> None:
        d = approval_gate(
            acceptance_met=False,
            evidence_paths=(),
            human_approved=False,
            irreversible=False,
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "require_human_review")

    def test_blocks_irreversible_without_approval(self) -> None:
        d = approval_gate(
            acceptance_met=True,
            evidence_paths=("marketing/data/proof.json",),
            human_approved=False,
            irreversible=True,
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_irreversible_without_approval")

    def test_auto_allows_complete_reversible(self) -> None:
        d = approval_gate(
            acceptance_met=True,
            evidence_paths=("marketing/data/proof.json",),
            human_approved=False,
            irreversible=False,
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_auto_with_evidence")


class CompoundLoopTests(unittest.TestCase):
    def test_reject_full_replacement_claim(self) -> None:
        d = compound_loop_policy(
            target_speedup=10.0,
            human_in_loop=False,
            replaces_engineer=True,
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_full_replacement")

    def test_accept_realistic_speedup_with_hitl(self) -> None:
        d = compound_loop_policy(
            target_speedup=3.0,
            human_in_loop=True,
            replaces_engineer=False,
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_compound_loop")


class InfraPostureTests(unittest.TestCase):
    def test_fleet_cap_constant(self) -> None:
        self.assertEqual(FLEET_MONTHLY_CAP_USD, 20.0)

    def test_prefer_application_layer(self) -> None:
        d = select_infra_posture(
            needs_foundation_training=False,
            month_to_date_spend_usd=1.0,
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "application_layer_automation")

    def test_block_foundation_under_budget(self) -> None:
        d = select_infra_posture(
            needs_foundation_training=True,
            month_to_date_spend_usd=0.0,
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_foundation_under_cap")


class PlanOpsTests(unittest.TestCase):
    def test_plan_blocks_lazy_foundation_pitch(self) -> None:
        report = plan_ops_wedge(
            platform="local_pre_recursive_ops",
            claim="recursive self-improvement soon",
            dependency="",
            wedge_12m="",
            proof_metric="",
            layer="foundation",
            bottleneck="compute",
            hours_saved_per_week=1.0,
            effort=20.0,
            target_speedup=20.0,
            human_in_loop=False,
            replaces_engineer=True,
            acceptance_met=False,
            evidence_paths=(),
            human_approved=False,
            irreversible=True,
            needs_foundation_training=True,
            month_to_date_spend_usd=0.0,
        )
        self.assertFalse(report["ok"])
        self.assertEqual(report["claim_card"]["action"], "block_incomplete_claim_card")

    def test_plan_passes_eval_ops_wedge(self) -> None:
        report = plan_ops_wedge(
            platform="local_pre_recursive_ops",
            claim="evals make agent engineering deployable",
            dependency="acceptance_criteria + evidence + human_review",
            wedge_12m="CI triage + store ops with proof metrics",
            proof_metric="hours_saved_per_week",
            layer="application",
            bottleneck="evaluation",
            hours_saved_per_week=6.0,
            effort=2.0,
            target_speedup=3.0,
            human_in_loop=True,
            replaces_engineer=False,
            acceptance_met=True,
            evidence_paths=("marketing/data/agent_pre_recursive_ops.json",),
            human_approved=False,
            irreversible=False,
            needs_foundation_training=False,
            month_to_date_spend_usd=2.0,
        )
        self.assertTrue(report["ok"])
        self.assertEqual(report["infra"]["action"], "application_layer_automation")
        self.assertEqual(report["compound_loop"]["action"], "allow_compound_loop")
        self.assertEqual(report["approval"]["action"], "allow_auto_with_evidence")


if __name__ == "__main__":
    unittest.main()
