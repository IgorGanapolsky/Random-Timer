"""TDD: Apple Private Cloud Compute lite — eligibility + routing discipline."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.apple_pcc_gate import (
    ENTITLEMENT_KEY,
    HEALTH_SIGNALS,
    evaluate,
    evaluate_pcc_claim,
)


def _scaffold(root: Path) -> None:
    (root / "docs").mkdir()
    (root / "docs" / "APPLE_PRIVATE_CLOUD_COMPUTE.md").write_text(
        "\n".join(
            [
                "# Apple PCC",
                "App Store Small Business Program",
                "fewer than 2 million first-time downloads",
                "Private Cloud Compute entitlement",
                "prefer on-device then static fallback",
                "PostHog is proxy not App Store totals",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (root / "scripts").mkdir()
    (root / "scripts" / "apple_pcc_gate.py").write_text("#\n")
    for sr in (".cursor/skills", ".claude/skills"):
        p = root / sr / "apple-pcc-lite"
        p.mkdir(parents=True)
        (p / "SKILL.md").write_text("# apple-pcc-lite\n")
    svc = (
        root
        / "native-ios"
        / "RandomTimer"
        / "Sources"
        / "Services"
    )
    svc.mkdir(parents=True)
    (svc / "AppleIntelligenceCoach.swift").write_text("//\n")
    (svc / "AppleIntelligenceCoachService.swift").write_text("//\n")
    ent = root / "native-ios" / "RandomTimer"
    ent.mkdir(parents=True, exist_ok=True)
    (ent / "RandomTimer.entitlements").write_text(
        f"<key>{ENTITLEMENT_KEY}</key><true/>\n"
    )
    fixture = root / "marketing" / "data" / "code_health"
    fixture.mkdir(parents=True)
    (fixture / "apple_pcc_discipline.json").write_text(
        json.dumps(
            {
                "sbp_download_cap_tracked": True,
                "entitlement_declared_in_repo": True,
                "prefer_pcc_then_on_device_then_static": "x",
                "zero_cloud_api_cost_under_cap": "y",
                "no_claim_pcc_runtime_without_sdk": "z",
                "sdk_has_pcc_api_ios_26_5": False,
                "budget": {"subscribe_paid_llm_tips": False},
            }
        )
    )


class SignalTests(unittest.TestCase):
    def test_health_signals(self) -> None:
        self.assertEqual(len(HEALTH_SIGNALS), 5)


class ClaimTests(unittest.TestCase):
    def test_pcc_live_blocked_without_sdk(self) -> None:
        d = evaluate_pcc_claim({"action": "claim_pcc_live", "entitlement_assigned": True})
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_pcc_claim_without_sdk")

    def test_pcc_live_blocked_without_entitlement(self) -> None:
        d = evaluate_pcc_claim(
            {"action": "claim_pcc_live", "sdk_has_pcc_api": True, "entitlement_assigned": False}
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_pcc_claim_without_entitlement")

    def test_paid_cloud_blocked_while_eligible(self) -> None:
        d = evaluate_pcc_claim(
            {
                "action": "buy_paid_cloud_tips",
                "sbp_eligible": True,
                "under_download_cap": True,
            }
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_paid_cloud_while_eligible")

    def test_posthog_proxy_not_first_time_total(self) -> None:
        d = evaluate_pcc_claim(
            {
                "action": "claim_under_download_cap",
                "source": "posthog",
                "first_time_downloads": 51,
            }
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_proxy_as_first_time_downloads")

    def test_on_device_path_allowed(self) -> None:
        d = evaluate_pcc_claim({"action": "use_on_device_foundation_models"})
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_apple_intelligence_path")

    def test_pcc_live_allowed_with_evidence(self) -> None:
        d = evaluate_pcc_claim(
            {
                "action": "claim_pcc_live",
                "sdk_has_pcc_api": True,
                "entitlement_assigned": True,
            }
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_pcc_live_claim")


class PresenceTests(unittest.TestCase):
    def test_evaluate_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _scaffold(root)
            report = evaluate(root)
            self.assertTrue(report["ready"], report["blockers"])
            self.assertEqual(report["framework"], "apple-pcc-lite")

    def test_evaluate_blocks_missing_entitlement(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _scaffold(root)
            (root / "native-ios" / "RandomTimer" / "RandomTimer.entitlements").write_text(
                "<dict/>\n"
            )
            report = evaluate(root)
            self.assertFalse(report["ready"])
            self.assertTrue(
                any("missing_entitlement" in b for b in report["blockers"]),
                report["blockers"],
            )


if __name__ == "__main__":
    unittest.main()
