#!/usr/bin/env python3
"""Print the service account email from GOOGLE_PLAY_JSON_KEY for Play Console setup.

Usage:
  GOOGLE_PLAY_JSON_KEY_PATH=/path/to/key.json python scripts/play_service_account_email.py
  # or
  GOOGLE_PLAY_JSON_KEY='{"type":"service_account",...}' python scripts/play_service_account_email.py

Output: the client_email to add in Play Console > Users and permissions.
"""

import json
import os
import sys


def main() -> int:
    key_path: str = os.environ.get("GOOGLE_PLAY_JSON_KEY_PATH", "").strip()
    key_raw: str = os.environ.get("GOOGLE_PLAY_JSON_KEY", "").strip()

    if key_path and os.path.isfile(key_path):
        with open(key_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    elif key_raw:
        data = json.loads(key_raw)
    else:
        print("Set GOOGLE_PLAY_JSON_KEY_PATH or GOOGLE_PLAY_JSON_KEY", file=sys.stderr)
        return 1

    email = data.get("client_email")
    if not email:
        print("No client_email in JSON", file=sys.stderr)
        return 1

    print(email)
    return 0


if __name__ == "__main__":
    sys.exit(main())
