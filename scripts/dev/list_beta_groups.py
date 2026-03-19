#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Add scripts root to path so we can import asc_client
sys.path.append(str(Path(__file__).parent.parent))
from asc_client import ASCClient, ASCAuth

def main():
    key_id = os.getenv("APPSTORE_KEY_ID")
    issuer_id = os.getenv("APPSTORE_ISSUER_ID")
    key_content = os.getenv("APPSTORE_PRIVATE_KEY")
    
    if not all([key_id, issuer_id, key_content]):
        print("Missing ASC credentials in env")
        return 1
        
    auth = ASCAuth(key_id, issuer_id, key_content)
    client = ASCClient(auth)
    
    # Get app ID first
    apps = client.get("/v1/apps", params={"filter[bundleId]": "com.igorganapolsky.randomtimer"})
    if not apps:
        print("App not found")
        return 1
        
    app_id = apps[0]["id"]
    print(f"App ID: {app_id}")
    
    groups = client.get(f"/v1/apps/{app_id}/betaGroups")
    print("\nBeta Groups:")
    for g in groups:
        name = g["attributes"]["name"]
        is_internal = g["attributes"]["isInternalGroup"]
        print(f"- {name} (internal={is_internal}, id={g['id']})")
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
