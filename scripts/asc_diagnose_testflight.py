#!/usr/bin/env python3
"""Diagnose TestFlight tester/build/group state via ASC API."""

import json
import os
import sys
import time

import jwt
import requests

BUNDLE_ID = "com.igorganapolsky.randomtimer"


def build_token():
    key_id = os.environ["APPSTORE_KEY_ID"]
    issuer_id = os.environ["APPSTORE_ISSUER_ID"]
    key_path = os.environ.get(
        "APPSTORE_PRIVATE_KEY_PATH",
        os.path.expanduser(f"~/.appstoreconnect/private_keys/AuthKey_{key_id}.p8"),
    )
    with open(key_path, encoding="utf-8") as f:
        pk = f.read().replace("\\n", "\n").strip()
    now = int(time.time())
    return jwt.encode(
        {"iss": issuer_id, "iat": now, "exp": now + 1200, "aud": "appstoreconnect-v1"},
        pk, algorithm="ES256", headers={"kid": key_id},
    )


def api(token, method, path, params=None):
    url = f"https://api.appstoreconnect.apple.com/v1{path}"
    r = requests.request(method, url, headers={"Authorization": f"Bearer {token}"}, params=params, timeout=30)
    if r.status_code >= 400:
        print(f"  API {method} {path} -> {r.status_code}: {r.text[:300]}")
        return {}
    return r.json() if r.text else {}


def main():
    token = build_token()

    # 1. Find app
    data = api(token, "GET", "/apps", {"filter[bundleId]": BUNDLE_ID})
    app_id = data["data"][0]["id"]
    print(f"App ID: {app_id}")

    # 2. List all beta groups
    print("\n=== Beta Groups ===")
    data = api(token, "GET", f"/apps/{app_id}/betaGroups",
               {"fields[betaGroups]": "name,isInternalGroup,publicLinkEnabled"})
    for g in data.get("data", []):
        attrs = g["attributes"]
        print(f"  {attrs['name']} (id={g['id']}, internal={attrs.get('isInternalGroup')}, publicLink={attrs.get('publicLinkEnabled')})")

    # 3. Check "Beta Testers" group members
    print("\n=== Beta Testers Group Members ===")
    for g in data.get("data", []):
        if g["attributes"]["name"] == "Beta Testers":
            members = api(token, "GET", f"/betaGroups/{g['id']}/betaTesters",
                          {"fields[betaTesters]": "email,firstName,lastName,inviteType,state"})
            for m in members.get("data", []):
                a = m["attributes"]
                print(f"  {a.get('email')} — state={a.get('state')} inviteType={a.get('inviteType')}")
            if not members.get("data"):
                print("  (no members)")

            # Check builds assigned to this group
            builds = api(token, "GET", f"/betaGroups/{g['id']}/builds",
                         {"fields[builds]": "version,processingState,uploadedDate"})
            print(f"\n  Builds assigned to group:")
            for b in builds.get("data", []):
                ba = b["attributes"]
                print(f"    Build {ba['version']} — processing={ba['processingState']} uploaded={ba.get('uploadedDate')}")
            if not builds.get("data"):
                print("    (no builds)")

    # 4. List recent builds and their beta review status
    print("\n=== Recent Builds (last 5) ===")
    data = api(token, "GET", "/builds",
               {"filter[app]": app_id, "sort": "-uploadedDate", "limit": 5,
                "fields[builds]": "version,processingState,uploadedDate",
                "include": "betaBuildLocalizations,buildBetaDetail",
                "fields[buildBetaDetails]": "externalBuildState,internalBuildState"})
    for b in data.get("data", []):
        ba = b["attributes"]
        print(f"  Build {ba['version']} — processing={ba['processingState']} uploaded={ba.get('uploadedDate')}")

    # Check beta details from included
    for inc in data.get("included", []):
        if inc["type"] == "buildBetaDetails":
            ia = inc["attributes"]
            print(f"    Beta detail: external={ia.get('externalBuildState')} internal={ia.get('internalBuildState')}")

    # 5. Check tester directly
    print("\n=== Tester: iganapolsky@gmail.com ===")
    data = api(token, "GET", "/betaTesters",
               {"filter[email]": "iganapolsky@gmail.com",
                "fields[betaTesters]": "email,firstName,lastName,inviteType,state",
                "include": "betaGroups",
                "fields[betaGroups]": "name"})
    for t in data.get("data", []):
        ta = t["attributes"]
        print(f"  Email: {ta.get('email')}")
        print(f"  State: {ta.get('state')}")
        print(f"  Invite type: {ta.get('inviteType')}")
    for inc in data.get("included", []):
        if inc["type"] == "betaGroups":
            print(f"  In group: {inc['attributes']['name']}")

    print("\n=== Diagnosis Complete ===")


if __name__ == "__main__":
    main()
