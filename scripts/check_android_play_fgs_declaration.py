#!/usr/bin/env python3
"""Fail fast when Android Play FGS declarations are required but not acknowledged."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path


SPECIAL_USE_SUBTYPE = "android.app.PROPERTY_SPECIAL_USE_FGS_SUBTYPE"
ANDROID_NAME_RE = re.compile(r'android:name\s*=\s*"([^"]+)"')
ANDROID_VALUE_RE = re.compile(r'android:value\s*=\s*"([^"]*)"')
ANDROID_FGS_TYPE_RE = re.compile(r'android:foregroundServiceType\s*=\s*"([^"]*)"')
PERMISSION_RE = re.compile(r"<uses-permission\b[^>]*>", re.DOTALL)
SERVICE_RE = re.compile(r"<service\b(?P<attrs>[^>]*)>(?P<body>.*?)</service>", re.DOTALL)
PROPERTY_RE = re.compile(r"<property\b[^>]*/?>", re.DOTALL)


def _read_manifest(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise SystemExit(f"Manifest not found: {path}") from exc


def _first_match(pattern: re.Pattern[str], text: str) -> str:
    match = pattern.search(text)
    return match.group(1) if match else ""


def inspect_manifest(path: Path) -> dict[str, object]:
    manifest = _read_manifest(path)
    permissions = sorted(
        name
        for name in (_first_match(ANDROID_NAME_RE, node.group(0)) for node in PERMISSION_RE.finditer(manifest))
        if name.startswith("android.permission.FOREGROUND_SERVICE")
    )

    services: list[dict[str, object]] = []
    for service in SERVICE_RE.finditer(manifest):
        attrs = service.group("attrs")
        body = service.group("body")
        raw_types = _first_match(ANDROID_FGS_TYPE_RE, attrs)
        foreground_service_types = sorted(part for part in raw_types.split("|") if part)
        if not foreground_service_types:
            continue
        special_use_subtype = ""
        for prop in PROPERTY_RE.finditer(body):
            prop_text = prop.group(0)
            if _first_match(ANDROID_NAME_RE, prop_text) == SPECIAL_USE_SUBTYPE:
                special_use_subtype = _first_match(ANDROID_VALUE_RE, prop_text)
                break
        services.append(
            {
                "name": _first_match(ANDROID_NAME_RE, attrs),
                "foreground_service_types": foreground_service_types,
                "special_use_subtype": special_use_subtype,
            }
        )

    return {
        "manifest": str(path),
        "foreground_service_permissions": permissions,
        "foreground_service_services": services,
        "requires_play_console_declaration": bool(permissions or services),
    }


def _ack_present(env_names: list[str]) -> bool:
    return any(bool(os.environ.get(name, "").strip()) for name in env_names)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("native-android/app/src/main/AndroidManifest.xml"),
    )
    parser.add_argument(
        "--require-ack-env",
        action="append",
        default=[],
        help="Environment variable that must be non-empty when FGS use is detected.",
    )
    args = parser.parse_args(argv)

    result = inspect_manifest(args.manifest)
    print(json.dumps(result, indent=2, sort_keys=True))

    if result["requires_play_console_declaration"] and args.require_ack_env and not _ack_present(args.require_ack_env):
        env_list = ", ".join(args.require_ack_env)
        print(
            "::error::Android manifest uses Foreground Service permissions/types, but Play Console "
            f"FGS declaration acknowledgement is missing. Complete Play Console > App content > "
            f"Foreground service permissions for com.iganapolsky.randomtimer, then set one of: {env_list}.",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
