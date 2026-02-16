#!/usr/bin/env python3
"""Fail-fast store API credential and permission checks.

This script verifies that configured credentials can access:
- Google Play Developer API for the Android package
- App Store Connect API for the iOS bundle ID

It is intentionally read-only/safe:
- Android: creates a temporary edit and immediately deletes it
- iOS: performs app lookup by bundle ID

Exit codes:
    0 - All requested checks passed
    1 - Check failed (permission/config/API error)
    2 - Invalid invocation or missing required configuration
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
from typing import Any, Dict, List, Optional, Tuple

ANDROID_PACKAGE_DEFAULT = "com.iganapolsky.randomtimer"
IOS_BUNDLE_ID_DEFAULT = "com.igorganapolsky.randomtimer"
APP_STORE_CONNECT_API = "https://api.appstoreconnect.apple.com/v1"


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


def _read_service_account_email(key_value: str) -> Optional[str]:
    try:
        if os.path.isfile(key_value):
            with open(key_value, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = json.loads(key_value)
        email = data.get("client_email")
        return str(email) if email else None
    except Exception:
        return None


def check_android_access(package_name: str) -> Tuple[bool, str]:
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
    except ImportError:
        return (
            False,
            "Missing dependencies. Install: pip install google-api-python-client google-auth",
        )

    key_value = _resolve_google_play_key()
    if not key_value:
        return (
            False,
            "Missing Google Play key. Set GOOGLE_PLAY_JSON_KEY or GOOGLE_PLAY_JSON_KEY_PATH.",
        )

    scopes = ["https://www.googleapis.com/auth/androidpublisher"]
    service_account_email = _read_service_account_email(key_value)

    try:
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

        service = build("androidpublisher", "v3", credentials=credentials)
        edits = service.edits()
        edit = edits.insert(body={}, packageName=package_name).execute()
        edit_id = edit["id"]
        edits.delete(packageName=package_name, editId=edit_id).execute()

        return (
            True,
            f"Google Play API access OK for package '{package_name}'"
            + (f" via '{service_account_email}'" if service_account_email else ""),
        )
    except Exception as exc:
        details = f"Google Play API access failed: {exc}"
        if "403" in str(exc) and service_account_email:
            details += (
                f"\n  Service account: {service_account_email}\n"
                "  Fix: Grant this account access in Play Console > Users and permissions,"
                " and confirm API access is linked for this app."
            )
        return (False, details)


def _read_appstore_key_material(key_id: str) -> str:
    private_key = (os.environ.get("APPSTORE_PRIVATE_KEY") or "").strip()
    if not private_key:
        private_key = (os.environ.get("APPSTORE_PRIVATE_KEY_PATH") or "").strip()
    if not private_key:
        default_path = os.path.expanduser(
            f"~/.appstoreconnect/private_keys/AuthKey_{key_id}.p8"
        )
        if os.path.isfile(default_path):
            private_key = default_path
    if not private_key:
        return ""
    expanded_path = os.path.expanduser(private_key)
    if os.path.isfile(expanded_path):
        with open(expanded_path, "r", encoding="utf-8") as f:
            return f.read()
    return private_key


def _build_asc_jwt() -> Tuple[Optional[str], str]:
    try:
        import jwt
    except ImportError:
        return (None, "Missing dependencies. Install: pip install pyjwt cryptography")

    key_id = (os.environ.get("APPSTORE_KEY_ID") or "").strip()
    issuer_id = (os.environ.get("APPSTORE_ISSUER_ID") or "").strip()
    private_key = _read_appstore_key_material(key_id)

    missing: List[str] = []
    if not key_id:
        missing.append("APPSTORE_KEY_ID")
    if not issuer_id:
        missing.append("APPSTORE_ISSUER_ID")
    if not private_key:
        missing.append("APPSTORE_PRIVATE_KEY (or APPSTORE_PRIVATE_KEY_PATH)")
    if missing:
        return (None, f"Missing App Store credentials: {', '.join(missing)}")

    now = int(time.time())
    payload = {
        "iss": issuer_id,
        "iat": now,
        "exp": now + 1200,
        "aud": "appstoreconnect-v1",
    }
    headers = {"alg": "ES256", "kid": key_id, "typ": "JWT"}
    token = jwt.encode(payload, private_key, algorithm="ES256", headers=headers)
    return (token, "")


def check_ios_access(bundle_id: str) -> Tuple[bool, str]:
    try:
        import requests
    except ImportError:
        return (False, "Missing dependency. Install: pip install requests")

    token, err = _build_asc_jwt()
    if not token:
        return (False, err)

    try:
        resp = requests.get(
            f"{APP_STORE_CONNECT_API}/apps",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            params={
                "filter[bundleId]": bundle_id,
                "limit": 1,
            },
            timeout=30,
        )
        resp.raise_for_status()
        payload: Dict[str, Any] = resp.json()
        apps = payload.get("data", [])
        if not apps:
            return (
                False,
                f"App Store Connect access OK, but no app found for bundleId '{bundle_id}'",
            )

        app = apps[0]
        app_id = app.get("id", "?")
        name = app.get("attributes", {}).get("name", "?")
        return (True, f"App Store Connect API access OK for '{name}' (id={app_id})")
    except Exception as exc:
        return (False, f"App Store Connect API access failed: {exc}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify store API access and permissions.")
    parser.add_argument(
        "--platform",
        choices=["android", "ios", "both"],
        required=True,
        help="Which store(s) to verify.",
    )
    parser.add_argument(
        "--android-package",
        default=ANDROID_PACKAGE_DEFAULT,
        help=f"Android package name (default: {ANDROID_PACKAGE_DEFAULT})",
    )
    parser.add_argument(
        "--ios-bundle-id",
        default=IOS_BUNDLE_ID_DEFAULT,
        help=f"iOS bundle ID (default: {IOS_BUNDLE_ID_DEFAULT})",
    )
    return parser.parse_args()


def _print_results(results: List[Dict[str, str]]) -> bool:
    print()
    print("══ Store API Access Check ═══════════════════════════")
    all_passed = True
    for item in results:
        icon = "✅" if item["passed"] == "true" else "❌"
        if item["passed"] != "true":
            all_passed = False
        print(f"{item['platform']:<8} {icon} {item['summary']}")
    print("══════════════════════════════════════════════════════")
    print(f"Result: {'ALL PASSED' if all_passed else 'FAILED'}")
    print()
    return all_passed


def main() -> int:
    args = _parse_args()
    results: List[Dict[str, str]] = []

    if args.platform in ("android", "both"):
        ok, summary = check_android_access(args.android_package)
        results.append(
            {
                "platform": "Android",
                "passed": "true" if ok else "false",
                "summary": summary,
            }
        )

    if args.platform in ("ios", "both"):
        ok, summary = check_ios_access(args.ios_bundle_id)
        results.append(
            {
                "platform": "iOS",
                "passed": "true" if ok else "false",
                "summary": summary,
            }
        )

    if not results:
        print("No checks executed.")
        return 2

    all_passed = _print_results(results)
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
