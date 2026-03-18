#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Reuse logic from asc_add_tester.py
sys.path.append(str(Path(__file__).parent.parent))
import asc_add_tester as asc

def main():
    token = asc.build_token()
    
    data = asc.api(token, "GET", "/users")
    
    print("\nApp Store Connect Users:")
    for u in data.get("data", []):
        attrs = u.get("attributes", {})
        print(f"- {attrs.get('username')} ({attrs.get('firstName')} {attrs.get('lastName')}, Roles: {attrs.get('roles')})")

if __name__ == "__main__":
    main()
