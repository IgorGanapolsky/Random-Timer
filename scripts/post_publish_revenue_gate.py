#!/usr/bin/env python3
"""GSD gate: public store versions match configured post-publish expectations."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts import verify_public_store_versions as store_verify


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_gate_config(gate_path: Path) -> dict:
    if not gate_path.is_file():
        return {}
    try:
        payload = json.loads(gate_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def resolve_gate_expected_versions(
    *,
    platform: str,
    repo_root: Path,
    gate_config: dict,
) -> tuple[str, str, str]:
    """Prefer per-platform expected versions from post_publish_gate.json."""
    ios_cfg = str(gate_config.get("expected_ios") or "").strip()
    android_cfg = str(gate_config.get("expected_android") or "").strip()

    if ios_cfg or android_cfg:
        gh_ios, gh_android, _ = store_verify.resolve_expected_versions(
            platform=platform,
            expected_version="",
            ios_expected_version="",
            android_expected_version="",
            expected_source="github_latest_release",
            repo_root=repo_root,
        )
        ios = ios_cfg or gh_ios
        android = android_cfg or gh_android
        return ios, android, "post_publish_gate"

    return store_verify.resolve_expected_versions(
        platform=platform,
        expected_version="",
        ios_expected_version="",
        android_expected_version="",
        expected_source="github_latest_release",
        repo_root=repo_root,
    )


def build_report(
    *,
    repo_root: Path,
    platform: str,
    timeout: int,
    gate_config_path: Path | None = None,
) -> dict:
    gate_path = gate_config_path or (repo_root / "marketing" / "data" / "post_publish_gate.json")
    prior_config = load_gate_config(gate_path)

    ios_expected, android_expected, expected_source = resolve_gate_expected_versions(
        platform=platform,
        repo_root=repo_root,
        gate_config=prior_config,
    )

    def verify_once() -> list[store_verify.StoreVersionResult]:
        checks: list[store_verify.StoreVersionResult] = []
        if platform in {"ios", "both"}:
            checks.append(
                store_verify.verify_app_store_public_version(
                    store_verify.DEFAULT_IOS_APP_ID,
                    ios_expected,
                )
            )
        if platform in {"android", "both"}:
            checks.append(
                store_verify.verify_play_public_version(
                    store_verify.DEFAULT_ANDROID_PACKAGE,
                    android_expected,
                )
            )
        return checks

    results = store_verify.poll_until_public(verify_once, timeout, poll_interval=0)
    store_pass = all(r.passed for r in results)

    paywall_path = repo_root / "marketing" / "data" / "paywall_conversion_report.json"
    paywall_summary = None
    if paywall_path.is_file():
        paywall = json.loads(paywall_path.read_text(encoding="utf-8"))
        funnel = paywall.get("funnel") or {}
        paywall_summary = {
            "generated_at": paywall.get("generated_at"),
            "purchase_successes_30d": funnel.get("purchase_successes"),
            "purchase_attempts_30d": funnel.get("purchase_attempts"),
        }

    prior_stores = {
        str(entry.get("platform")): entry
        for entry in (prior_config.get("stores") or [])
        if isinstance(entry, dict) and entry.get("platform")
    }

    stores: list[dict] = []
    for result in results:
        store_entry = {
            "platform": result.platform,
            "passed": result.passed,
            "expected_version": result.expected_version,
            "observed_version": result.observed_version,
            "status": result.status,
        }
        prior_entry = prior_stores.get(result.platform) or {}
        note = prior_entry.get("note")
        if note and result.passed:
            store_entry["note"] = note
        stores.append(store_entry)

    report: dict = {
        "source": "post_publish_revenue_gate",
        "generated_at": _utc_now(),
        "expected_source": expected_source,
        "expected_ios": ios_expected,
        "expected_android": android_expected,
        "store_public_pass": store_pass,
        "stores": stores,
        "paywall_proxy": paywall_summary,
        "revenue_note": (
            "store_public_pass does not imply revenue; check paywall_purchase_success in PostHog."
        ),
    }

    ship_evidence = prior_config.get("ship_evidence")
    if isinstance(ship_evidence, dict):
        report["ship_evidence"] = ship_evidence

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=_REPO_ROOT)
    parser.add_argument("--platform", choices=("ios", "android", "both"), default="both")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument(
        "--json-out",
        type=Path,
        default=_REPO_ROOT / "marketing" / "data" / "post_publish_gate.json",
    )
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    report = build_report(
        repo_root=repo_root,
        platform=args.platform,
        timeout=args.timeout,
        gate_config_path=args.json_out.resolve(),
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["store_public_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
