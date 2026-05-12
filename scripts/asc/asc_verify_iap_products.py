#!/usr/bin/env python3
"""Read back App Store Connect IAP/subscription product states for Random Timer.

This is a read-only monetization health check. App-version readiness can pass
while paid products are missing, waiting for review, or unavailable to StoreKit.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from asc.asc_client import ASCClient, AscClientError
else:
    from .asc_client import ASCClient, AscClientError

DEFAULT_BUNDLE_ID = "com.igorganapolsky.randomtimer"
DEFAULT_EXPECTED_PRODUCT_IDS = [
    "com.iganapolsky.randomtimer.pro",
    "com.iganapolsky.randomtimer.pro.monthly",
    "com.iganapolsky.randomtimer.pro.annual",
]
DEFAULT_READY_STATES = {"APPROVED"}


def _items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    data = payload.get("data")
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return [data]
    return []


def _attributes(resource: dict[str, Any]) -> dict[str, Any]:
    attrs = resource.get("attributes")
    return attrs if isinstance(attrs, dict) else {}


def _find_app_id(client: Any, bundle_id: str) -> str:
    payload = client.get(
        "/apps",
        params={
            "filter[bundleId]": bundle_id,
            "fields[apps]": "bundleId,name,sku",
            "limit": 1,
        },
    )
    for app in _items(payload):
        if _attributes(app).get("bundleId") == bundle_id:
            return str(app.get("id") or "")
    raise AscClientError(f"No App Store Connect app found for bundleId={bundle_id}")


def _summarize_iap(resource: dict[str, Any]) -> dict[str, Any]:
    attrs = _attributes(resource)
    return {
        "kind": "in_app_purchase",
        "id": resource.get("id"),
        "product_id": attrs.get("productId"),
        "name": attrs.get("name") or attrs.get("referenceName"),
        "state": attrs.get("state"),
        "type": attrs.get("inAppPurchaseType"),
    }


def _summarize_subscription(resource: dict[str, Any], group: dict[str, Any]) -> dict[str, Any]:
    attrs = _attributes(resource)
    group_attrs = _attributes(group)
    return {
        "kind": "subscription",
        "id": resource.get("id"),
        "product_id": attrs.get("productId"),
        "name": attrs.get("name") or attrs.get("referenceName"),
        "state": attrs.get("state"),
        "subscription_period": attrs.get("subscriptionPeriod"),
        "subscription_group_id": group.get("id"),
        "subscription_group_name": group_attrs.get("referenceName"),
    }


def _list_in_app_purchases(client: Any, app_id: str) -> list[dict[str, Any]]:
    payload = client.get(
        f"/apps/{app_id}/inAppPurchasesV2",
        params={
            "fields[inAppPurchases]": "name,productId,inAppPurchaseType,state",
            "limit": 200,
        },
    )
    return [_summarize_iap(item) for item in _items(payload)]


def _list_subscriptions(client: Any, app_id: str) -> list[dict[str, Any]]:
    groups_payload = client.get(
        f"/apps/{app_id}/subscriptionGroups",
        params={"fields[subscriptionGroups]": "referenceName", "limit": 200},
    )
    subscriptions: list[dict[str, Any]] = []
    for group in _items(groups_payload):
        group_id = group.get("id")
        if not group_id:
            continue
        subs_payload = client.get(
            f"/subscriptionGroups/{group_id}/subscriptions",
            params={
                "fields[subscriptions]": "name,productId,state,subscriptionPeriod",
                "limit": 200,
            },
        )
        subscriptions.extend(
            _summarize_subscription(subscription, group)
            for subscription in _items(subs_payload)
        )
    return subscriptions


def _normalize_states(states: Iterable[str]) -> set[str]:
    return {state.strip().upper() for state in states if state.strip()}


def build_report(
    client: Any,
    *,
    bundle_id: str,
    expected_product_ids: list[str],
    ready_states: set[str] | None = None,
) -> dict[str, Any]:
    ready = ready_states or DEFAULT_READY_STATES
    app_id = _find_app_id(client, bundle_id)
    products = _list_in_app_purchases(client, app_id) + _list_subscriptions(client, app_id)
    by_product_id = {
        str(product.get("product_id")): product
        for product in products
        if product.get("product_id")
    }

    missing = [product_id for product_id in expected_product_ids if product_id not in by_product_id]
    blocked: list[dict[str, Any]] = []
    ready_expected_count = 0
    for product_id in expected_product_ids:
        product = by_product_id.get(product_id)
        if not product:
            continue
        state = str(product.get("state") or "").upper()
        if state in ready:
            ready_expected_count += 1
        else:
            blocked.append(product)

    status = "ready" if not missing and not blocked else "blocked"
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "bundle_id": bundle_id,
        "app_id": app_id,
        "status": status,
        "ready_states": sorted(ready),
        "expected_product_ids": expected_product_ids,
        "products": products,
        "summary": {
            "expected_count": len(expected_product_ids),
            "found_product_count": len(products),
            "ready_expected_count": ready_expected_count,
            "missing_expected_product_ids": missing,
            "blocked_expected_products": blocked,
        },
    }


def _print_report(report: dict[str, Any]) -> None:
    summary = report["summary"]
    print("== ASC IAP Product Readiness ==")
    print(f"bundle_id: {report['bundle_id']}")
    print(f"app_id: {report['app_id']}")
    print(f"status: {report['status']}")
    print(
        "expected: "
        f"{summary['ready_expected_count']}/{summary['expected_count']} ready; "
        f"{len(summary['missing_expected_product_ids'])} missing; "
        f"{len(summary['blocked_expected_products'])} blocked"
    )
    for product in report["products"]:
        print(
            "- "
            f"{product.get('product_id')} [{product.get('kind')}] "
            f"state={product.get('state')} name={product.get('name')}"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle-id", default=DEFAULT_BUNDLE_ID)
    parser.add_argument(
        "--expected-product-id",
        action="append",
        dest="expected_product_ids",
        help="Expected paid product ID. Repeat to override defaults.",
    )
    parser.add_argument("--json-out", help="Write the full report to this path.")
    parser.add_argument(
        "--ready-state",
        action="append",
        dest="ready_states",
        help="Accepted App Store Connect state. Repeat to override APPROVED.",
    )
    args = parser.parse_args(argv)

    expected_product_ids = args.expected_product_ids or DEFAULT_EXPECTED_PRODUCT_IDS
    ready_states = _normalize_states(args.ready_states or DEFAULT_READY_STATES)
    report = build_report(
        ASCClient.from_env(),
        bundle_id=args.bundle_id,
        expected_product_ids=expected_product_ids,
        ready_states=ready_states,
    )
    if args.json_out:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _print_report(report)
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
