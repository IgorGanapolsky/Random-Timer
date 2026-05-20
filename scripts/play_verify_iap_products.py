#!/usr/bin/env python3
"""Read back Google Play monetization product states for Random Timer."""

from __future__ import annotations

import argparse
import json
import sys

from scripts.play_monetization_client import (
    PACKAGE,
    REQUIRED_ONE_TIME,
    REQUIRED_SUBSCRIPTIONS,
    build_android_publisher_service,
    list_one_time_products,
    list_subscription_products,
    resolve_play_credentials,
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
