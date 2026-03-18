#!/usr/bin/env python3
"""Add an external beta tester to a TestFlight group via App Store Connect API.

Creates the beta group if it doesn't exist, adds the tester, then distributes
the latest processed build to that group.

Usage:
    python3 scripts/asc_add_tester.py --email iganapolsky@gmail.com --group "Beta Testers"
"""

import argparse
import json
import os
import sys
import time

import jwt
import requests


def die(msg: str) -> None:
    print(f"❌ {msg}", file=sys.stderr)
    sys.exit(1)


def build_token() -> str:
    key_id = os.environ.get("APPSTORE_KEY_ID")
    issuer_id = os.environ.get("APPSTORE_ISSUER_ID")
    private_key = os.environ.get("APPSTORE_PRIVATE_KEY") or ""

    if not key_id or not issuer_id:
        die("Missing APPSTORE_KEY_ID or APPSTORE_ISSUER_ID")

    key_path = os.environ.get(
        "APPSTORE_PRIVATE_KEY_PATH",
        os.path.expanduser(f"~/.appstoreconnect/private_keys/AuthKey_{key_id}.p8"),
    )
    if os.path.isfile(key_path):
        with open(key_path, encoding="utf-8") as f:
            private_key = f.read()

    if not private_key.strip():
        die("No private key found")

    private_key = private_key.replace("\\n", "\n").strip()

    now = int(time.time())
    payload = {
        "iss": issuer_id,
        "iat": now,
        "exp": now + 1200,
        "aud": "appstoreconnect-v1",
    }
    return jwt.encode(payload, private_key, algorithm="ES256", headers={"kid": key_id})


def api(token: str, method: str, path: str, body: dict | None = None, params: dict | None = None) -> dict:
    url = f"https://api.appstoreconnect.apple.com/v1{path}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    resp = requests.request(method, url, headers=headers, json=body, params=params, timeout=30)
    if resp.status_code >= 400:
        print(f"API {method} {path} -> {resp.status_code}: {resp.text[:500]}", file=sys.stderr)
        resp.raise_for_status()
    return resp.json() if resp.text else {}


def find_app(token: str, bundle_id: str) -> str:
    data = api(token, "GET", "/apps", params={"filter[bundleId]": bundle_id})
    apps = data.get("data", [])
    if not apps:
        die(f"No app found with bundleId '{bundle_id}'")
    return apps[0]["id"]


def find_or_create_group(token: str, app_id: str, group_name: str) -> str:
    data = api(token, "GET", f"/apps/{app_id}/betaGroups",
               params={"filter[name]": group_name})
    groups = data.get("data", [])
    if groups:
        print(f"Found existing group '{group_name}' (id={groups[0]['id']})")
        return groups[0]["id"]

    print(f"Creating beta group '{group_name}'...")
    body = {
        "data": {
            "type": "betaGroups",
            "attributes": {
                "name": group_name,
                "isInternalGroup": False,
                "publicLinkEnabled": False,
            },
            "relationships": {
                "app": {"data": {"type": "apps", "id": app_id}}
            },
        }
    }
    data = api(token, "POST", "/betaGroups", body=body)
    group_id = data["data"]["id"]
    print(f"Created group '{group_name}' (id={group_id})")
    return group_id


def find_or_create_tester(token: str, email: str, first_name: str, last_name: str) -> str:
    data = api(token, "GET", "/betaTesters", params={"filter[email]": email})
    testers = data.get("data", [])
    if testers:
        print(f"Found existing tester {email} (id={testers[0]['id']})")
        return testers[0]["id"]

    print(f"Creating tester {email}...")
    body = {
        "data": {
            "type": "betaTesters",
            "attributes": {
                "email": email,
                "firstName": first_name or None,
                "lastName": last_name or None,
            },
        }
    }
    data = api(token, "POST", "/betaTesters", body=body)
    tester_id = data["data"]["id"]
    print(f"Created tester {email} (id={tester_id})")
    return tester_id


def add_tester_to_group(token: str, group_id: str, tester_id: str) -> None:
    body = {"data": [{"type": "betaTesters", "id": tester_id}]}
    api(token, "POST", f"/betaGroups/{group_id}/relationships/betaTesters", body=body)
    print("Added tester to group")


def distribute_latest_build(token: str, app_id: str, group_id: str) -> None:
    data = api(token, "GET", "/builds",
               params={
                   "filter[app]": app_id,
                   "filter[processingState]": "VALID",
                   "sort": "-uploadedDate",
                   "limit": 1,
                   "fields[builds]": "version,processingState,uploadedDate",
               })
    builds = data.get("data", [])
    if not builds:
        print("⚠️ No processed builds found — tester added but no build distributed")
        return

    build_id = builds[0]["id"]
    build_version = builds[0]["attributes"]["version"]
    print(f"Distributing build {build_version} (id={build_id}) to group...")

    body = {"data": [{"type": "builds", "id": build_id}]}
    api(token, "POST", f"/betaGroups/{group_id}/relationships/builds", body=body)
    print(f"✅ Build {build_version} distributed to group")


def main() -> None:
    parser = argparse.ArgumentParser(description="Add TestFlight external beta tester")
    parser.add_argument("--email", required=True)
    parser.add_argument("--first-name", default="")
    parser.add_argument("--last-name", default="")
    parser.add_argument("--group", default="Beta Testers")
    parser.add_argument("--bundle-id", default="com.igorganapolsky.randomtimer")
    args = parser.parse_args()

    token = build_token()
    app_id = find_app(token, args.bundle_id)
    group_id = find_or_create_group(token, app_id, args.group)
    tester_id = find_or_create_tester(token, args.email, args.first_name, args.last_name)
    add_tester_to_group(token, group_id, tester_id)
    distribute_latest_build(token, app_id, group_id)
    print(f"\n✅ {args.email} invited to '{args.group}' on TestFlight")


if __name__ == "__main__":
    main()
