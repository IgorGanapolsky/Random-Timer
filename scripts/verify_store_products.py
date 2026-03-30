#!/usr/bin/env python3
"""Read-only verification for specific App Store Connect and Google Play product IDs."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.asc_client import ASCClient, AscClientError

ANDROID_PACKAGE_DEFAULT = "com.iganapolsky.randomtimer"
ANDROID_PRODUCT_ID_DEFAULT = "elite_tactical"
IOS_BUNDLE_ID_DEFAULT = "com.igorganapolsky.randomtimer"
IOS_PRODUCT_ID_DEFAULT = "com.iganapolsky.randomtimer.elite"


def _resolve_google_play_key() -> str:
    value = (os.environ.get("GOOGLE_PLAY_JSON_KEY") or "").strip()
    if value:
        return value

    value = (os.environ.get("GOOGLE_PLAY_JSON_KEY_PATH") or "").strip()
    if value:
        return value

    fallback = os.path.join(tempfile.gettempdir(), "play-service-account.json")
    if os.path.isfile(fallback):
        return fallback

    return ""


def _load_play_service():
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise RuntimeError(
            "Missing Google Play dependencies. Install: pip install google-api-python-client google-auth"
        ) from exc

    key_value = _resolve_google_play_key()
    if not key_value:
        raise RuntimeError(
            "Missing Google Play key. Set GOOGLE_PLAY_JSON_KEY or GOOGLE_PLAY_JSON_KEY_PATH."
        )

    scopes = ["https://www.googleapis.com/auth/androidpublisher"]
    if os.path.isfile(key_value):
        credentials = service_account.Credentials.from_service_account_file(
            key_value,
            scopes=scopes,
        )
    else:
        credentials = service_account.Credentials.from_service_account_info(
            json.loads(key_value),
            scopes=scopes,
        )

    return build("androidpublisher", "v3", credentials=credentials)


def _google_http_status(exc: Exception) -> int | None:
    return getattr(getattr(exc, "resp", None), "status", None)


def verify_android_subscription(
    package_name: str,
    product_id: str,
) -> tuple[dict[str, Any], list[str]]:
    service = _load_play_service()
    findings: list[str] = []

    try:
        subscription = (
            service.monetization()
            .subscriptions()
            .get(packageName=package_name, productId=product_id)
            .execute()
        )
    except Exception as exc:
        if _google_http_status(exc) == 404:
            return (
                {
                    "found": False,
                    "packageName": package_name,
                    "productId": product_id,
                    "error": f"Google Play subscription '{product_id}' was not found for package '{package_name}'.",
                },
                [f"Android product missing: {product_id}"],
            )
        raise

    base_plans = subscription.get("basePlans", []) or []
    listings = subscription.get("listings", []) or []

    base_plan_summaries: list[dict[str, Any]] = []
    active_base_plan_count = 0
    total_offer_count = 0
    active_offer_count = 0

    for base_plan in base_plans:
        base_plan_id = base_plan.get("basePlanId", "")
        base_plan_state = base_plan.get("state", "UNKNOWN")
        if base_plan_state == "ACTIVE":
            active_base_plan_count += 1

        offers_payload = {"subscriptionOffers": []}
        if base_plan_id:
            try:
                offers_payload = (
                    service.monetization()
                    .subscriptions()
                    .basePlans()
                    .offers()
                    .list(
                        packageName=package_name,
                        productId=product_id,
                        basePlanId=base_plan_id,
                    )
                    .execute()
                )
            except Exception as exc:
                findings.append(
                    f"Android base plan '{base_plan_id}' offer read failed: {exc}"
                )

        offers = offers_payload.get("subscriptionOffers", []) or []
        total_offer_count += len(offers)
        active_offer_count += sum(1 for offer in offers if offer.get("state") == "ACTIVE")

        base_plan_type = "unknown"
        if "autoRenewingBasePlanType" in base_plan:
            base_plan_type = "autoRenewing"
        elif "prepaidBasePlanType" in base_plan:
            base_plan_type = "prepaid"
        elif "installmentsBasePlanType" in base_plan:
            base_plan_type = "installments"

        base_plan_summaries.append(
            {
                "basePlanId": base_plan_id,
                "state": base_plan_state,
                "type": base_plan_type,
                "offerCount": len(offers),
                "activeOfferCount": sum(
                    1 for offer in offers if offer.get("state") == "ACTIVE"
                ),
            }
        )

    listing_languages = sorted(
        {
            listing.get("languageCode", "")
            for listing in listings
            if listing.get("languageCode")
        }
    )

    if not base_plans:
        findings.append("Android subscription exists but has no base plans configured.")
    if active_base_plan_count == 0:
        findings.append("Android subscription exists but has no ACTIVE base plan.")
    if not listings:
        findings.append("Android subscription exists but has no localized listings.")

    return (
        {
            "found": True,
            "packageName": subscription.get("packageName", package_name),
            "productId": subscription.get("productId", product_id),
            "basePlanCount": len(base_plans),
            "activeBasePlanCount": active_base_plan_count,
            "offerCount": total_offer_count,
            "activeOfferCount": active_offer_count,
            "listingLanguages": listing_languages,
            "basePlans": base_plan_summaries,
        },
        findings,
    )


def _asc_find_app(client: ASCClient, bundle_id: str) -> dict[str, Any]:
    payload = client.get(
        "/apps",
        params={
            "filter[bundleId]": bundle_id,
            "limit": 1,
            "fields[apps]": "name,bundleId,sku",
        },
    )
    apps = payload.get("data", [])
    if not apps:
        raise AscClientError(f"No App Store Connect app found for bundleId '{bundle_id}'.")
    return apps[0]


def _asc_find_matching_in_app_purchase(
    client: ASCClient,
    app_id: str,
    product_id: str,
) -> dict[str, Any] | None:
    in_app_purchases = client.get_all(
        f"/apps/{app_id}/inAppPurchasesV2",
        params={
            "limit": 200,
            "fields[inAppPurchasesV2]": "name,productId,state,inAppPurchaseType",
        },
    )
    for purchase in in_app_purchases:
        attributes = purchase.get("attributes", {})
        if attributes.get("productId") == product_id:
            return purchase
    return None


def _asc_find_matching_subscription(
    client: ASCClient,
    app_id: str,
    product_id: str,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    subscription_groups = client.get_all(
        f"/apps/{app_id}/subscriptionGroups",
        params={
            "limit": 200,
            "fields[subscriptionGroups]": "referenceName",
        },
    )

    for group in subscription_groups:
        group_id = group.get("id", "")
        subscriptions = client.get_all(
            f"/subscriptionGroups/{group_id}/subscriptions",
            params={
                "limit": 200,
                "fields[subscriptions]": "name,productId,state,subscriptionPeriod,groupLevel,familySharable",
            },
        )
        for subscription in subscriptions:
            attributes = subscription.get("attributes", {})
            if attributes.get("productId") == product_id:
                return subscription, group
    return None, None


def _asc_relationship_ids(resource: dict[str, Any], relationship_name: str) -> list[str]:
    relationship = resource.get("relationships", {}).get(relationship_name, {})
    linkage = relationship.get("data")
    if isinstance(linkage, list):
        return [item.get("id", "") for item in linkage if item.get("id")]
    if isinstance(linkage, dict):
        resource_id = linkage.get("id", "")
        return [resource_id] if resource_id else []
    return []


def _asc_subscription_metadata_details(
    client: ASCClient,
    subscription_id: str,
) -> dict[str, Any]:
    payload = client.get(
        f"/subscriptions/{subscription_id}",
        params={
            "include": "subscriptionLocalizations,appStoreReviewScreenshot,prices,subscriptionAvailability",
            "fields[subscriptions]": (
                "name,productId,familySharable,state,subscriptionPeriod,reviewNote,"
                "groupLevel,subscriptionLocalizations,appStoreReviewScreenshot,"
                "prices,subscriptionAvailability"
            ),
            "fields[subscriptionLocalizations]": "name,locale,description,state",
            "limit[subscriptionLocalizations]": 50,
            "limit[prices]": 50,
        },
    )

    subscription = payload.get("data", {})
    included = payload.get("included", []) or []
    if not subscription:
        return {}

    included_by_id = {
        item.get("id", ""): item
        for item in included
        if item.get("id")
    }

    localization_ids = _asc_relationship_ids(subscription, "subscriptionLocalizations")
    price_ids = _asc_relationship_ids(subscription, "prices")
    availability_ids = _asc_relationship_ids(subscription, "subscriptionAvailability")
    review_screenshot_ids = _asc_relationship_ids(subscription, "appStoreReviewScreenshot")

    localizations = [
        included_by_id[item_id]
        for item_id in localization_ids
        if item_id in included_by_id
    ]
    prices = [
        included_by_id[item_id]
        for item_id in price_ids
        if item_id in included_by_id
    ]
    availabilities = [
        included_by_id[item_id]
        for item_id in availability_ids
        if item_id in included_by_id
    ]
    review_screenshots = [
        included_by_id[item_id]
        for item_id in review_screenshot_ids
        if item_id in included_by_id
    ]

    return {
        "reviewNotePresent": bool(subscription.get("attributes", {}).get("reviewNote")),
        "localizations": [
            {
                "id": item.get("id"),
                "locale": item.get("attributes", {}).get("locale"),
                "name": item.get("attributes", {}).get("name"),
                "state": item.get("attributes", {}).get("state"),
                "hasDescription": bool(item.get("attributes", {}).get("description")),
            }
            for item in localizations
        ],
        "prices": [
            {
                "id": item.get("id"),
                "startDate": item.get("attributes", {}).get("startDate"),
                "preserved": item.get("attributes", {}).get("preserved"),
                "current": item.get("attributes", {}).get("current"),
            }
            for item in prices
        ],
        "availability": [
            {
                "id": item.get("id"),
                "availableInNewTerritories": item.get("attributes", {}).get(
                    "availableInNewTerritories"
                ),
            }
            for item in availabilities
        ],
        "reviewScreenshots": [
            {
                "id": item.get("id"),
                "fileName": item.get("attributes", {}).get("fileName"),
                "fileSize": item.get("attributes", {}).get("fileSize"),
                "assetDeliveryState": item.get("attributes", {}).get(
                    "assetDeliveryState"
                ),
            }
            for item in review_screenshots
        ],
    }


def verify_ios_product(bundle_id: str, product_id: str) -> tuple[dict[str, Any], list[str]]:
    client = ASCClient.from_env()
    app = _asc_find_app(client, bundle_id)
    app_id = app.get("id", "")
    app_attributes = app.get("attributes", {})

    subscription, subscription_group = _asc_find_matching_subscription(
        client,
        app_id,
        product_id,
    )
    findings: list[str] = []

    if subscription is not None:
        attributes = subscription.get("attributes", {})
        state = attributes.get("state", "UNKNOWN")
        metadata_details = (
            _asc_subscription_metadata_details(
                client,
                subscription.get("id", ""),
            )
            if subscription_group is not None
            else {}
        )
        if state in {"MISSING_METADATA", "READY_TO_SUBMIT", "DEVELOPER_ACTION_NEEDED", "REJECTED"}:
            findings.append(f"iOS subscription exists but is not sale-ready (state={state}).")

        return (
            {
                "found": True,
                "bundleId": bundle_id,
                "appId": app_id,
                "appName": app_attributes.get("name"),
                "productId": attributes.get("productId", product_id),
                "resourceType": "subscription",
                "resourceId": subscription.get("id"),
                "state": state,
                "name": attributes.get("name"),
                "subscriptionPeriod": attributes.get("subscriptionPeriod"),
                "groupLevel": attributes.get("groupLevel"),
                "familySharable": attributes.get("familySharable"),
                "subscriptionGroupId": subscription_group.get("id") if subscription_group else None,
                "subscriptionGroupReferenceName": (
                    subscription_group.get("attributes", {}).get("referenceName")
                    if subscription_group
                    else None
                ),
                "reviewNotePresent": metadata_details.get("reviewNotePresent"),
                "localizations": metadata_details.get("localizations", []),
                "priceCount": len(metadata_details.get("prices", [])),
                "availabilityCount": len(metadata_details.get("availability", [])),
                "reviewScreenshotCount": len(metadata_details.get("reviewScreenshots", [])),
                "prices": metadata_details.get("prices", []),
                "availability": metadata_details.get("availability", []),
                "reviewScreenshots": metadata_details.get("reviewScreenshots", []),
            },
            findings,
        )

    in_app_purchase = _asc_find_matching_in_app_purchase(client, app_id, product_id)
    if in_app_purchase is None:
        return (
            {
                "found": False,
                "bundleId": bundle_id,
                "appId": app_id,
                "appName": app_attributes.get("name"),
                "productId": product_id,
                "error": f"App Store Connect product '{product_id}' was not found for bundleId '{bundle_id}'.",
            },
            [f"iOS product missing: {product_id}"],
        )

    attributes = in_app_purchase.get("attributes", {})
    state = attributes.get("state", "UNKNOWN")
    if state in {"MISSING_METADATA", "READY_TO_SUBMIT", "DEVELOPER_ACTION_NEEDED", "REJECTED"}:
        findings.append(f"iOS in-app purchase exists but is not sale-ready (state={state}).")

    return (
        {
            "found": True,
            "bundleId": bundle_id,
            "appId": app_id,
            "appName": app_attributes.get("name"),
            "productId": attributes.get("productId", product_id),
            "resourceType": "inAppPurchaseV2",
            "resourceId": in_app_purchase.get("id"),
            "state": state,
            "name": attributes.get("name"),
            "inAppPurchaseType": attributes.get("inAppPurchaseType"),
        },
        findings,
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify that exact App Store Connect and Google Play product IDs exist and are configured."
    )
    parser.add_argument(
        "--platform",
        choices=["android", "ios", "both"],
        default="both",
        help="Which store(s) to verify.",
    )
    parser.add_argument(
        "--android-package",
        default=ANDROID_PACKAGE_DEFAULT,
        help=f"Android package name (default: {ANDROID_PACKAGE_DEFAULT})",
    )
    parser.add_argument(
        "--android-product-id",
        default=ANDROID_PRODUCT_ID_DEFAULT,
        help=f"Android product ID (default: {ANDROID_PRODUCT_ID_DEFAULT})",
    )
    parser.add_argument(
        "--ios-bundle-id",
        default=IOS_BUNDLE_ID_DEFAULT,
        help=f"iOS bundle ID (default: {IOS_BUNDLE_ID_DEFAULT})",
    )
    parser.add_argument(
        "--ios-product-id",
        default=IOS_PRODUCT_ID_DEFAULT,
        help=f"iOS product ID (default: {IOS_PRODUCT_ID_DEFAULT})",
    )
    parser.add_argument(
        "--output",
        default="",
        help="Optional path to write JSON results.",
    )
    return parser.parse_args()


def _print_section(title: str) -> None:
    print()
    print(title)
    print("-" * len(title))


def _print_json(data: dict[str, Any]) -> None:
    print(json.dumps(data, indent=2, sort_keys=True))


def main() -> int:
    args = _parse_args()

    results: dict[str, Any] = {}
    failures: list[str] = []

    try:
        if args.platform in {"android", "both"}:
            android_result, android_findings = verify_android_subscription(
                args.android_package,
                args.android_product_id,
            )
            results["android"] = android_result
            failures.extend(android_findings)

        if args.platform in {"ios", "both"}:
            ios_result, ios_findings = verify_ios_product(
                args.ios_bundle_id,
                args.ios_product_id,
            )
            results["ios"] = ios_result
            failures.extend(ios_findings)
    except (AscClientError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"❌ Verification failed: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"❌ Unexpected verification failure: {exc}", file=sys.stderr)
        return 2

    _print_section("Store Product Verification")
    _print_json(results)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            json.dump(results, handle, indent=2, sort_keys=True)
            handle.write("\n")
        print()
        print(f"Wrote JSON report to {args.output}")

    print()
    if failures:
        print("Result: FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Result: ALL PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
