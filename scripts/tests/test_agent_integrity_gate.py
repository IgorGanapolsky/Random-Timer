"""TDD: human is the integrity standard agents are held to (Terra / CTech)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.agent_integrity_gate import (
    INTEGRITY_PILLARS,
    evaluate,
    evaluate_agent_claim,
    evaluate_research_loop,
)


class PillarTests(unittest.TestCase):
    def test_four_pillars(self) -> None:
        self.assertEqual(
            list(INTEGRITY_PILLARS),
            [
                "human_standard",
                "velocity_with_rigor",
                "research_product_loop",
                "critical_judgment_human",
            ],
        )


class ClaimTests(unittest.TestCase):
    def test_speed_without_verification_blocked(self) -> None:
        d = evaluate_agent_claim(
            {
                "claim": "done",
                "evidence": "looks right, shipped fast",
                "verified_readback": False,
            }
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_velocity_without_integrity")

    def test_absolute_truth_claim_blocked(self) -> None:
        d = evaluate_agent_claim(
            {
                "claim": "expert judgment fully captured",
                "evidence": "absolute truth in the skill",
                "verified_readback": True,
            }
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_absolute_expert_capture")

    def test_verified_claim_allowed(self) -> None:
        d = evaluate_agent_claim(
            {
                "claim": "store upload complete",
                "evidence": "Publisher API versionCodes include 1360",
                "verified_readback": True,
                "human_judgment_at": "production-signoff",
            }
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_integrity_backed_claim")


class LoopTests(unittest.TestCase):
    def test_loop_requires_both_directions(self) -> None:
        d = evaluate_research_loop(
            {
                "research_to_product": "encode store read-back into gate",
                "product_to_research": "",
            }
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_one_way_loop")

    def test_bidirectional_loop_ok(self) -> None:
        d = evaluate_research_loop(
            {
                "research_to_product": "formalize release completion stages",
                "product_to_research": "agent stuck at CDN lag → new verification question",
            }
        )
        self.assertTrue(d.ok)


class RepoPresenceTests(unittest.TestCase):
    def test_missing_docs_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = evaluate(Path(tmp))
            self.assertFalse(report["ready"])
            self.assertIn("missing_docs/AGENT_INTEGRITY.md", report["blockers"])

    def test_wired_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "AGENT_INTEGRITY.md").write_text(
                "\n".join(
                    [
                        "# Agent Integrity",
                        "human is the standard the agents are held to",
                        "velocity without integrity",
                        "research product feedback loop",
                        "critical judgment",
                        "muscle memory",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            (root / "scripts").mkdir()
            (root / "scripts" / "agent_integrity_gate.py").write_text("#\n")
            for sr in (".cursor/skills", ".claude/skills"):
                p = root / sr / "agent-integrity-lite"
                p.mkdir(parents=True)
                (p / "SKILL.md").write_text("# agent-integrity-lite\n")
            fixture = root / "marketing" / "data" / "integrity"
            fixture.mkdir(parents=True)
            (fixture / "native_release_integrity.json").write_text(
                json.dumps(
                    {
                        "name": "native_release_integrity",
                        "human_standard": "CTO evidence read-back before done",
                        "velocity_with_rigor": "CI + store API verify before claim",
                        "research_product_loop": {
                            "research_to_product": "completion loop stages in gate",
                            "product_to_research": "CDN lag vs API truth gap",
                        },
                        "critical_judgment_human": "production-signoff",
                        "never_absolute": True,
                    }
                )
            )
            report = evaluate(root)
            self.assertTrue(report["ready"], msg=json.dumps(report, indent=2))


if __name__ == "__main__":
    unittest.main()
