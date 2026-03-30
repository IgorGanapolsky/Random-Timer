#!/usr/bin/env python3
"""Repair App Store Connect metadata for the iOS subscription product.

This script fills the specific App Store review metadata currently missing for
the Random Tactical Timer subscription:
  - subscription reviewNote
  - subscription App Review screenshot

It uses the App Store Connect API directly and writes a JSON evidence report.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
from typing import Any

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.asc_client import ASCClient, AscClientError
from scripts.verify_store_products import (
    IOS_BUNDLE_ID_DEFAULT,
    IOS_PRODUCT_ID_DEFAULT,
    _asc_find_app,
    _asc_find_matching_subscription,
)

DEFAULT_REVIEW_NOTE = (
    "Auto-renewable annual subscription unlocks Pro Tactical features including "
    "voice callouts, extended timer range, and advanced round controls. "
    "To test, open Random Tactical Timer, tap Upgrade to Pro, select the annual plan, "
    "and complete the sandbox purchase flow. No account, demo login, or special hardware is required."
)
DEFAULT_SCREENSHOT_PATH = (
    REPO_ROOT / "native-ios" / "fastlane" / "screenshots" / "en-US" / "3_pro.png"
)
DEFAULT_OUTPUT_PATH = REPO_ROOT / "ios-subscription-metadata-fix.json"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def _md5_hexdigest(data: bytes) -> str:
    return hashlib.md5(data, usedforsecurity=False).hexdigest()


def _build_review_note_payload(subscription_id: str, review_note: str) -> dict[str, Any]:
    return {
        "data": {
            "id": subscription_id,
            "type": "subscriptions",
            "attributes": {"reviewNote": review_note},
        }
    }


def _build_review_screenshot_create_payload(
    subscription_id: str,
    *,
    file_name: str,
    file_size: int,
) -> dict[str, Any]:
    return {
        "data": {
            "type": "subscriptionAppStoreReviewScreenshots",
            "attributes": {
                "fileName": file_name,
                "fileSize": file_size,
            },
            "relationships": {
                "subscription": {
                    "data": {
                        "id": subscription_id,
                        "type": "subscriptions",
                    }
                }
            },
        }
    }


def _build_review_screenshot_commit_payload(
    screenshot_id: str,
    *,
    checksum_md5: str,
) -> dict[str, Any]:
    return {
        "data": {
            "id": screenshot_id,
            "type": "subscriptionAppStoreReviewScreenshots",
            "attributes": {
                "uploaded": True,
                "sourceFileChecksum": checksum_md5,
            },
        }
    }


def _headers_dict(request_headers: list[dict[str, Any]] | None) -> dict[str, str]:
    headers: dict[str, str] = {}
    for item in request_headers or []:
        name = str(item.get("name") or "").strip()
        value = str(item.get("value") or "").strip()
        if name:
            headers[name] = value
    return headers


def _slice_bytes(data: bytes, *, offset: int, length: int) -> bytes:
    if offset < 0 or length < 0:
        raise ValueError("Upload operations require non-negative offset and length.")
    return data[offset : offset + length]


def _json_dump(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _find_subscription(client: ASCClient, bundle_id: str, product_id: str) -> tuple[str, dict[str, Any]]:
    app = _asc_find_app(client, bundle_id)
    subscription, _group = _asc_find_matching_subscription(client, app.get("id", ""), product_id)
    if subscription is None:
        raise AscClientError(
            f"No iOS subscription found for bundleId '{bundle_id}' and productId '{product_id}'."
        )
    return str(subscription.get("id") or ""), subscription


def _get_subscription(client: ASCClient, subscription_id: str) -> dict[str, Any]:
    payload = client.get(
        f"/subscriptions/{subscription_id}",
        params={
            "fields[subscriptions]": (
                "name,productId,state,reviewNote,subscriptionPeriod,groupLevel,familySharable"
            )
        },
    )
    data = payload.get("data")
    return data if isinstance(data, dict) else {}


def _patch_review_note(client: ASCClient, subscription_id: str, review_note: str) -> dict[str, Any]:
    return client.request(
        "PATCH",
        f"/subscriptions/{subscription_id}",
        payload=_build_review_note_payload(subscription_id, review_note),
    )


def _get_review_screenshot_for_subscription(
    client: ASCClient,
    subscription_id: str,
) -> dict[str, Any] | None:
    payload = client.get(f"/subscriptions/{subscription_id}/appStoreReviewScreenshot")
    data = payload.get("data")
    return data if isinstance(data, dict) else None


def _get_review_screenshot(
    client: ASCClient,
    screenshot_id: str,
) -> dict[str, Any]:
    payload = client.get(
        f"/subscriptionAppStoreReviewScreenshots/{screenshot_id}",
        params={
            "fields[subscriptionAppStoreReviewScreenshots]": (
                "assetDeliveryState,assetToken,assetType,fileName,fileSize,imageAsset,"
                "sourceFileChecksum,uploadOperations"
            )
        },
    )
    data = payload.get("data")
    return data if isinstance(data, dict) else {}


def _create_review_screenshot(
    client: ASCClient,
    subscription_id: str,
    *,
    file_name: str,
    file_size: int,
) -> dict[str, Any]:
    payload = client.request(
        "POST",
        "/subscriptionAppStoreReviewScreenshots",
        payload=_build_review_screenshot_create_payload(
            subscription_id,
            file_name=file_name,
            file_size=file_size,
        ),
    )
    data = payload.get("data")
    if not isinstance(data, dict):
        raise AscClientError("Create review screenshot returned no resource data.")
    return data


def _upload_review_screenshot(data: bytes, upload_operations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    if not upload_operations:
        raise AscClientError("Create review screenshot returned no upload operations.")

    for op in upload_operations:
        method = str(op.get("method") or "PUT").upper()
        url = str(op.get("url") or "").strip()
        offset = int(op.get("offset") or 0)
        length = int(op.get("length") or 0)
        headers = _headers_dict(op.get("requestHeaders"))
        chunk = _slice_bytes(data, offset=offset, length=length or len(data))

        response = requests.request(
            method,
            url,
            headers=headers,
            data=chunk,
            timeout=300,
        )
        if response.status_code >= 400:
            raise AscClientError(
                f"Upload operation failed: HTTP {response.status_code} body={response.text[:1000]!r}"
            )

        evidence.append(
            {
                "method": method,
                "offset": offset,
                "length": len(chunk),
                "statusCode": response.status_code,
                "urlHost": requests.utils.urlparse(url).netloc,
            }
        )

    return evidence


def _commit_review_screenshot(
    client: ASCClient,
    screenshot_id: str,
    *,
    checksum_md5: str,
) -> dict[str, Any]:
    return client.request(
        "PATCH",
        f"/subscriptionAppStoreReviewScreenshots/{screenshot_id}",
        payload=_build_review_screenshot_commit_payload(
            screenshot_id,
            checksum_md5=checksum_md5,
        ),
    )


def _state_errors(state: dict[str, Any] | None) -> list[dict[str, Any]]:
    errors = []
    for item in (state or {}).get("errors", []) or []:
        if isinstance(item, dict):
            errors.append(
                {
                    "code": item.get("code"),
                    "description": item.get("description"),
                }
            )
    return errors


def _state_warnings(state: dict[str, Any] | None) -> list[dict[str, Any]]:
    warnings = []
    for item in (state or {}).get("warnings", []) or []:
        if isinstance(item, dict):
            warnings.append(
                {
                    "code": item.get("code"),
                    "description": item.get("description"),
                }
            )
    return warnings


def _wait_for_review_screenshot(
    client: ASCClient,
    screenshot_id: str,
    *,
    timeout_seconds: int,
    poll_seconds: int,
) -> dict[str, Any]:
    deadline = time.time() + timeout_seconds
    history: list[dict[str, Any]] = []

    while True:
        resource = _get_review_screenshot(client, screenshot_id)
        attrs = resource.get("attributes", {}) or {}
        asset_state = attrs.get("assetDeliveryState", {}) or {}
        state = str(asset_state.get("state") or "UNKNOWN")
        history.append(
            {
                "observedAt": int(time.time()),
                "state": state,
                "errors": _state_errors(asset_state),
                "warnings": _state_warnings(asset_state),
            }
        )

        if state in {"COMPLETE", "FAILED"}:
            return {
                "resource": resource,
                "history": history,
            }

        if time.time() >= deadline:
            raise AscClientError(
                f"Timed out waiting for review screenshot '{screenshot_id}' to finish processing."
            )

        time.sleep(poll_seconds)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Repair the iOS subscription metadata required by App Store Connect."
    )
    parser.add_argument(
        "--ios-bundle-id",
        default=IOS_BUNDLE_ID_DEFAULT,
        help=f"Bundle identifier to inspect (default: {IOS_BUNDLE_ID_DEFAULT})",
    )
    parser.add_argument(
        "--ios-product-id",
        default=IOS_PRODUCT_ID_DEFAULT,
        help=f"Subscription product identifier (default: {IOS_PRODUCT_ID_DEFAULT})",
    )
    parser.add_argument(
        "--subscription-id",
        default="",
        help="Optional explicit subscription resource ID. If omitted, the script finds it by product ID.",
    )
    parser.add_argument(
        "--review-note",
        default=DEFAULT_REVIEW_NOTE,
        help="Review note text to apply to the subscription.",
    )
    parser.add_argument(
        "--review-note-file",
        default="",
        help="Optional text file whose contents replace --review-note.",
    )
    parser.add_argument(
        "--screenshot",
        default=str(DEFAULT_SCREENSHOT_PATH),
        help=f"PNG screenshot path to upload (default: {DEFAULT_SCREENSHOT_PATH})",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=300,
        help="How long to wait for screenshot processing to finish (default: 300).",
    )
    parser.add_argument(
        "--poll-seconds",
        type=int,
        default=10,
        help="Polling interval when waiting for screenshot processing (default: 10).",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help=f"Where to write the JSON evidence report (default: {DEFAULT_OUTPUT_PATH})",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    screenshot_path = Path(args.screenshot).expanduser().resolve()
    if not screenshot_path.is_file():
        raise SystemExit(f"Screenshot file not found: {screenshot_path}")
    screenshot_bytes = screenshot_path.read_bytes()
    screenshot_md5 = _md5_hexdigest(screenshot_bytes)

    review_note = args.review_note
    if args.review_note_file:
        review_note = _read_text(Path(args.review_note_file).expanduser().resolve())
    if not review_note:
        raise SystemExit("Review note must be non-empty.")

    client = ASCClient.from_env(timeout=max(args.timeout_seconds, 30))

    subscription_id = args.subscription_id.strip()
    original_subscription = {}
    if subscription_id:
        original_subscription = _get_subscription(client, subscription_id)
    else:
        subscription_id, original_subscription = _find_subscription(
            client,
            args.ios_bundle_id,
            args.ios_product_id,
        )

    evidence: dict[str, Any] = {
        "bundleId": args.ios_bundle_id,
        "productId": args.ios_product_id,
        "subscriptionId": subscription_id,
        "generatedAtUnix": int(time.time()),
        "input": {
            "reviewNoteLength": len(review_note),
            "reviewNoteSource": (
                str(Path(args.review_note_file).expanduser().resolve())
                if args.review_note_file
                else "inline"
            ),
            "screenshotPath": str(screenshot_path),
            "screenshotFileName": screenshot_path.name,
            "screenshotFileSize": len(screenshot_bytes),
            "screenshotMd5": screenshot_md5,
        },
        "subscriptionBefore": {
            "id": original_subscription.get("id"),
            "attributes": original_subscription.get("attributes", {}),
        },
    }

    patched_subscription = _patch_review_note(client, subscription_id, review_note)
    patched_subscription_data = patched_subscription.get("data") or {}
    evidence["reviewNotePatch"] = {
        "success": True,
        "subscriptionId": patched_subscription_data.get("id"),
        "reviewNotePresent": bool(
            (patched_subscription_data.get("attributes") or {}).get("reviewNote")
        ),
    }

    review_screenshot = _get_review_screenshot_for_subscription(client, subscription_id)
    created = False
    if review_screenshot is None:
        review_screenshot = _create_review_screenshot(
            client,
            subscription_id,
            file_name=screenshot_path.name,
            file_size=len(screenshot_bytes),
        )
        created = True

    review_screenshot_id = str(review_screenshot.get("id") or "")
    if not review_screenshot_id:
        raise SystemExit("App Store Connect returned a review screenshot without an ID.")
    review_screenshot = _get_review_screenshot(client, review_screenshot_id)
    review_screenshot_attrs = review_screenshot.get("attributes", {}) or {}
    upload_operations = review_screenshot_attrs.get("uploadOperations") or []
    current_state = (review_screenshot_attrs.get("assetDeliveryState") or {}).get("state")
    upload_evidence: list[dict[str, Any]] = []
    commit_response: dict[str, Any] | None = None

    if current_state != "COMPLETE":
        upload_evidence = _upload_review_screenshot(screenshot_bytes, upload_operations)
        commit_response = _commit_review_screenshot(
            client,
            review_screenshot_id,
            checksum_md5=screenshot_md5,
        )

    waited = _wait_for_review_screenshot(
        client,
        review_screenshot_id,
        timeout_seconds=args.timeout_seconds,
        poll_seconds=args.poll_seconds,
    )
    final_resource = waited["resource"]
    final_attrs = final_resource.get("attributes", {}) or {}
    final_state = (final_attrs.get("assetDeliveryState") or {}).get("state")

    evidence["reviewScreenshot"] = {
        "created": created,
        "id": review_screenshot_id,
        "stateBeforeUpload": current_state,
        "uploadOperationCount": len(upload_operations),
        "uploadOperations": upload_evidence,
        "commitResponse": commit_response,
        "finalResource": final_resource,
        "finalState": final_state,
        "processingHistory": waited["history"],
    }

    refreshed_subscription = _get_subscription(client, subscription_id)
    evidence["subscriptionAfter"] = {
        "id": refreshed_subscription.get("id"),
        "attributes": refreshed_subscription.get("attributes", {}),
    }

    output_path = Path(args.output).expanduser().resolve()
    _json_dump(output_path, evidence)
    print(json.dumps(evidence, indent=2, sort_keys=True))

    if final_state != "COMPLETE":
        raise SystemExit(
            f"Review screenshot processing did not complete successfully (state={final_state})."
        )

    if not (refreshed_subscription.get("attributes", {}) or {}).get("reviewNote"):
        raise SystemExit("Review note is still empty after PATCH.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
