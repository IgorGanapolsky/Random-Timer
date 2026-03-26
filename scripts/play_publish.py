#!/usr/bin/env python3
"""Publish Android AAB to Google Play with production->alpha fallback support."""

from __future__ import annotations

import argparse
import glob
import json
import mimetypes
import os
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

RESET_ERROR_FRAGMENT = (
    "certificate this apk is signed with is not yet valid because it has been recently reset"
)
TRANSIENT_ERROR_FRAGMENTS = (
    "eof occurred in violation of protocol",
    "connection reset",
    "connection aborted",
    "timed out",
    "temporary failure",
    "service unavailable",
)
FAILED_PRECONDITION_MARKERS = (
    "failed_precondition",
    "precondition check failed",
)
MANUAL_REVIEW_REQUIRED_MARKERS = (
    "changes cannot be sent for review automatically",
    "changesnotsentforreview",
)
LANG_MAP = {
    "en-US": "en-US",
    "de-DE": "de-DE",
    "pt-BR": "pt-BR",
    "ja-JP": "ja-JP",
    "ko": "ko-KR",
}


@dataclass
class PublishError(RuntimeError):
    """Structured publish error with response payload for workflow triage."""

    message: str
    http_status: int | None
    response_text: str
    attempt: int


def _read_text(path: Path) -> str:
    try:
        if path.is_file():
            return path.read_text(encoding="utf-8").strip()
    except Exception:
        return ""
    return ""


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def _mime_for(path: str) -> str:
    mime, _ = mimetypes.guess_type(path)
    return mime or "application/octet-stream"


def _extract_response_text(error: Exception) -> str:
    raw = getattr(error, "content", b"") or b""
    if isinstance(raw, (bytes, bytearray)):
        return raw.decode("utf-8", errors="ignore").strip()
    return str(raw).strip()


def _is_failed_precondition(message: str, response_text: str, http_status: int | None) -> bool:
    combined = f"{message}\n{response_text}".lower()
    if any(marker in combined for marker in FAILED_PRECONDITION_MARKERS):
        return True
    return http_status == 400 and "precondition" in combined


def _is_transient_http(http_status: int | None, message: str) -> bool:
    if http_status in (429, 500, 502, 503, 504):
        return True
    lowered = message.lower()
    return any(fragment in lowered for fragment in TRANSIENT_ERROR_FRAGMENTS)


def _requires_manual_review_submission(message: str, response_text: str, http_status: int | None) -> bool:
    combined = f"{message}\n{response_text}".lower()
    return http_status == 400 and any(marker in combined for marker in MANUAL_REVIEW_REQUIRED_MARKERS)


def _load_google_clients(credentials_path: Path):
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    credentials = service_account.Credentials.from_service_account_file(
        str(credentials_path), scopes=["https://www.googleapis.com/auth/androidpublisher"]
    )
    return build("androidpublisher", "v3", credentials=credentials)


def _upload_images(service: Any, package: str, edit_id: str, language: str, image_type: str, pattern: str) -> None:
    from googleapiclient.http import MediaFileUpload

    files = sorted(glob.glob(pattern))
    if not files:
        return
    try:
        service.edits().images().deleteall(
            packageName=package,
            editId=edit_id,
            language=language,
            imageType=image_type,
        ).execute()
    except Exception:
        pass

    for fp in files:
        service.edits().images().upload(
            packageName=package,
            editId=edit_id,
            language=language,
            imageType=image_type,
            media_body=MediaFileUpload(fp, mimetype=_mime_for(fp)),
        ).execute()


def _commit_edit(edits_service: Any, package: str, edit_id: str) -> bool:
    """Commit a Play edit.

    Returns True when Google requires `changesNotSentForReview=true`, which means
    the edit was committed successfully but still needs a manual "Send for review"
    action in Play Console.
    """

    try:
        edits_service.commit(packageName=package, editId=edit_id).execute()
        return False
    except Exception as error:
        message = str(error)
        response_text = _extract_response_text(error)
        status = getattr(getattr(error, "resp", None), "status", None)
        if "changesNotSentForReview must not be set" in message:
            return False
        if not _requires_manual_review_submission(message, response_text, status):
            raise
        try:
            edits_service.commit(
                packageName=package,
                editId=edit_id,
                changesNotSentForReview=True,
            ).execute()
            return True
        except Exception as retry_error:
            if "changesNotSentForReview must not be set" in str(retry_error):
                return False
            raise


def _update_listing_and_assets(
    service: Any,
    package: str,
    edit_id: str,
    metadata_dir: Path,
    ios_support_url_path: Path,
) -> None:
    for local_lang, api_lang in LANG_MAP.items():
        locale_dir = metadata_dir / local_lang
        listing = {}
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

        if not listing:
            continue

        try:
            service.edits().listings().update(
                packageName=package,
                editId=edit_id,
                language=api_lang,
                body=listing,
            ).execute()
        except Exception:
            continue

    details = {"defaultLanguage": "en-US"}
    support_url = _read_text(ios_support_url_path)
    if support_url:
        details["contactWebsite"] = support_url
    try:
        service.edits().details().patch(
            packageName=package,
            editId=edit_id,
            body=details,
        ).execute()
    except Exception:
        pass

    _upload_images(
        service,
        package,
        edit_id,
        "en-US",
        "icon",
        str(metadata_dir / "en-US" / "images" / "icon.*"),
    )
    _upload_images(
        service,
        package,
        edit_id,
        "en-US",
        "featureGraphic",
        str(metadata_dir / "en-US" / "images" / "featureGraphic" / "*.*"),
    )
    _upload_images(
        service,
        package,
        edit_id,
        "en-US",
        "phoneScreenshots",
        str(metadata_dir / "en-US" / "images" / "phoneScreenshots" / "*.*"),
    )


def _release_payload(
    version_code: str | int,
    release_status: str,
    release_notes: str,
    user_fraction_raw: str,
) -> dict[str, Any]:
    release: dict[str, Any] = {
        "versionCodes": [str(version_code)],
        "status": release_status,
        "name": f"v{version_code}",
    }
    if release_notes:
        release["releaseNotes"] = [{"language": "en-US", "text": release_notes}]

    if release_status == "inProgress":
        try:
            user_fraction = float(user_fraction_raw.strip() or "0.1")
        except Exception:
            user_fraction = 0.1
        user_fraction = max(0.0, min(1.0, user_fraction))
        if user_fraction >= 1.0:
            user_fraction = 0.1
        release["userFraction"] = user_fraction

    return release


def _publish_to_track(
    *,
    package: str,
    aab_path: Path,
    track: str,
    release_status: str,
    retry_window_seconds: int,
    retry_interval_seconds: int,
    metadata_dir: Path,
    ios_support_url_path: Path,
    changelog_dir: Path,
    credentials_path: Path,
    user_fraction_raw: str,
) -> dict[str, Any]:
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload

    service = _load_google_clients(credentials_path)
    deadline = time.time() + retry_window_seconds
    attempt = 0

    while True:
        attempt += 1
        try:
            edit = service.edits().insert(body={}, packageName=package).execute()
            edit_id = edit["id"]

            bundle = service.edits().bundles().upload(
                packageName=package,
                editId=edit_id,
                media_body=MediaFileUpload(str(aab_path), mimetype="application/octet-stream"),
            ).execute()
            version_code = bundle["versionCode"]

            _update_listing_and_assets(
                service=service,
                package=package,
                edit_id=edit_id,
                metadata_dir=metadata_dir,
                ios_support_url_path=ios_support_url_path,
            )

            notes_path = changelog_dir / f"{version_code}.txt"
            release_notes = _read_text(notes_path)
            release = _release_payload(
                version_code=version_code,
                release_status=release_status,
                release_notes=release_notes,
                user_fraction_raw=user_fraction_raw,
            )

            service.edits().tracks().update(
                packageName=package,
                editId=edit_id,
                track=track,
                body={"releases": [release]},
            ).execute()
            changes_not_sent_for_review = _commit_edit(service.edits(), package, edit_id)

            return {
                "version_code": str(version_code),
                "attempt": attempt,
                "changes_not_sent_for_review": changes_not_sent_for_review,
            }
        except HttpError as error:
            message = str(error)
            response_text = _extract_response_text(error)
            status = getattr(getattr(error, "resp", None), "status", None)
            is_recent_reset = RESET_ERROR_FRAGMENT in f"{message}\n{response_text}".lower()
            if (is_recent_reset or _is_transient_http(status, message)) and int(deadline - time.time()) > 0:
                remaining = int(deadline - time.time())
                sleep_for = min(retry_interval_seconds, remaining)
                reason = "key reset propagation" if is_recent_reset else f"transient HTTP {status}"
                print(
                    f"⚠️ Play upload retry due to {reason} (track={track}, attempt={attempt}). "
                    f"Retrying in {sleep_for}s (remaining window: {remaining}s)...",
                    file=sys.stderr,
                )
                time.sleep(sleep_for)
                continue
            raise PublishError(message=message, http_status=status, response_text=response_text, attempt=attempt)
        except Exception as error:
            message = str(error)
            if _is_transient_http(None, message) and int(deadline - time.time()) > 0:
                remaining = int(deadline - time.time())
                sleep_for = min(retry_interval_seconds, remaining)
                print(
                    f"⚠️ Play upload transient network error (track={track}, attempt={attempt}): {message}. "
                    f"Retrying in {sleep_for}s (remaining window: {remaining}s)...",
                    file=sys.stderr,
                )
                time.sleep(sleep_for)
                continue
            raise PublishError(message=message, http_status=None, response_text="", attempt=attempt)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Publish AAB to Play with fallback.")
    parser.add_argument("--service-account-json", required=True)
    parser.add_argument("--package", required=True)
    parser.add_argument("--aab-path", required=True)
    parser.add_argument("--requested-track", default="production")
    parser.add_argument("--fallback-track", default="alpha")
    parser.add_argument("--release-status", default="completed")
    parser.add_argument("--retry-window-seconds", type=int, default=10800)
    parser.add_argument("--retry-interval-seconds", type=int, default=300)
    parser.add_argument(
        "--metadata-dir",
        default="native-android/fastlane/metadata/android",
    )
    parser.add_argument(
        "--ios-support-url-path",
        default="native-ios/fastlane/metadata/en-US/support_url.txt",
    )
    parser.add_argument(
        "--changelog-dir",
        default="native-android/fastlane/metadata/android/en-US/changelogs",
    )
    parser.add_argument(
        "--result-json",
        default=os.path.join(tempfile.gettempdir(), "play-upload-result.json"),
    )
    parser.add_argument(
        "--error-json",
        default=os.path.join(tempfile.gettempdir(), "play-upload-error.json"),
    )
    parser.add_argument("--user-fraction", default=os.getenv("PLAY_USER_FRACTION", "0.1"))
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    requested_track = (args.requested_track or "production").strip()
    fallback_track = (args.fallback_track or "alpha").strip()
    tracks = [requested_track]
    if requested_track == "production" and fallback_track and fallback_track != requested_track:
        tracks.append(fallback_track)

    package = args.package.strip()
    aab_path = Path(args.aab_path)
    if not aab_path.is_file():
        print(f"❌ AAB not found: {aab_path}", file=sys.stderr)
        return 2

    service_account_json = Path(args.service_account_json)
    if not service_account_json.is_file():
        print(f"❌ Service account JSON not found: {service_account_json}", file=sys.stderr)
        return 2

    metadata_dir = Path(args.metadata_dir)
    changelog_dir = Path(args.changelog_dir)
    ios_support_url_path = Path(args.ios_support_url_path)
    result_json_path = Path(args.result_json)
    error_json_path = Path(args.error_json)
    release_status = (args.release_status or "completed").strip() or "completed"

    precondition_error_payload: dict[str, Any] | None = None
    for idx, track in enumerate(tracks):
        try:
            outcome = _publish_to_track(
                package=package,
                aab_path=aab_path,
                track=track,
                release_status=release_status,
                retry_window_seconds=args.retry_window_seconds,
                retry_interval_seconds=args.retry_interval_seconds,
                metadata_dir=metadata_dir,
                ios_support_url_path=ios_support_url_path,
                changelog_dir=changelog_dir,
                credentials_path=service_account_json,
                user_fraction_raw=args.user_fraction,
            )
            fallback_used = track != requested_track
            result_payload = {
                "requested_track": requested_track,
                "effective_track": track,
                "fallback_used": fallback_used,
                "precondition_blocked": bool(precondition_error_payload),
                "release_status": release_status,
                "version_code": outcome["version_code"],
                "attempt": outcome["attempt"],
                "changes_not_sent_for_review": bool(outcome.get("changes_not_sent_for_review")),
                "fallback_reason": "FAILED_PRECONDITION" if fallback_used else "",
            }
            if precondition_error_payload:
                result_payload["production_precondition_error"] = precondition_error_payload
            _write_json(result_json_path, result_payload)
            print(
                f"✅ Uploaded version code {outcome['version_code']} to '{track}' track "
                f"(requested={requested_track}, status={release_status}, fallback_used={fallback_used})"
            )
            if outcome.get("changes_not_sent_for_review"):
                print(
                    "ℹ️ Google Play committed the edit with changesNotSentForReview=true. "
                    "Open Play Console and click 'Send for review' for this release.",
                    file=sys.stderr,
                )
            return 0
        except PublishError as error:
            payload = {
                "package": package,
                "requested_track": requested_track,
                "track": track,
                "release_status": release_status,
                "attempt": error.attempt,
                "http_status": error.http_status,
                "error": error.message,
                "response": error.response_text,
            }
            _write_json(error_json_path, payload)
            is_production_precondition = (
                idx == 0
                and track == "production"
                and _is_failed_precondition(error.message, error.response_text, error.http_status)
            )
            if is_production_precondition and len(tracks) > 1:
                precondition_error_payload = payload
                print(
                    "⚠️ Production publish blocked by FAILED_PRECONDITION. "
                    f"Falling back to '{tracks[1]}' for continuity.",
                    file=sys.stderr,
                )
                continue
            if error.response_text:
                print(
                    f"❌ Google Play upload failed on track '{track}': {error.message}\n\n"
                    f"Response:\n{error.response_text}",
                    file=sys.stderr,
                )
            else:
                print(f"❌ Google Play upload failed on track '{track}': {error.message}", file=sys.stderr)
            return 1

    print("❌ No publish tracks attempted.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
