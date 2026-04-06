#!/usr/bin/env python3
"""Compute a monotonic Android release versionCode safe for Google Play rollout."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    from scripts.source_versions import VersionParseError, extract_android_version_code
except ModuleNotFoundError:
    from source_versions import VersionParseError, extract_android_version_code


ANDROID_PACKAGE_DEFAULT = "com.iganapolsky.randomtimer"
DEFAULT_TRACKS = ("production", "beta", "alpha", "internal")
DEFAULT_HTTP_TIMEOUT_SECONDS = 180
DEFAULT_REQUEST_RETRIES = 3


def _read_gradle_version_code(gradle_file: Path) -> int:
    try:
        return extract_android_version_code(gradle_file.read_text(encoding="utf-8"))
    except VersionParseError as exc:
        raise ValueError(f"Unable to find versionCode in {gradle_file}") from exc


def _load_play_service(
    service_account_json: Path,
    timeout_seconds: int = DEFAULT_HTTP_TIMEOUT_SECONDS,
):
    from google.oauth2 import service_account
    from google_auth_httplib2 import AuthorizedHttp
    from googleapiclient.discovery import build
    import httplib2

    credentials = service_account.Credentials.from_service_account_file(
        str(service_account_json),
        scopes=["https://www.googleapis.com/auth/androidpublisher"],
    )
    http = AuthorizedHttp(credentials, http=httplib2.Http(timeout=timeout_seconds))
    return build("androidpublisher", "v3", http=http, cache_discovery=False)


def _execute_request(request: Any, request_retries: int = DEFAULT_REQUEST_RETRIES):
    return request.execute(num_retries=request_retries)


def _extract_release_codes(track_payload: dict[str, Any]) -> list[int]:
    codes: list[int] = []
    for release in track_payload.get("releases", []):
        for raw_code in release.get("versionCodes", []):
            try:
                codes.append(int(raw_code))
            except (TypeError, ValueError):
                continue
    return codes


def _fetch_existing_track_codes(
    service: Any,
    package_name: str,
    tracks: list[str],
    request_retries: int = DEFAULT_REQUEST_RETRIES,
) -> dict[str, list[int]]:
    edits = service.edits()
    edit_id = None
    codes_by_track: dict[str, list[int]] = {}

    try:
        edit = _execute_request(
            edits.insert(body={}, packageName=package_name),
            request_retries=request_retries,
        )
        edit_id = edit["id"]

        for track in tracks:
            try:
                payload = _execute_request(
                    edits.tracks().get(
                        packageName=package_name,
                        editId=edit_id,
                        track=track,
                    ),
                    request_retries=request_retries,
                )
                codes_by_track[track] = _extract_release_codes(payload)
            except Exception as error:
                status = getattr(getattr(error, "resp", None), "status", None)
                if status == 404:
                    codes_by_track[track] = []
                    continue
                raise

        return codes_by_track
    finally:
        if edit_id is not None:
            try:
                _execute_request(
                    edits.delete(packageName=package_name, editId=edit_id),
                    request_retries=request_retries,
                )
            except Exception:
                pass


def compute_next_version_code(base_version_code: int, existing_track_codes: dict[str, list[int]]) -> int:
    highest_existing = max(
        (code for codes in existing_track_codes.values() for code in codes),
        default=0,
    )
    return max(base_version_code, highest_existing) + 1


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute a safe monotonic Android release versionCode.")
    parser.add_argument("--service-account-json", required=True)
    parser.add_argument("--package", default=ANDROID_PACKAGE_DEFAULT)
    parser.add_argument("--gradle-file", default="native-android/app/build.gradle.kts")
    parser.add_argument("--tracks", default=",".join(DEFAULT_TRACKS))
    parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_HTTP_TIMEOUT_SECONDS)
    parser.add_argument("--request-retries", type=int, default=DEFAULT_REQUEST_RETRIES)
    parser.add_argument("--json-output", default="")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    gradle_file = Path(args.gradle_file)
    service_account_json = Path(args.service_account_json)
    tracks = [track.strip() for track in args.tracks.split(",") if track.strip()]

    if not gradle_file.is_file():
        print(f"❌ Gradle file not found: {gradle_file}", file=sys.stderr)
        return 2
    if not service_account_json.is_file():
        print(f"❌ Service account file not found: {service_account_json}", file=sys.stderr)
        return 2

    try:
        base_version_code = _read_gradle_version_code(gradle_file)
        service = _load_play_service(service_account_json, timeout_seconds=args.timeout_seconds)
        existing_track_codes = _fetch_existing_track_codes(
            service,
            args.package,
            tracks,
            request_retries=args.request_retries,
        )
        next_version_code = compute_next_version_code(base_version_code, existing_track_codes)
    except Exception as error:
        print(f"❌ Failed to compute Android release versionCode: {error}", file=sys.stderr)
        return 1

    if args.json_output:
        payload = {
            "package": args.package,
            "gradle_file": str(gradle_file),
            "base_version_code": base_version_code,
            "tracks": tracks,
            "existing_track_codes": existing_track_codes,
            "next_version_code": next_version_code,
        }
        output_path = Path(args.json_output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")

    print(next_version_code)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
