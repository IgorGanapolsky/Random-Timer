#!/usr/bin/env python3
"""Write marketing/data/admob_status.json — GSD telemetry for AdMob P1 hosting + API."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import admob_api_auth as auth_mod
import admob_status as status_mod
import verify_app_ads_txt as ads_mod

verify_app_ads_txt = ads_mod.verify_app_ads_txt


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _app_ads_urls(*, also_play_path: bool) -> list[str]:
    urls = [ads_mod.DEFAULT_URL]
    if also_play_path:
        urls.extend(
            [
                ads_mod.ADMOB_CRAWLER_ROOT_APP_ADS_URL,
                ads_mod.PLAY_CONTACT_WEBSITE_APP_ADS_URL,
            ]
        )
    return urls


def build_snapshot(
    *,
    also_play_path: bool,
    include_api: bool,
    access_token: str | None,
) -> dict:
    checks: list[dict] = []
    for url in _app_ads_urls(also_play_path=also_play_path):
        ok, msg = verify_app_ads_txt(url=url)
        checks.append({"url": url, "ok": ok, "message": msg})

    payload: dict = {
        "source": "admob_metrics_snapshot",
        "generated_at": _utc_now(),
        "publisher_id": ads_mod.EXPECTED_PUBLISHER,
        "app_ads": {
            "expected_line": ads_mod.EXPECTED_LINE,
            "checks": checks,
            "all_pass": all(c["ok"] for c in checks),
        },
        "api": None,
    }

    if include_api:
        auth = auth_mod.resolve_admob_auth(access_token)
        if not auth:
            payload["api"] = {"skipped": True, "reason": "no_credentials"}
        else:
            try:
                apps = status_mod.list_apps(auth, status_mod.DEFAULT_ACCOUNT)
                payload["api"] = {
                    "skipped": False,
                    "token_source": auth.source,
                    "quota_project": auth.quota_project,
                    "account": status_mod.DEFAULT_ACCOUNT,
                    "app_count": len(apps),
                    "apps": [
                        {
                            "platform": app.get("platform"),
                            "appId": app.get("appId"),
                            "appApprovalState": app.get("appApprovalState"),
                            "displayName": (app.get("linkedAppInfo") or {}).get("displayName")
                            or (app.get("manualAppInfo") or {}).get("displayName"),
                        }
                        for app in apps
                    ],
                }
            except Exception as exc:  # noqa: BLE001 — snapshot must always write
                payload["api"] = {"skipped": False, "error": str(exc)[:500]}

    return payload


def write_snapshot(repo_root: Path, payload: dict) -> Path:
    out_path = repo_root / "marketing" / "data" / "admob_status.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return out_path


def main() -> int:
    p = argparse.ArgumentParser(description="Write marketing/data/admob_status.json")
    p.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument("--also-check-play-contact-path", action="store_true")
    p.add_argument("--api", action="store_true", help="Include AdMob API apps when creds exist.")
    p.add_argument("--access-token", default=None)
    args = p.parse_args()

    payload = build_snapshot(
        also_play_path=args.also_check_play_contact_path,
        include_api=args.api,
        access_token=args.access_token,
    )
    out_path = write_snapshot(args.repo_root.resolve(), payload)
    print(f"Wrote {out_path}")
    return 0 if payload["app_ads"]["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
