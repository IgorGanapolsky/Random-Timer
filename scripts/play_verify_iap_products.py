#!/usr/bin/env python3
"""Read back Google Play monetization product states for Random Timer."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.play_monetization_client import (
    PACKAGE,
    REQUIRED_ELITE_ANNUAL_BASE_PLAN_ID,
    REQUIRED_MONTHLY_BASE_PLAN_ID,
    REQUIRED_ONE_TIME,
    REQUIRED_SUBSCRIPTIONS,
    build_android_publisher_service,
    list_one_time_products,
    list_subscription_products,
    resolve_play_credentials,
    subscription_purchase_blockers,
    subscription_purchase_warnings,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-out", default="", help="Optional JSON output path")
    args = parser.parse_args()

    key_value = resolve_play_credentials()
    if not key_value:
        print("Missing GOOGLE_PLAY_JSON_KEY or GOOGLE_PLAY_JSON_KEY_PATH", file=sys.stderr)
        return 2

    service = build_android_publisher_service(key_value)
    one_time = list_one_time_products(service)
    subscriptions = list_subscription_products(service)
    all_products = one_time + subscriptions

    found_ids = {p["product_id"] for p in all_products}
    missing = [
        *[pid for pid in REQUIRED_ONE_TIME if pid not in found_ids],
        *[pid for pid in REQUIRED_SUBSCRIPTIONS if pid not in found_ids],
    ]
    blockers = subscription_purchase_blockers(subscriptions)
    warnings = subscription_purchase_warnings(subscriptions)

    report = {
        "package": PACKAGE,
        "one_time_products": one_time,
        "subscriptions": subscriptions,
        "required_missing": missing,
        "subscription_purchase_blockers": blockers,
        "subscription_purchase_warnings": warnings,
        "required_elite_annual_base_plan_id": REQUIRED_ELITE_ANNUAL_BASE_PLAN_ID,
        "required_monthly_base_plan_id": REQUIRED_MONTHLY_BASE_PLAN_ID,
        "status": (
            "ok"
            if not missing and not blockers
            else "missing_products"
            if missing
            else "subscription_not_purchasable"
        ),
    }

    print("== Play IAP Product Readiness ==")
    print(json.dumps(report, indent=2, sort_keys=True))

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, sort_keys=True)

    return 0 if not missing and not blockers else 1


if __name__ == "__main__":
    raise SystemExit(main())
