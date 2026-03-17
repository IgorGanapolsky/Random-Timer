#!/usr/bin/env python3
"""Read release version metadata from Android and iOS source files."""

from __future__ import annotations

import argparse
import json
import re
import shlex
import sys
from pathlib import Path
from typing import Any


class VersionParseError(RuntimeError):
    """Raised when source version metadata cannot be parsed."""


ANDROID_VERSION_NAME_RE = re.compile(r'versionName\s*=\s*"([^"]+)"')
ANDROID_VERSION_CODE_RE = re.compile(r"versionCode\s*=\s*(?:[^\n]*?\?:\s*)?(\d+)")")
ANDROID_VERSION_CODE_FALLBACK_RE = re.compile(r"versionCode\s*=\s*[^\n]*?\?:\s*(\d+)")
IOS_MARKETING_VERSION_RE = re.compile(r"MARKETING_VERSION\s*=\s*([0-9]+\.[0-9]+\.[0-9]+)\s*;")
IOS_BUILD_NUMBER_RE = re.compile(r"CURRENT_PROJECT_VERSION\s*=\s*(\d+)\s*;")


def _read_text(path: Path) -> str:
    if not path.is_file():
        raise VersionParseError(f"Missing required file: {path}")
    return path.read_text(encoding="utf-8", errors="replace")


def extract_android_version_name(text: str) -> str:
    match = ANDROID_VERSION_NAME_RE.search(text)
    if not match:
        raise VersionParseError("Could not parse Android versionName")
    return match.group(1)


def extract_android_version_code(text: str) -> int:
    match = ANDROID_VERSION_CODE_RE.search(text)
    if match:
        return int(match.group(1))

    fallback_match = ANDROID_VERSION_CODE_FALLBACK_RE.search(text)
    if fallback_match:
        return int(fallback_match.group(1))

    raise VersionParseError("Could not parse Android versionCode")


def extract_ios_version_name(text: str) -> str:
    match = IOS_MARKETING_VERSION_RE.search(text)
    if not match:
        raise VersionParseError("Could not parse iOS MARKETING_VERSION")
    return match.group(1)


def extract_ios_build_number(text: str) -> int:
    match = IOS_BUILD_NUMBER_RE.search(text)
    if not match:
        raise VersionParseError("Could not parse iOS CURRENT_PROJECT_VERSION")
    return int(match.group(1))


def read_source_versions(repo_root: Path) -> dict[str, dict[str, Any]]:
    android_file = repo_root / "native-android" / "app" / "build.gradle.kts"
    ios_file = repo_root / "native-ios" / "RandomTimer.xcodeproj" / "project.pbxproj"

    android_text = _read_text(android_file)
    ios_text = _read_text(ios_file)

    return {
        "android": {
            "version_name": extract_android_version_name(android_text),
            "version_code": extract_android_version_code(android_text),
        },
        "ios": {
            "version_name": extract_ios_version_name(ios_text),
            "build_number": extract_ios_build_number(ios_text),
        },
    }


def _flatten_versions(payload: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "ANDROID_VERSION_NAME": payload["android"]["version_name"],
        "ANDROID_VERSION_CODE": payload["android"]["version_code"],
        "IOS_VERSION_NAME": payload["ios"]["version_name"],
        "IOS_BUILD_NUMBER": payload["ios"]["build_number"],
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read release version metadata from source files.")
    parser.add_argument("--repo-root", default=".", help="Repository root")
    parser.add_argument("--format", choices=("json", "shell", "value"), default="json")
    parser.add_argument("--key", default="", help="Required when --format=value")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    try:
        payload = read_source_versions(Path(args.repo_root).resolve())
    except VersionParseError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    flat = _flatten_versions(payload)
    if args.format == "shell":
        for key, value in flat.items():
            print(f"{key}={shlex.quote(str(value))}")
        return 0

    if args.key not in flat:
        print(f"❌ Unknown key '{args.key}'", file=sys.stderr)
        return 2

    print(flat[args.key])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
