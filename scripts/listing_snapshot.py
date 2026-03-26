#!/usr/bin/env python3
"""Write a store-listing snapshot artifact for Android or iOS."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from scripts.source_versions import read_source_versions
except ModuleNotFoundError:
    from source_versions import read_source_versions  # type: ignore


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _png_inventory(directory: Path) -> list[dict[str, str]]:
    files = sorted(directory.glob("*.png")) if directory.is_dir() else []
    return [{"file": path.name, "sha256": _sha256(path)} for path in files]


def build_android_snapshot(
    repo_root: Path,
    *,
    source_run_id: str,
    source_run_url: str,
    track: str,
    version_code: str,
) -> dict[str, Any]:
    versions = read_source_versions(repo_root)
    images_root = repo_root / "native-android" / "fastlane" / "metadata" / "android" / "en-US" / "images"
    icon_path = images_root / "icon.png"
    feature_graphic_path = images_root / "featureGraphic" / "feature-graphic.png"
    screenshots_dir = images_root / "phoneScreenshots"
    return {
        "generated_at": _now_iso(),
        "platform": "android",
        "source_run": {"id": source_run_id, "url": source_run_url},
        "app_name": (repo_root / "native-android" / "fastlane" / "metadata" / "android" / "en-US" / "title.txt")
        .read_text(encoding="utf-8")
        .strip(),
        "version_name": str(versions["android"]["version_name"]),
        "version_code": version_code or str(versions["android"]["version_code"]),
        "track": track,
        "icon_sha256": _sha256(icon_path),
        "feature_graphic_sha256": _sha256(feature_graphic_path),
        "screenshots": _png_inventory(screenshots_dir),
    }


def build_ios_snapshot(
    repo_root: Path,
    *,
    source_run_id: str,
    source_run_url: str,
    locale: str,
    app_store_version: str,
) -> dict[str, Any]:
    versions = read_source_versions(repo_root)
    screenshots_dir = repo_root / "native-ios" / "fastlane" / "screenshots" / locale
    icon_path = (
        repo_root
        / "native-ios"
        / "RandomTimer"
        / "Resources"
        / "Assets.xcassets"
        / "AppIcon.appiconset"
        / "icon-1024.png"
    )
    return {
        "generated_at": _now_iso(),
        "platform": "ios",
        "source_run": {"id": source_run_id, "url": source_run_url},
        "app_name": (repo_root / "native-ios" / "fastlane" / "metadata" / locale / "name.txt")
        .read_text(encoding="utf-8")
        .strip(),
        "version_name": str(versions["ios"]["version_name"]),
        "build_number": str(versions["ios"]["build_number"]),
        "app_store_version": app_store_version or str(versions["ios"]["version_name"]),
        "locale": locale,
        "icon_sha256": _sha256(icon_path),
        "screenshots": _png_inventory(screenshots_dir),
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write a store-listing snapshot artifact.")
    parser.add_argument("--platform", choices=("android", "ios"), required=True)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output", required=True)
    parser.add_argument("--source-run-id", default="")
    parser.add_argument("--source-run-url", default="")
    parser.add_argument("--track", default="")
    parser.add_argument("--version-code", default="")
    parser.add_argument("--locale", default="en-US")
    parser.add_argument("--app-store-version", default="")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    repo_root = Path(args.repo_root).resolve()
    if args.platform == "android":
        payload = build_android_snapshot(
            repo_root,
            source_run_id=args.source_run_id,
            source_run_url=args.source_run_url,
            track=args.track,
            version_code=args.version_code,
        )
    else:
        payload = build_ios_snapshot(
            repo_root,
            source_run_id=args.source_run_id,
            source_run_url=args.source_run_url,
            locale=args.locale,
            app_store_version=args.app_store_version,
        )

    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
