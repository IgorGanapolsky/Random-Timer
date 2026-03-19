#!/usr/bin/env python3
"""Add an external beta tester to a TestFlight group via App Store Connect API."""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import jwt
import requests

ISSUER_ID = os.getenv("APPSTORE_ISSUER_ID")
KEY_ID = os.getenv("APPSTORE_KEY_ID")
PRIVATE_KEY = os.getenv("APPSTORE_PRIVATE_KEY")


def build_token():
    if not all([ISSUER_ID, KEY_ID, PRIVATE_KEY]):
        print("Missing App Store Connect credentials in environment")
        sys.exit(1)

    private_key = PRIVATE_KEY.replace("\\n", "\n")
    now = int(time.time())
    payload = {
        "iss": ISSUER_ID,
        "iat": now,
        "exp": now + 1200,
        "aud": "appstoreconnect-v1",
    }
    headers = {"kid": KEY_ID, "typ": "JWT", "alg": "ES256"}
    return jwt.encode(payload, private_key, algorithm="ES256", headers=headers)


def api(token, method, path, params=None, body=None):
    url = f"https://api.appstoreconnect.apple.com/v1{path}"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.request(method, url, headers=headers, params=params, json=body)
    if not resp.ok:
        print(f"API {method} {path} -> {resp.status_code}: {resp.text}")
    resp.raise_for_status()
    return resp.json() if resp.text else {}


def find_app(token, bundle_id):
    data = api(token, "GET", "/apps", params={"filter[bundleId]": bundle_id})
    if not data.get("data"):
        print(f"App with bundle ID {bundle_id} not found")
        sys.exit(1)
    return data["data"][0]["id"]


def find_or_create_group(token, app_id, group_name):
    data = api(token, "GET", f"/apps/{app_id}/betaGroups")
    for g in data.get("data", []):
        if g["attributes"]["name"] == group_name:
            group_id = g["id"]
            is_internal = g["attributes"]["isInternalGroup"]
            print(f"Found existing group '{group_name}' (id={group_id}, internal={is_internal})")
            return group_id, is_internal

    print(f"Creating beta group '{group_name}'...")
    body = {
        "data": {
            "type": "betaGroups",
            "attributes": {"name": group_name, "isInternalGroup": False},
            "relationships": {"app": {"data": {"type": "apps", "id": app_id}}},
        }
    }
    data = api(token, "POST", "/betaGroups", body=body)
    return data["data"]["id"], False


def find_or_create_tester(token, email, first_name, last_name, group_id):
    data = api(token, "GET", "/betaTesters", params={"filter[email]": email})
    if data.get("data"):
        tester_id = data["data"][0]["id"]
        print(f"Found existing tester {email} (id={tester_id})")
        
        print(f"Ensuring {email} is in group...")
        body = {"data": [{"type": "betaTesters", "id": tester_id}]}
        try:
            api(token, "POST", f"/betaGroups/{group_id}/relationships/betaTesters", body=body)
        except Exception as e:
            if "409" not in str(e): raise e
            
        return tester_id

    print(f"Creating tester {email}...")
    body = {
        "data": {
            "type": "betaTesters",
            "attributes": {"email": email, "firstName": first_name, "lastName": last_name},
            "relationships": {"betaGroups": {"data": [{"type": "betaGroups", "id": group_id}]}},
        }
    }
    data = api(token, "POST", "/betaTesters", body=body)
    return data["data"]["id"]


def distribute_latest_build(token, app_id, group_id, is_internal):
    # Find latest build for the app
    data = api(token, "GET", f"/apps/{app_id}/builds", params={"limit": 50, "sort": "-uploadedDate"})
    if not data.get("data"):
        print("No builds found for app")
        return

    latest_build = data["data"][0]
    build_id = latest_build["id"]
    build_version = latest_build["attributes"]["version"]
    
    print(f"Distributing build {build_version} (id={build_id}) to group (internal={is_internal})...")

    # For internal groups, we check if build is already there first to avoid 422
    if is_internal:
        existing = api(token, "GET", f"/betaGroups/{group_id}/builds", params={"filter[version]": build_version})
        if any(b['id'] == build_id for b in existing.get('data', [])):
            print(f"Build {build_version} is already in internal group.")
            return

    body = {"data": [{"type": "builds", "id": build_id}]}
    try:
        api(token, "POST", f"/betaGroups/{group_id}/relationships/builds", body=body)
        print(f"✅ Build {build_version} distributed to group")
    except Exception as e:
        if "409" in str(e):
            print(f"Note: Build {build_version} already distributed.")
        else:
            print(f"Warning: Could not distribute build {build_version}: {e}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    parser.add_argument("--group", default="Beta Testers")
    parser.add_argument("--first-name", default="")
    parser.add_argument("--last-name", default="")
    args = parser.parse_args()

    token = build_token()
    app_id = find_app(token, "com.igorganapolsky.randomtimer")
    group_id, is_internal = find_or_create_group(token, app_id, args.group)
    find_or_create_tester(token, args.email, args.first_name, args.last_name, group_id)
    distribute_latest_build(token, app_id, group_id, is_internal)
    print(f"\n✅ {args.email} processed for '{args.group}' on TestFlight")


if __name__ == "__main__":
    main()
