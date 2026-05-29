#!/usr/bin/env python3
"""CLI readback for AdMob setup: hosted app-ads.txt + optional AdMob API app state."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import verify_app_ads_txt as ads_mod

DEFAULT_URL = ads_mod.DEFAULT_URL
EXPECTED_PUBLISHER = ads_mod.EXPECTED_PUBLISHER
PLAY_CONTACT_WEBSITE_APP_ADS_URL = ads_mod.PLAY_CONTACT_WEBSITE_APP_ADS_URL
verify_app_ads_txt = ads_mod.verify_app_ads_txt

ADMOB_API_BASE = "https://admob.googleapis.com/v1"
DEFAULT_ACCOUNT = f"accounts/{EXPECTED_PUBLISHER}"
ANDROID_APP_ID_NUMERIC = "4427145410"


def _fetch_admob_json(path: str, token: str, timeout: int = 30) -> dict:
    url = f"{ADMOB_API_BASE}/{path.lstrip('/')}"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def resolve_access_token(explicit: str | None) -> tuple[str | None, str]:
    if explicit:
        return explicit.strip(), "--access-token"
    env = (os.environ.get("ADMOB_ACCESS_TOKEN") or "").strip()
    if env:
        return env, "ADMOB_ACCESS_TOKEN"
    return None, ""


def list_apps(token: str, account: str) -> list[dict]:
    apps: list[dict] = []
    page_token = ""
    while True:
        query = f"{account}/apps?pageSize=100"
        if page_token:
            query += f"&pageToken={page_token}"
        data = _fetch_admob_json(query, token)
        apps.extend(data.get("apps") or [])
        page_token = data.get("nextPageToken") or ""
        if not page_token:
            break
    return apps


def print_app_ads_report(*, also_play_path: bool) -> int:
    urls = [DEFAULT_URL]
    if also_play_path:
        urls.append(PLAY_CONTACT_WEBSITE_APP_ADS_URL)
    failed = False
    print("## app-ads.txt (hosted)")
    for url in urls:
        ok, msg = verify_app_ads_txt(url=url)
        status = "PASS" if ok else "FAIL"
        print(f"- [{status}] {msg}")
        if not ok:
            failed = True
    return 1 if failed else 0


def print_api_report(token: str, account: str, android_app_id: str) -> int:
    print("## AdMob API (apps)")
    try:
        apps = list_apps(token, account)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"- [FAIL] HTTP {exc.code}: {body[:500]}")
        if exc.code == 403 and "ACCESS_TOKEN_SCOPE_INSUFFICIENT" in body:
            print(
                "  Hint: create OAuth token with scope "
                "https://www.googleapis.com/auth/admob.readonly "
                "(AdMob API has no app-ads.txt verification field; approval state only)."
            )
        return 1

    match = None
    for app in apps:
        app_id = str(app.get("appId") or "")
        if app_id.endswith(android_app_id) or android_app_id in app_id:
            match = app
            break

    print(json.dumps({"account": account, "app_count": len(apps)}, indent=2))
    if not match:
        print(f"- [WARN] No app matching id fragment {android_app_id!r}")
        return 0

    print("- [INFO] Android app:")
    print(json.dumps(match, indent=2))
    print(
        "  Note: app-ads.txt verification is UI/crawler only; "
        "use appApprovalState for ads serving approval."
    )
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="AdMob setup readback (CLI).")
    p.add_argument("--also-check-play-contact-path", action="store_true")
    p.add_argument("--api", action="store_true", help="Call AdMob API (needs OAuth token).")
    p.add_argument("--access-token", default=None)
    p.add_argument("--account", default=DEFAULT_ACCOUNT)
    p.add_argument("--android-app-id", default=ANDROID_APP_ID_NUMERIC)
    p.add_argument("--json", action="store_true", help="Machine-readable summary.")
    args = p.parse_args()

    ads_rc = print_app_ads_report(also_play_path=args.also_check_play_contact_path)
    api_rc = 0
    if args.api:
        token, source = resolve_access_token(args.access_token)
        if not token:
            print(
                "## AdMob API\n"
                "- [SKIP] Set ADMOB_ACCESS_TOKEN or pass --access-token "
                "(scope: https://www.googleapis.com/auth/admob.readonly).",
                file=sys.stderr,
            )
            api_rc = 2
        else:
            if not args.json:
                print(f"(token source: {source})")
            api_rc = print_api_report(token, args.account, args.android_app_id)

    if args.json:
        print(
            json.dumps(
                {
                    "publisher_id": EXPECTED_PUBLISHER,
                    "app_ads_exit_code": ads_rc,
                    "api_exit_code": api_rc,
                }
            )
        )
    return ads_rc or api_rc


if __name__ == "__main__":
    raise SystemExit(main())
