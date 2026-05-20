#!/usr/bin/env python3
"""Activate required Google Play monetization products for Random Timer."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

PACKAGE = "com.iganapolsky.randomtimer"
TARGET_ONE_TIME = "pro_base"


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


def _activate_one_time_product(service: Any, product_id: str) -> dict[str, Any]:
    monetization = service.monetization()
    product = (
        monetization.onetimeproducts()
        .get(packageName=PACKAGE, productId=product_id)
        .execute()
    )
    actions: list[dict[str, Any]] = []
    purchase_options = product.get("purchaseOptions") or []
    for option in purchase_options:
        purchase_option_id = option.get("purchaseOptionId") or option.get("id") or ""
        if not purchase_option_id:
            continue
        state = (option.get("state") or option.get("status") or "").upper()
        if state == "ACTIVE":
            actions.append(
                {
                    "purchase_option_id": purchase_option_id,
                    "action": "skip",
                    "reason": "already_active",
                }
            )
            continue
        try:
            monetization.onetimeproducts().purchaseOptions().batchUpdateStates(
                packageName=PACKAGE,
                productId=product_id,
                body={
                    "requests": [
                        {
                            "purchaseOptionId": purchase_option_id,
                            "state": "ACTIVE",
                        }
                    ]
                },
            ).execute()
            actions.append(
                {
                    "purchase_option_id": purchase_option_id,
                    "action": "activated",
                    "prior_state": state or "unknown",
                }
            )
        except Exception as exc:  # noqa: BLE001 - surface API failure in JSON report
            actions.append(
                {
                    "purchase_option_id": purchase_option_id,
                    "action": "error",
                    "error": str(exc),
                    "prior_state": state or "unknown",
                }
            )
    return {"product_id": product_id, "actions": actions}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-out", default="", help="Optional JSON output path")
    parser.add_argument("--dry-run", action="store_true", help="Inspect only; do not mutate")
    args = parser.parse_args()

    key_value = _resolve_key()
    if not key_value:
        print("Missing GOOGLE_PLAY_JSON_KEY or GOOGLE_PLAY_JSON_KEY_PATH", file=sys.stderr)
        return 2

    service = _build_service(key_value)
    report: dict[str, Any] = {
        "package": PACKAGE,
        "dry_run": args.dry_run,
        "target_one_time": TARGET_ONE_TIME,
    }

    if args.dry_run:
        payload = (
            service.monetization()
            .onetimeproducts()
            .list(packageName=PACKAGE)
            .execute()
        )
        report["one_time_products"] = payload.get("oneTimeProducts") or []
    else:
        report["activation"] = _activate_one_time_product(service, TARGET_ONE_TIME)

    print(json.dumps(report, indent=2, sort_keys=True))
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, sort_keys=True)

    activation = report.get("activation") or {}
    errors = [
        item
        for item in activation.get("actions") or []
        if item.get("action") == "error"
    ]
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
