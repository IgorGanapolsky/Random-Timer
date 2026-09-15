#!/usr/bin/env python3
"""Apple Private Cloud Compute lite — zero-cost Foundation Models under SBP.

Source:
  https://developer.apple.com/private-cloud-compute/

Apple thesis: App Store Small Business Program developers under 2M first-time
downloads can use Apple Foundation Models on Private Cloud Compute with no
cloud API cost once the PCC entitlement is assigned.

High-ROI steals for Random Timer (hard monthly budget — no paid LLM SaaS tips):
  - Prefer PCC → on-device Foundation Models → static fallback
  - Declare com.apple.developer.private-cloud-compute in entitlements
  - Never claim PCC runtime before SDK exposes it
  - Never treat PostHog install proxies as App Store first-time download totals
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

SOURCE = "https://developer.apple.com/private-cloud-compute/"

HEALTH_SIGNALS = (
    "sbp_download_cap_tracked",
    "entitlement_declared_in_repo",
    "prefer_pcc_then_on_device_then_static",
    "zero_cloud_api_cost_under_cap",
    "no_claim_pcc_runtime_without_sdk",
)

ENTITLEMENT_KEY = "com.apple.developer.private-cloud-compute"
FIRST_TIME_DOWNLOAD_CAP = 2_000_000


def evaluate_pcc_claim(claim: Mapping[str, object]) -> Decision:
    action = norm(claim.get("action"))
    backend = norm(claim.get("backend") or claim.get("runtime"))

    if action in {"claim_pcc_live", "claim_pcc_production"} and claim.get("sdk_has_pcc_api") is not True:
        return Decision(
            action="block_pcc_claim_without_sdk",
            ok=False,
            reason="do not claim PCC runtime until sdk_has_pcc_api=true (absent on iOS 26.5 SDK)",
        )

    if action in {"claim_pcc_live", "claim_pcc_production"} and claim.get("entitlement_assigned") is not True:
        return Decision(
            action="block_pcc_claim_without_entitlement",
            ok=False,
            reason="require entitlement_assigned=true on the Apple developer account",
        )

    if action in {"buy_paid_cloud_tips", "subscribe_paid_llm_tips"}:
        eligible = claim.get("sbp_eligible")
        under_cap = claim.get("under_download_cap")
        if eligible is True and under_cap is True:
            return Decision(
                action="block_paid_cloud_while_eligible",
                ok=False,
                reason="SBP + under 2M first-time downloads → use PCC/on-device, not paid cloud tips",
            )

    if action in {"claim_under_download_cap", "claim_first_time_downloads"}:
        if claim.get("source") in {None, "", "posthog", "posthog_proxy", "install_proxy"}:
            return Decision(
                action="block_proxy_as_first_time_downloads",
                ok=False,
                reason="App Store Connect Analytics is ground truth for first-time downloads; PostHog is proxy only",
            )
        try:
            total = int(claim.get("first_time_downloads"))  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return Decision(
                action="block_malformed_download_total",
                ok=False,
                reason="first_time_downloads must be an integer from App Store Connect",
            )
        if total >= FIRST_TIME_DOWNLOAD_CAP:
            return Decision(
                action="block_over_download_cap",
                ok=False,
                reason="first-time downloads at or above 2M — migrate off free PCC within Apple's window",
            )

    if backend == "private_cloud_compute" and claim.get("sdk_has_pcc_api") is not True:
        return Decision(
            action="block_pcc_backend_without_sdk",
            ok=False,
            reason="route to on-device or static until PCC API ships in the SDK",
        )

    if action in {
        "use_on_device_foundation_models",
        "use_static_fallback",
        "declare_entitlement",
        "track_sbp_eligibility",
    }:
        return Decision(
            action="allow_apple_intelligence_path",
            ok=True,
            reason="zero-cost Apple Intelligence / eligibility discipline path",
        )

    if action in {"claim_pcc_live", "claim_pcc_production"}:
        return Decision(
            action="allow_pcc_live_claim",
            ok=True,
            reason="SDK + entitlement evidence present for PCC claim",
        )

    return Decision(
        action="block_unknown_pcc_action",
        ok=False,
        reason=(
            "declare action: use_on_device_foundation_models|use_static_fallback|"
            "declare_entitlement|track_sbp_eligibility|claim_pcc_live|buy_paid_cloud_tips"
        ),
    )


def _entitlement_declared(repo: Path) -> bool:
    path = repo / "native-ios" / "RandomTimer" / "RandomTimer.entitlements"
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    return ENTITLEMENT_KEY in text


def evaluate(repo: Path) -> dict[str, Any]:
    blockers: list[str] = []
    if not (repo / "docs" / "APPLE_PRIVATE_CLOUD_COMPUTE.md").is_file():
        blockers.append("missing_docs/APPLE_PRIVATE_CLOUD_COMPUTE.md")
    if not (repo / "scripts" / "apple_pcc_gate.py").is_file():
        blockers.append("missing_scripts/apple_pcc_gate.py")
    blockers.extend(require_dual_skills(repo, "apple-pcc-lite"))
    blockers.extend(
        require_docs_needles(
            repo / "docs" / "APPLE_PRIVATE_CLOUD_COMPUTE.md",
            (
                "small business",
                "2 million",
                "private cloud compute",
                "entitlement",
                "on-device",
                "static",
                "posthog",
            ),
        )
    )

    coach = (
        repo
        / "native-ios"
        / "RandomTimer"
        / "Sources"
        / "Services"
        / "AppleIntelligenceCoach.swift"
    )
    service = (
        repo
        / "native-ios"
        / "RandomTimer"
        / "Sources"
        / "Services"
        / "AppleIntelligenceCoachService.swift"
    )
    if not coach.is_file():
        blockers.append("missing_ios:AppleIntelligenceCoach.swift")
    if not service.is_file():
        blockers.append("missing_ios:AppleIntelligenceCoachService.swift")
    if not _entitlement_declared(repo):
        blockers.append("missing_entitlement:com.apple.developer.private-cloud-compute")

    fixture = (
        repo / "marketing" / "data" / "code_health" / "apple_pcc_discipline.json"
    )
    if not fixture.is_file():
        blockers.append(
            "missing_fixture:marketing/data/code_health/apple_pcc_discipline.json"
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
            if not isinstance(budget, dict) or budget.get("subscribe_paid_llm_tips") is not False:
                blockers.append("fixture_missing:budget.subscribe_paid_llm_tips=false")
            if charter.get("sdk_has_pcc_api_ios_26_5") is not False:
                blockers.append("fixture_missing:sdk_has_pcc_api_ios_26_5=false")

    ready = len(blockers) == 0
    return {
        "framework": "apple-pcc-lite",
        "source": SOURCE,
        "ready": ready,
        "blockers": blockers,
        "health_signals": list(HEALTH_SIGNALS),
        "anti_pattern": "paid_cloud_tips_while_sbp_eligible",
        "entitlement_key": ENTITLEMENT_KEY,
        "first_time_download_cap": FIRST_TIME_DOWNLOAD_CAP,
        "budget_note": "zero cloud API cost under SBP+<2M; on-device FM until PCC SDK ships",
        "sdk_note": "PrivateCloudComputeLanguageModel not present in Xcode 26.5 / iOS 26.5 SDK",
    }


def main(argv: list[str] | None = None) -> int:
    return run_presence_cli(
        description=__doc__ or "apple-pcc-lite",
        evaluate=evaluate,
        claim_evaluator=evaluate_pcc_claim,
        argv=argv,
    )


if __name__ == "__main__":
    raise SystemExit(main())
