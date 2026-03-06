#!/usr/bin/env python3
from scripts.asc_client import ASCClient
import sys

def main():
    client = ASCClient.from_env()
    apps = client.get_all("/apps", params={"filter[bundleId]": "com.igorganapolsky.randomtimer"})
    app_id = apps[0]["id"]
    
    print(f"App ID: {app_id}")
    
    # Check for existing review submissions
    subs = client.get_all("/reviewSubmissions", params={"filter[app]": app_id, "filter[state]": "READY_FOR_REVIEW"})
    
    for sub in subs:
        print(f"Found existing draft submission: {sub['id']} in state {sub.get('attributes', {}).get('state')}")
        print("Canceling/Deleting it to unblock Fastlane...")
        try:
            client.request("DELETE", f"/reviewSubmissions/{sub['id']}")
            print("Deleted successfully.")
        except Exception as e:
            print(f"Failed to delete: {e}")

if __name__ == "__main__":
    main()
