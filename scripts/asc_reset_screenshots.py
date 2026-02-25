#!/usr/bin/env python3
"""Delete existing App Store Connect screenshots for a version localization.

This prevents duplicate/stale screenshots when fastlane deliver appends assets.
"""

from __future__ import annotations

import argparse
from typing import Any, Dict, List

from scripts.asc_client import APP_STORE_CONNECT_API, AscClient, AscClientError
from scripts.asc_verify_ready import (
    _die,
    _get_app_id,
    _get_screenshot_sets,
    _list_app_store_versions,
    _pick_localization,
)


def _api_delete(client: AscClient, path: str) -> None:
    try:
        import requests
    except ImportError:
        _die(2, "❌ Missing requests. Install: pip install requests")

    response = requests.delete(
        f"{APP_STORE_CONNECT_API}{path}",
        headers={
            "Authorization": f"Bearer {client.token_value()}",
            "Content-Type": "application/json",
        },
        timeout=30,
    )
    if response.status_code >= 400:
        _die(
            2,
            "❌ App Store Connect API error\n"
            f"  DELETE {path}\n"
            f"  HTTP {response.status_code}\n"
            f"  Body: {response.text[:2000]}",
        )


def list_screenshot_assets(client: AscClient, localization_id: str) -> List[Dict[str, str]]:
    assets: List[Dict[str, str]] = []
    screenshot_sets = _get_screenshot_sets(client, localization_id)
    for screenshot_set in screenshot_sets:
        set_id = str(screenshot_set.get("id") or "")
        display_type = str((screenshot_set.get("attributes") or {}).get("screenshotDisplayType") or "UNKNOWN")
        payload = client.get(
            f"/appScreenshotSets/{set_id}/appScreenshots",
            params={"limit": "200", "fields[appScreenshots]": "assetDeliveryState,fileName"},
        )
        for shot in payload.get("data", []) or []:
            attrs = shot.get("attributes", {}) or {}
            assets.append(
                {
                    "set_id": set_id,
                    "display_type": display_type,
                    "screenshot_id": str(shot.get("id") or ""),
                    "file_name": str(attrs.get("fileName") or ""),
                    "state": str((attrs.get("assetDeliveryState") or {}).get("state") or "UNKNOWN"),
                }
            )
    return assets


def reset_screenshots(version: str, locale: str, bundle_id: str, dry_run: bool) -> Dict[str, Any]:
    try:
        client = AscClient.from_env(timeout=30)
    except AscClientError as exc:
        _die(2, f"❌ {exc}")
    app_id = _get_app_id(client, bundle_id)
    _, version_obj = _list_app_store_versions(client, app_id, version)
    if not version_obj:
        _die(2, f"❌ No App Store version '{version}' found for bundle id '{bundle_id}'")

    version_localizations = (
        (version_obj.get("relationships", {}) or {})
        .get("appStoreVersionLocalizations", {})
        .get("data", [])
        or []
    )
    if not version_localizations:
        _die(2, f"❌ No localizations found for App Store version '{version}'")

    loc_payload = client.get(
        f"/appStoreVersions/{version_obj['id']}/appStoreVersionLocalizations",
        params={"limit": "200", "fields[appStoreVersionLocalizations]": "locale"},
    )
    loc = _pick_localization(loc_payload.get("data", []) or [], locale)
    if not loc:
        _die(2, f"❌ No localization found for locale '{locale}'")

    localization_id = str(loc["id"])
    assets = list_screenshot_assets(client, localization_id)
    deleted = 0
    for asset in assets:
        shot_id = asset.get("screenshot_id") or ""
        if not shot_id:
            continue
        if not dry_run:
            _api_delete(client, f"/appScreenshots/{shot_id}")
        deleted += 1

    summary = {
        "bundle_id": bundle_id,
        "version": version,
        "locale": locale,
        "localization_id": localization_id,
        "found_assets": len(assets),
        "deleted_assets": deleted,
        "dry_run": dry_run,
    }
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Delete existing ASC screenshots before upload")
    parser.add_argument("--bundle-id", default="com.igorganapolsky.randomtimer")
    parser.add_argument("--version", required=True)
    parser.add_argument("--locale", default="en-US")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    summary = reset_screenshots(
        version=args.version,
        locale=args.locale,
        bundle_id=args.bundle_id,
        dry_run=args.dry_run,
    )
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
