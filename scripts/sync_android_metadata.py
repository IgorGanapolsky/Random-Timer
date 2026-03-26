#!/usr/bin/env python3
"""Sync Android Google Play listing metadata, creatives, and release notes.

This script updates localized listing text for every configured locale and the
en-US image set (icon, feature graphic, phone screenshots). When a track and
version code are supplied it also updates the matching release notes entry.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from pathlib import Path
from typing import Any

try:
    from scripts.play_publish import (
        _commit_edit,
        _load_google_clients,
        _read_text,
        _upload_images,
        _write_json,
    )
except ModuleNotFoundError:
    from play_publish import (  # type: ignore
        _commit_edit,
        _load_google_clients,
        _read_text,
        _upload_images,
        _write_json,
    )

PACKAGE_NAME = "com.iganapolsky.randomtimer"
DEFAULT_METADATA_ROOT = (
    Path(__file__).resolve().parent.parent / "native-android" / "fastlane" / "metadata" / "android"
)
DEFAULT_SUPPORT_URL_PATH = (
    Path(__file__).resolve().parent.parent
    / "native-ios"
    / "fastlane"
    / "metadata"
    / "en-US"
    / "support_url.txt"
)
DEFAULT_RESULT_JSON = Path(os.path.join(os.environ.get("RUNNER_TEMP", os.getcwd()), "android-listing-sync.json"))

# Local dir name -> Google Play API language code.
LANG_MAP = {
    "en-US": "en-US",
    "de-DE": "de-DE",
    "pt-BR": "pt-BR",
    "ja-JP": "ja-JP",
    "ko": "ko-KR",
}


class MetadataSyncError(RuntimeError):
    """Raised when the Play listing sync cannot be completed."""


def _resolve_key_path(explicit_path: str) -> Path:
    if explicit_path.strip():
        path = Path(explicit_path).expanduser().resolve()
        if path.is_file():
            return path
        raise MetadataSyncError(f"Service account key not found at {path}")

    env_path = (os.environ.get("GOOGLE_PLAY_JSON_KEY_PATH") or "").strip()
    if env_path:
        path = Path(env_path).expanduser().resolve()
        if path.is_file():
            return path
        raise MetadataSyncError(f"Service account key not found at {path}")

    fallback = Path(os.environ.get("RUNNER_TEMP", os.getcwd())) / "play-service-account.json"
    if fallback.is_file():
        return fallback

    raise MetadataSyncError(
        "Google Play service account key not found. Set --service-account-json, "
        "GOOGLE_PLAY_JSON_KEY_PATH, or create $RUNNER_TEMP/play-service-account.json."
    )


def _locale_listing(locale_dir: Path) -> dict[str, str]:
    listing: dict[str, str] = {}
    title = _read_text(locale_dir / "title.txt")
    short_desc = _read_text(locale_dir / "short_description.txt")
    full_desc = _read_text(locale_dir / "full_description.txt")
    video = _read_text(locale_dir / "video.txt")

    if title:
        listing["title"] = title
    if short_desc:
        listing["shortDescription"] = short_desc
    if full_desc:
        listing["fullDescription"] = full_desc
    if video:
        listing["video"] = video
    return listing


def _update_localized_listings(service: Any, package: str, edit_id: str, metadata_root: Path) -> list[str]:
    updated: list[str] = []
    for local_lang, api_lang in LANG_MAP.items():
        listing = _locale_listing(metadata_root / local_lang)
        if not listing:
            continue

        try:
            service.edits().listings().update(
                packageName=package,
                editId=edit_id,
                language=api_lang,
                body=listing,
            ).execute()
        except Exception as exc:
            err_msg = str(exc).lower()
            if "invalid" in err_msg or "404" in err_msg or "not found" in err_msg:
                print(
                    f"⚠️ Skipping Play locale {api_lang}: locale not configured in Play Console or invalid request.",
                    file=sys.stderr,
                )
                continue
            raise
        updated.append(api_lang)
    return updated


def _patch_app_details(service: Any, package: str, edit_id: str, support_url_path: Path) -> None:
    body = {"defaultLanguage": "en-US"}
    support_url = _read_text(support_url_path)
    if support_url:
        body["contactWebsite"] = support_url

    try:
        service.edits().details().patch(
            packageName=package,
            editId=edit_id,
            body=body,
        ).execute()
    except Exception:
        # Non-fatal: some app details may be locked or already match.
        pass


def _count_files(pattern: str) -> int:
    return len(sorted(glob.glob(pattern)))


def _update_assets(service: Any, package: str, edit_id: str, metadata_root: Path) -> dict[str, int]:
    image_locale = metadata_root / "en-US" / "images"
    icon_pattern = str(image_locale / "icon.*")
    feature_pattern = str(image_locale / "featureGraphic" / "*.*")
    screenshots_pattern = str(image_locale / "phoneScreenshots" / "*.*")

    _upload_images(service, package, edit_id, "en-US", "icon", icon_pattern)
    _upload_images(service, package, edit_id, "en-US", "featureGraphic", feature_pattern)
    _upload_images(service, package, edit_id, "en-US", "phoneScreenshots", screenshots_pattern)

    return {
        "icon": _count_files(icon_pattern),
        "featureGraphic": _count_files(feature_pattern),
        "phoneScreenshots": _count_files(screenshots_pattern),
    }


def _resolve_release_notes(changelog_dir: Path, version_code: str) -> tuple[str, str]:
    preferred = changelog_dir / f"{version_code}.txt"
    if preferred.is_file():
        return _read_text(preferred), str(preferred)

    fallback = changelog_dir / "default.txt"
    if fallback.is_file():
        return _read_text(fallback), str(fallback)

    return "", ""


def _update_release_notes(
    service: Any,
    package: str,
    edit_id: str,
    track: str,
    version_code: str,
    changelog_dir: Path,
) -> tuple[bool, str]:
    release_notes, source_path = _resolve_release_notes(changelog_dir, version_code)
    if not release_notes:
        return False, ""

    track_info = service.edits().tracks().get(
        packageName=package,
        editId=edit_id,
        track=track,
    ).execute()
    releases = track_info.get("releases", [])
    target_release: dict[str, Any] | None = None
    for release in releases:
        codes = [str(code) for code in release.get("versionCodes", [])]
        if version_code in codes:
            target_release = release
            break

    if target_release is None:
        raise MetadataSyncError(
            f"Could not find versionCode {version_code} on track '{track}' to update release notes."
        )

    target_release["releaseNotes"] = [{"language": "en-US", "text": release_notes}]
    service.edits().tracks().update(
        packageName=package,
        editId=edit_id,
        track=track,
        body={"releases": releases},
    ).execute()
    return True, source_path


def run(
    *,
    package: str,
    metadata_root: Path,
    support_url_path: Path,
    credentials_path: Path,
    track: str,
    version_code: str,
    result_json: Path | None,
) -> dict[str, Any]:
    service = _load_google_clients(credentials_path)
    edit = service.edits().insert(packageName=package, body={}).execute()
    edit_id = edit["id"]

    updated_languages = _update_localized_listings(service, package, edit_id, metadata_root)
    _patch_app_details(service, package, edit_id, support_url_path)
    image_counts = _update_assets(service, package, edit_id, metadata_root)

    release_notes_updated = False
    release_notes_source = ""
    if track and version_code:
        release_notes_updated, release_notes_source = _update_release_notes(
            service,
            package,
            edit_id,
            track,
            version_code,
            metadata_root / "en-US" / "changelogs",
        )

    changes_not_sent_for_review = _commit_edit(service.edits(), package, edit_id)
    payload = {
        "package": package,
        "updated_languages": updated_languages,
        "image_counts": image_counts,
        "track": track,
        "version_code": version_code,
        "release_notes_updated": release_notes_updated,
        "release_notes_source": release_notes_source,
        "changes_not_sent_for_review": changes_not_sent_for_review,
    }
    if result_json is not None:
        _write_json(result_json, payload)
    return payload


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync Google Play listing metadata and creatives.")
    parser.add_argument("--service-account-json", default="")
    parser.add_argument("--package", default=PACKAGE_NAME)
    parser.add_argument("--metadata-root", default=str(DEFAULT_METADATA_ROOT))
    parser.add_argument("--support-url-path", default=str(DEFAULT_SUPPORT_URL_PATH))
    parser.add_argument("--track", default="", help="Optional Play track for release note sync.")
    parser.add_argument("--version-code", default="", help="Optional versionCode for release note sync.")
    parser.add_argument("--result-json", default=str(DEFAULT_RESULT_JSON))
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    try:
        payload = run(
            package=args.package.strip() or PACKAGE_NAME,
            metadata_root=Path(args.metadata_root).expanduser().resolve(),
            support_url_path=Path(args.support_url_path).expanduser().resolve(),
            credentials_path=_resolve_key_path(args.service_account_json),
            track=args.track.strip(),
            version_code=args.version_code.strip(),
            result_json=Path(args.result_json).expanduser().resolve() if args.result_json.strip() else None,
        )
    except MetadataSyncError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"❌ Android metadata sync failed: {exc}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "updated_languages": payload["updated_languages"],
                "image_counts": payload["image_counts"],
                "track": payload["track"],
                "version_code": payload["version_code"],
                "release_notes_updated": payload["release_notes_updated"],
            },
            indent=2,
        )
    )
    if payload["changes_not_sent_for_review"]:
        print(
            "ℹ️ Google Play committed the edit with changesNotSentForReview=true. "
            "Open Play Console and click 'Send for review' if needed.",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
