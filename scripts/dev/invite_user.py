#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Reuse logic from asc_add_tester.py
sys.path.append(str(Path(__file__).parent.parent))
import asc_add_tester as asc

def main():
    token = asc.build_token()
    
    # Invite user to the team
    body = {
        "data": {
            "type": "userInvitations",
            "attributes": {
                "email": "iganapolsky@gmail.com",
                "firstName": "Igor",
                "lastName": "Ganapolsky",
                "roles": ["DEVELOPER"],
                "allAppsVisible": True
            }
        }
    }
    
    try:
        print("Inviting iganapolsky@gmail.com to the App Store Connect team...")
        resp = asc.api(token, "POST", "/userInvitations", body=body)
        print("✅ Team invite sent! Check your email to accept.")
    except Exception as e:
        if "is already a user on this team" in str(e) or "409" in str(e):
            print("Note: User is already on the team or has a pending invite.")
        else:
            raise e

if __name__ == "__main__":
    main()
