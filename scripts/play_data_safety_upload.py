#!/usr/bin/env python3
"""Upload Play Data Safety labels via Google Play Android Publisher API.

Official method: POST .../applications/{packageName}/dataSafety with body
{"safetyLabels": "<CSV contents>"}.

Docs:
  https://developers.google.com/android-publisher/api-ref/rest/v3/applications/dataSafety
  CSV format: https://support.google.com/googleplay/android-developer/answer/10787469

Requires (same as other Play scripts):
  GOOGLE_PLAY_JSON_KEY (inline JSON) or GOOGLE_PLAY_JSON_KEY_PATH (file path)

Usage:
  python scripts/play_data_safety_upload.py --csv-path ./export.csv
  python scripts/play_data_safety_upload.py --csv-path ./export.csv --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

SCRIPTS = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

DEFAULT_PACKAGE = "com.iganapolsky.randomtimer"


def _credentials_and_service() -> tuple[Any, Optional[str]]:
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        from pem_env import load_google_play_service_account_dict
    except ImportError as exc:
        return None, f"missing_dependency:{exc}"

    import os

    key_path = os.environ.get("GOOGLE_PLAY_JSON_KEY", "").strip()
    if not key_path:
        key_path = os.environ.get("GOOGLE_PLAY_JSON_KEY_PATH", "").strip()
    if not key_path:
        return None, "no GOOGLE_PLAY_JSON_KEY or GOOGLE_PLAY_JSON_KEY_PATH"

    try:
        info = load_google_play_service_account_dict(key_path)
        credentials = service_account.Credentials.from_service_account_info(
            info,
            scopes=["https://www.googleapis.com/auth/androidpublisher"],
        )
    except Exception as exc:
        return None, f"credential_error:{exc}"

    try:
        service = build("androidpublisher", "v3", credentials=credentials)
    except Exception as exc:
        return None, f"build_error:{exc}"
    return service, None


def upload_data_safety_csv(package_name: str, csv_text: str, *, dry_run: bool) -> Dict[str, Any]:
    """Call applications.dataSafety. If dry_run, only validate inputs (no Google auth)."""
    if not csv_text or not csv_text.strip():
        return {"status": "error", "reason": "empty_csv"}

    if dry_run:
        return {
            "status": "dry_run",
            "package_name": package_name,
            "safety_labels_bytes": len(csv_text.encode("utf-8")),
        }

    service, err = _credentials_and_service()
    if err:
        return {"status": "error", "reason": err}

    try:
        (service.applications().dataSafety(packageName=package_name, body={"safetyLabels": csv_text}).execute())
    except Exception as exc:
        return {"status": "error", "reason": str(exc), "package_name": package_name}

    return {"status": "ok", "package_name": package_name}


def main() -> int:
    parser = argparse.ArgumentParser(description="Upload Play Data Safety CSV via androidpublisher API")
    parser.add_argument("--csv-path", type=Path, required=True, help="Path to Data Safety export CSV")
    parser.add_argument("--package", type=str, default=DEFAULT_PACKAGE, help="Android applicationId")
    parser.add_argument("--dry-run", action="store_true", help="Do not call Google; print payload size only")
    parser.add_argument("--json-stdout", action="store_true", help="Print result JSON to stdout")
    args = parser.parse_args()

    path = args.csv_path.resolve()
    if not path.is_file():
        msg = json.dumps({"status": "error", "reason": f"not_a_file:{path}"})
        print(msg)
        return 1

    csv_text = path.read_text(encoding="utf-8")
    result = upload_data_safety_csv(args.package.strip(), csv_text, dry_run=args.dry_run)
    line = json.dumps(result, indent=2 if args.json_stdout else None)
    print(line)
    return 0 if result.get("status") in ("ok", "dry_run") else 1


if __name__ == "__main__":
    raise SystemExit(main())
