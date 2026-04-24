#!/usr/bin/env python3
"""Fail fast when Android Play FGS declarations are required but not acknowledged."""

from __future__ import annotations

import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


ANDROID_NS = "http://schemas.android.com/apk/res/android"
ANDROID_NAME = f"{{{ANDROID_NS}}}name"
ANDROID_VALUE = f"{{{ANDROID_NS}}}value"
ANDROID_FGS_TYPE = f"{{{ANDROID_NS}}}foregroundServiceType"
SPECIAL_USE_SUBTYPE = "android.app.PROPERTY_SPECIAL_USE_FGS_SUBTYPE"


def _parse_manifest(path: Path) -> ET.Element:
    try:
        return ET.parse(path).getroot()
    except FileNotFoundError as exc:
        raise SystemExit(f"Manifest not found: {path}") from exc
    except ET.ParseError as exc:
        raise SystemExit(f"Manifest XML parse failed for {path}: {exc}") from exc


def inspect_manifest(path: Path) -> dict[str, object]:
    root = _parse_manifest(path)
    permissions = sorted(
        node.attrib[ANDROID_NAME]
        for node in root.findall("uses-permission")
        if node.attrib.get(ANDROID_NAME, "").startswith("android.permission.FOREGROUND_SERVICE")
    )

    services: list[dict[str, object]] = []
    application = root.find("application")
    if application is not None:
        for service in application.findall("service"):
            raw_types = service.attrib.get(ANDROID_FGS_TYPE, "")
            foreground_service_types = sorted(part for part in raw_types.split("|") if part)
            if not foreground_service_types:
                continue
            special_use_subtype = ""
            for prop in service.findall("property"):
                if prop.attrib.get(ANDROID_NAME) == SPECIAL_USE_SUBTYPE:
                    special_use_subtype = prop.attrib.get(ANDROID_VALUE, "")
                    break
            services.append(
                {
                    "name": service.attrib.get(ANDROID_NAME, ""),
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
