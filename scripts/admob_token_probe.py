#!/usr/bin/env python3
"""Probe AdMob API auth without printing the access token."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import admob_api_auth as auth_mod

ADMOB_API = "https://admob.googleapis.com/v1"


def _get(path: str, auth: auth_mod.AdmobAuth) -> tuple[int, dict]:
    url = f"{ADMOB_API}/{path.lstrip('/')}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {auth.access_token}",
            "Accept": "application/json",
            "X-Goog-User-Project": auth.quota_project,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = {"raw": body[:500]}
        return exc.code, payload


def main() -> int:
    p = argparse.ArgumentParser(description="Probe AdMob OAuth token (no secret printed).")
    p.add_argument("--publisher-id", default="pub-5173650670360699")
    p.add_argument("--access-token", default=None)
    args = p.parse_args()

    auth = auth_mod.resolve_admob_auth(args.access_token)
    if not auth:
        print("auth: FAIL (no token)")
        print(
            "\nRun:\n"
            "  gcloud auth application-default login "
            f"--scopes={auth_mod.ADMOB_READONLY_SCOPE},"
            "https://www.googleapis.com/auth/cloud-platform\n"
            "Then: python3 scripts/admob_token_probe.py",
            file=sys.stderr,
        )
        return 2

    print(f"auth: OK (source={auth.source}, quota_project={auth.quota_project})")

    print("probe: GET /v1/accounts")
    code, body = _get("accounts", auth)
    print(f"http_status: {code}")
    if code != 200:
        print(json.dumps(body, indent=2)[:800])
        if code == 401:
            print(
                "\n401: expired ADMOB_ACCESS_TOKEN or invalid Playground token. Use ADC (see above).",
                file=sys.stderr,
            )
        return 1

    accounts = body.get("account") or []
    names = [a.get("name", "") for a in accounts]
    print(f"accounts: {json.dumps(names)}")
    parent = names[0] if names else f"accounts/{args.publisher_id}"
    print(f"probe: GET /v1/{parent}/apps?pageSize=5")
    code2, body2 = _get(f"{parent}/apps?pageSize=5", auth)
    print(f"http_status: {code2}")
    if code2 == 200:
        for app in body2.get("apps") or []:
            print(
                f"  - {app.get('platform')} {app.get('manualAppInfo', {}).get('displayName')} "
                f"approval={app.get('appApprovalState')}"
            )
        return 0
    print(json.dumps(body2, indent=2)[:800])
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
