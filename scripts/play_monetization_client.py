"""Shared Google Play monetization API helpers for IAP readback scripts."""

from __future__ import annotations

import json
import os
from typing import Any

PACKAGE = "com.iganapolsky.randomtimer"
REQUIRED_ONE_TIME = ("pro_base",)
REQUIRED_SUBSCRIPTIONS = ("elite_tactical", "elite_tactical_monthly")
TARGET_ONE_TIME = "pro_base"
# P2 scaffold — document SKUs; not required for verify until Play Console products exist.
SCAFFOLD_DISCIPLINE_PACKS = (
    "pack_special_forces",
    "pack_boxing_hiit",
    "pack_crossfit",
    "pack_bjj",
)


def resolve_play_credentials() -> str:
    value = (os.environ.get("GOOGLE_PLAY_JSON_KEY") or "").strip()
    if value:
        return value
    path = (os.environ.get("GOOGLE_PLAY_JSON_KEY_PATH") or "").strip()
    if path and os.path.isfile(path):
        return path
    return ""


def build_android_publisher_service(key_value: str):
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


def list_one_time_products(service: Any) -> list[dict[str, Any]]:
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


def list_subscription_products(service: Any) -> list[dict[str, Any]]:
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


def activate_one_time_product(service: Any, product_id: str) -> dict[str, Any]:
    monetization = service.monetization()
    product = (
        monetization.onetimeproducts()
        .get(packageName=PACKAGE, productId=product_id)
        .execute()
    )
    actions: list[dict[str, Any]] = []
    for option in product.get("purchaseOptions") or []:
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
    return {"product_id": product_id, "actions": actions}
