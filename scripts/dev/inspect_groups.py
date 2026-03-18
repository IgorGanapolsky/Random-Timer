#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Reuse logic from asc_add_tester.py
sys.path.append(str(Path(__file__).parent.parent))
import asc_add_tester as asc

def main():
    token = asc.build_token()
    app_id = asc.find_app(token, "com.igorganapolsky.randomtimer")
    
    data = asc.api(token, "GET", f"/apps/{app_id}/betaGroups", 
                   params={"fields[betaGroups]": "name,isInternalGroup"})
    
    print("\nExisting Beta Groups:")
    for g in data.get("data", []):
        attrs = g.get("attributes", {})
        print(f"- {attrs.get('name')} (Internal: {attrs.get('isInternalGroup')}, ID: {g['id']})")

if __name__ == "__main__":
    main()
