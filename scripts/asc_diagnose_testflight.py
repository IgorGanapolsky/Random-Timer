#!/usr/bin/env python3
"""Diagnose TestFlight state via ASC API."""
import os, time
import jwt, requests
BUNDLE_ID = "com.igorganapolsky.randomtimer"
def token():
    kid, iss = os.environ["APPSTORE_KEY_ID"], os.environ["APPSTORE_ISSUER_ID"]
    pk = os.environ.get("APPSTORE_PRIVATE_KEY", "")
    if not pk:
        kp = os.path.expanduser(f"~/.appstoreconnect/private_keys/AuthKey_{kid}.p8")
        pk = open(kp).read() if os.path.isfile(kp) else ""
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
    aid = app["id"]
    print(f"App: {app['attributes']['name']} (id={aid})")
    print("\n=== Beta Groups ===")
    gs = get(t, f"/apps/{aid}/betaGroups", {"fields[betaGroups]": "name,isInternalGroup"})
    for g in gs.get("data", []):
        a, gid = g["attributes"], g["id"]
        print(f"\n  GROUP: {a['name']} (internal={a.get('isInternalGroup')}, id={gid})")
        ms = get(t, f"/betaGroups/{gid}/betaTesters", {"fields[betaTesters]": "email,inviteType"})
        for m in ms.get("data", []): print(f"    tester: {m['attributes'].get('email')} inviteType={m['attributes'].get('inviteType')}")
        if not ms.get("data"): print("    (no members)")
        bs = get(t, f"/betaGroups/{gid}/builds", {"fields[builds]": "version,processingState", "limit": 3})
        for b in bs.get("data", []): print(f"    build: {b['attributes']['version']} processing={b['attributes']['processingState']}")
        if not bs.get("data"): print("    (no builds)")
    print("\n=== Recent Builds + Beta Review ===")
    bs = get(t, "/builds", {"filter[app]": aid, "sort": "-uploadedDate", "limit": 5, "fields[builds]": "version,processingState,uploadedDate", "include": "buildBetaDetail", "fields[buildBetaDetails]": "externalBuildState,internalBuildState"})
    dets = {i["id"]: i["attributes"] for i in bs.get("included", []) if i["type"] == "buildBetaDetails"}
    for b in bs.get("data", []):
        ba = b["attributes"]
        rel = b.get("relationships", {}).get("buildBetaDetail", {}).get("data", {})
        d = dets.get(rel.get("id"), {})
        print(f"  Build {ba['version']}: processing={ba['processingState']} external={d.get('externalBuildState','?')} internal={d.get('internalBuildState','?')}")
    print("\n=== Tester: iganapolsky@gmail.com ===")
    ts = get(t, "/betaTesters", {"filter[email]": "iganapolsky@gmail.com", "fields[betaTesters]": "email,inviteType", "include": "betaGroups", "fields[betaGroups]": "name"})
    for te in ts.get("data", []): print(f"  id={te['id']} email={te['attributes'].get('email')} inviteType={te['attributes'].get('inviteType')}")
    for inc in ts.get("included", []):
        if inc["type"] == "betaGroups": print(f"  group: {inc['attributes']['name']}")
    print("\nDone.")
if __name__ == "__main__":
    main()
