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
    
    data = asc.api(token, "GET", f"/apps/{app_id}/builds", 
                   params={"limit": 100, "fields[builds]": "version,uploadedDate"})
    
    print("\nAll Builds (Raw):")
    for b in data.get("data", []):
        attrs = b.get("attributes", {})
        print(f"- Version: {attrs.get('version')} | Uploaded: {attrs.get('uploadedDate')} | ID: {b['id']}")

if __name__ == "__main__":
    main()
