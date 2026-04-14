#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


ANDROID_PREFIXES = (
    "native-android/",
)
IOS_PREFIXES = (
    "native-ios/",
)
SHARED_APP_PREFIXES = (
    ".maestro/",
    "content/pro_audio/",
)
ANDROID_DEVICE_PATHS = (
    "scripts/device-tests/ci-maestro.sh",
)
IOS_DEVICE_PATHS = (
    "scripts/device-tests/ci-maestro-ios.sh",
)


def _clean_path(raw: str) -> str:
    return raw.strip().replace("\\", "/")


def classify(paths: list[str], force_all: bool = False) -> dict[str, bool]:
    if force_all:
        return {
            "android": True,
            "ios": True,
            "android_device": True,
            "ios_device": True,
        }

    changed = [_clean_path(path) for path in paths if _clean_path(path)]
    shared_app = any(path.startswith(SHARED_APP_PREFIXES) for path in changed)
    android = shared_app or any(path.startswith(ANDROID_PREFIXES) for path in changed)
    ios = shared_app or any(path.startswith(IOS_PREFIXES) for path in changed)
    android_device = android or any(path in ANDROID_DEVICE_PATHS for path in changed)
    ios_device = ios or any(path in IOS_DEVICE_PATHS for path in changed)

    return {
        "android": android,
        "ios": ios,
        "android_device": android_device,
        "ios_device": ios_device,
    }


def _read_paths(path: str | None) -> list[str]:
    if not path or path == "-":
        return [line.rstrip("\n") for line in os.sys.stdin]
    return Path(path).read_text(encoding="utf-8").splitlines()


def _write_github_output(outputs: dict[str, bool]) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return
    with Path(output_path).open("a", encoding="utf-8") as handle:
        for key, value in outputs.items():
            handle.write(f"{key}={str(value).lower()}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Classify changed files for path-aware CI gates.")
    parser.add_argument("--files", help="Newline-delimited changed-file list. Use '-' or omit for stdin.")
    parser.add_argument("--all", action="store_true", help="Force all app/device components on.")
    parser.add_argument("--github-output", action="store_true", help="Write booleans to $GITHUB_OUTPUT.")
    args = parser.parse_args()

    outputs = classify(_read_paths(args.files), force_all=args.all)
    if args.github_output:
        _write_github_output(outputs)
    print(json.dumps(outputs, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
