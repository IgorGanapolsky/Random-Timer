#!/usr/bin/env python3
"""Upload Android store listing metadata to Google Play using the Developer API.

Bypasses fastlane supply's track/release resolution which fails when
multiple releases exist on a track. Store listing metadata (title,
short description, full description) is app-level, not track-specific.

Usage:
    python3 scripts/sync_android_metadata.py

Requires:
    - GOOGLE_PLAY_JSON_KEY_PATH or $RUNNER_TEMP/play-service-account.json
    - google-api-python-client, google-auth
"""

import json
import os
import sys
from pathlib import Path

PACKAGE_NAME = "com.iganapolsky.randomtimer"
METADATA_ROOT = Path(__file__).resolve().parent.parent / "native-android" / "fastlane" / "metadata" / "android"

# Local dir name -> Google Play API language code.
# ja-JP/ko: Enable locale in Play Console first; per-locale errors are caught and skipped.
LANG_MAP = {
    "en-US": "en-US",
    "de-DE": "de-DE",
    "pt-BR": "pt-BR",
    "ja-JP": "ja-JP",
    "ko": "ko-KR",
}


def read_metadata(lang_dir: str, filename: str) -> str:
    path = METADATA_ROOT / lang_dir / filename
    if path.exists():
        return path.read_text().strip()
    return ""


def build_edits_service(key_path: str):
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    credentials = service_account.Credentials.from_service_account_file(
        key_path,
        scopes=["https://www.googleapis.com/auth/androidpublisher"],
    )
    service = build("androidpublisher", "v3", credentials=credentials)
    return service.edits()


def commit_edit(edits, *, edit_id: str):
    try:
        return edits.commit(
            packageName=PACKAGE_NAME,
            editId=edit_id,
            changesNotSentForReview=True,
        ).execute()
    except Exception as exc:
        message = str(exc).lower()
        if "changes are sent for review automatically" in message and "changesnotsentforreview" in message:
            print(
                "Play rejected changesNotSentForReview; retrying commit without that flag for auto-review apps.",
                file=sys.stderr,
            )
            return edits.commit(
                packageName=PACKAGE_NAME,
                editId=edit_id,
            ).execute()
        raise


def main():
    key_path = os.environ.get("GOOGLE_PLAY_JSON_KEY_PATH", os.path.join(os.environ.get("RUNNER_TEMP", os.getcwd()), "play-service-account.json"))
    if not os.path.exists(key_path):
        print(f"Service account key not found at {key_path}", file=sys.stderr)
        sys.exit(1)

    edits = build_edits_service(key_path)

    # Create edit
    edit = edits.insert(packageName=PACKAGE_NAME, body={}).execute()
    edit_id = edit["id"]
    print(f"Created edit: {edit_id}")

    updated = []
    skipped = []
    for local_lang, api_lang in LANG_MAP.items():
        title = read_metadata(local_lang, "title.txt")
        short_desc = read_metadata(local_lang, "short_description.txt")
        full_desc = read_metadata(local_lang, "full_description.txt")

        if not any([title, short_desc, full_desc]):
            continue

        listing = {}
        if title:
            listing["title"] = title
        if short_desc:
            listing["shortDescription"] = short_desc
        if full_desc:
            listing["fullDescription"] = full_desc

        try:
            edits.listings().update(
                packageName=PACKAGE_NAME,
                editId=edit_id,
                language=api_lang,
                body=listing,
            ).execute()
            updated.append(api_lang)
            print(f"  Updated listing for {api_lang}: title={'yes' if title else 'no'}, short={'yes' if short_desc else 'no'}, full={'yes' if full_desc else 'no'}")
        except Exception as e:
            err_msg = str(e).lower()
            if "invalid" in err_msg or "404" in err_msg or "not found" in err_msg:
                skipped.append(api_lang)
                print(f"  Skipped {api_lang}: locale not configured in Play Console or invalid request", file=sys.stderr)
            else:
                raise

    if not updated:
        print("No metadata to upload. Discarding edit.")
        edits.delete(packageName=PACKAGE_NAME, editId=edit_id).execute()
        return

    if skipped:
        print(f"Skipped {len(skipped)} locales (enable in Play Console if needed): {', '.join(skipped)}", file=sys.stderr)

    commit_edit(edits, edit_id=edit_id)
    print(f"Committed edit. Updated {len(updated)} languages: {', '.join(updated)}")


if __name__ == "__main__":
    main()
