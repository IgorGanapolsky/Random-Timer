#!/usr/bin/env python3
"""Read back Google Play monetization product states for Random Timer."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

PACKAGE = "com.iganapolsky.randomtimer"
REQUIRED_ONE_TIME = ("pro_base",)
REQUIRED_SUBSCRIPTIONS = ("elite_tactical", "elite_tactical_monthly")


def _resolve_key() -> str:
    value = (os.environ.get("GOOGLE_PLAY_JSON_KEY") or "").strip()
    if value:
        return value
    path = (os.environ.get("GOOGLE_PLAY_JSON_KEY_PATH") or "").strip()
    if path and os.path.isfile(path):
        return path
    return ""


def _build_service(key_value: str):
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    scopes = ["https://www.googleapis.com/auth/androidpublisher"]
    if os.path.isfile(key_value):
        credentials = service_account.Credentials.from_service_account_file(
            key_value, scopes=scopes
        )
    else:
        credentials = service_account.Credentials.from_service_account_info(
            json.loads(key_value), scopes=scopes
        )
    return build("androidpublisher", "v3", credentials=credentials)


def _list_one_time(service: Any) -> list[dict[str, Any]]:
    payload = (
        service.monetization()
        .onetimeproducts()
        .list(packageName=PACKAGE)
        .execute()
    )
    products: list[dict[str, Any]] = []
    for item in payload.get("oneTimeProducts") or []:
        product_id = item.get("productId") or item.get("sku") or "unknown"
        state = item.get("state") or item.get("status") or "unknown"
        products.append({"product_id": product_id, "state": state, "kind": "one_time"})
    return products


def _list_subscriptions(service: Any) -> list[dict[str, Any]]:
    payload = (
        service.monetization()
        .subscriptions()
        .list(packageName=PACKAGE)
        .execute()
    )
    products: list[dict[str, Any]] = []
    for item in payload.get("subscriptions") or []:
        product_id = item.get("productId") or "unknown"
        state = item.get("state") or item.get("status") or "unknown"
        base_plans = []
        for plan in item.get("basePlans") or []:
            base_plans.append(
                {
                    "base_plan_id": plan.get("basePlanId") or "unknown",
                    "state": plan.get("state") or plan.get("status") or "unknown",
                }
            )
        products.append(
            {
                "product_id": product_id,
                "state": state,
                "kind": "subscription",
                "base_plans": base_plans,
            }
        )
    return products


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-out", default="", help="Optional JSON output path")
    args = parser.parse_args()

    key_value = _resolve_key()
    if not key_value:
        print("Missing GOOGLE_PLAY_JSON_KEY or GOOGLE_PLAY_JSON_KEY_PATH", file=sys.stderr)
        return 2

    service = _build_service(key_value)
    one_time = _list_one_time(service)
    subscriptions = _list_subscriptions(service)
    all_products = one_time + subscriptions

    found_ids = {p["product_id"] for p in all_products}
    missing = [
        * [pid for pid in REQUIRED_ONE_TIME if pid not in found_ids],
        * [pid for pid in REQUIRED_SUBSCRIPTIONS if pid not in found_ids],
    ]

    report = {
        "package": PACKAGE,
        "one_time_products": one_time,
        "subscriptions": subscriptions,
        "required_missing": missing,
        "status": "ok" if not missing else "missing_products",
    }

    print("== Play IAP Product Readiness ==")
    print(json.dumps(report, indent=2, sort_keys=True))

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, sort_keys=True)

    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
