#!/usr/bin/env python3
"""Diagnose TestFlight tester/build/group state via ASC API."""
import os, sys, time
import jwt, requests

BUNDLE_ID = "com.igorganapolsky.randomtimer"

def token():
    kid = os.environ["APPSTORE_KEY_ID"]
    iss = os.environ["APPSTORE_ISSUER_ID"]
    pk = os.environ.get("APPSTORE_PRIVATE_KEY", "")
    kp = os.path.expanduser(f"~/.appstoreconnect/private_keys/AuthKey_{kid}.p8")
    if os.path.isfile(kp):
        pk = open(kp).read()
    pk = pk.replace("\\n", "\n").strip()
    now = int(time.time())
    return jwt.encode({"iss": iss, "iat": now, "exp": now+1200, "aud": "appstoreconnect-v1"}, pk, algorithm="ES256", headers={"kid": kid})

def get(tok, path, params=None):
    r = requests.get(f"https://api.appstoreconnect.apple.com/v1{path}", headers={"Authorization": f"Bearer {tok}"}, params=params, timeout=30)
    if not r.ok: print(f"  ERR {path} -> {r.status_code}: {r.text[:300]}")
    return r.json() if r.ok and r.text else {}

def main():
    t = token()
    app = get(t, "/apps", {"filter[bundleId]": BUNDLE_ID})["data"][0]
    app_id = app["id"]
    print(f"App: {app['attributes']['name']} (id={app_id})")

    print("\n=== Beta Groups ===")
    groups = get(t, f"/apps/{app_id}/betaGroups", {"fields[betaGroups]": "name,isInternalGroup"})
    for g in groups.get("data", []):
        a = g["attributes"]
        gid = g["id"]
        print(f"  {a['name']} (internal={a.get('isInternalGroup')}, id={gid})")
        members = get(t, f"/betaGroups/{gid}/betaTesters", {"fields[betaTesters]": "email,inviteType"})
        for m in members.get("data", []):
            ma = m["attributes"]
            print(f"    tester: {ma.get('email')} inviteType={ma.get('inviteType')}")
        builds = get(t, f"/betaGroups/{gid}/builds", {"fields[builds]": "version,processingState,uploadedDate", "limit": 3})
        for b in builds.get("data", []):
            ba = b["attributes"]
            print(f"    build: {ba['version']} processing={ba['processingState']} uploaded={ba.get('uploadedDate','?')}")

    print("\n=== Recent Builds + Beta Review State ===")
    builds = get(t, "/builds", {"filter[app]": app_id, "sort": "-uploadedDate", "limit": 5,
        "fields[builds]": "version,processingState,uploadedDate",
        "include": "buildBetaDetail", "fields[buildBetaDetails]": "externalBuildState,internalBuildState"})
    details = {i["id"]: i["attributes"] for i in builds.get("included", []) if i["type"] == "buildBetaDetails"}
    for b in builds.get("data", []):
        ba = b["attributes"]
        rel = b.get("relationships", {}).get("buildBetaDetail", {}).get("data", {})
        det = details.get(rel.get("id"), {})
        print(f"  Build {ba['version']}: processing={ba['processingState']} external={det.get('externalBuildState','?')} internal={det.get('internalBuildState','?')}")

    print("\n=== Tester: iganapolsky@gmail.com ===")
    testers = get(t, "/betaTesters", {"filter[email]": "iganapolsky@gmail.com",
        "fields[betaTesters]": "email,inviteType", "include": "betaGroups,apps",
        "fields[betaGroups]": "name", "fields[apps]": "name"})
    for te in testers.get("data", []):
        print(f"  id={te['id']} email={te['attributes'].get('email')} inviteType={te['attributes'].get('inviteType')}")
    for inc in testers.get("included", []):
        if inc["type"] == "betaGroups":
            print(f"  group: {inc['attributes']['name']}")
        elif inc["type"] == "apps":
            print(f"  app: {inc['attributes']['name']}")

    print("\n=== ASC Users (team members) ===")
    users = get(t, "/users", {"fields[users]": "username,roles", "limit": 10})
    for u in users.get("data", []):
        ua = u["attributes"]
        print(f"  {ua.get('username')} roles={ua.get('roles')}")

    print("\nDone.")

if __name__ == "__main__":
    main()
