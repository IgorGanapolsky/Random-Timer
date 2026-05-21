#!/usr/bin/env python3
"""Report Android agent workflow readiness for this repository."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any


VERSION_KEYS = ("compileSdk", "minSdk", "targetSdk")


def _run_version(executable: str, args: list[str]) -> str:
    try:
        completed = subprocess.run(
            [executable, *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    output = "\n".join(part.strip() for part in (completed.stdout, completed.stderr) if part.strip())
    return output.splitlines()[0] if output else ""


def _tool_status(name: str, version_args: list[str]) -> dict[str, Any]:
    path = shutil.which(name)
    result: dict[str, Any] = {"available": bool(path), "path": path or ""}
    if path:
        result["version"] = _run_version(path, version_args)
    return result


def _extract_gradle_versions(build_file: Path) -> dict[str, str]:
    if not build_file.exists():
        return {}
    source = build_file.read_text(encoding="utf-8")
    versions = {}
    for key in VERSION_KEYS:
        match = re.search(rf"\b{key}\s*=\s*(\d+)", source)
        if match:
            versions[key] = match.group(1)
    return versions


def _extract_manifest_package(manifest: Path) -> str:
    if not manifest.exists():
        return ""
    source = manifest.read_text(encoding="utf-8")
    match = re.search(r'package\s*=\s*"([^"]+)"', source)
    return match.group(1) if match else "com.iganapolsky.randomtimer"


def build_report(repo_root: Path) -> dict[str, Any]:
    android_root = repo_root / "native-android"
    gradlew = android_root / "gradlew"
    manifest = android_root / "app/src/main/AndroidManifest.xml"
    build_file = android_root / "app/build.gradle.kts"

    tools = {
        "android_cli": _tool_status("android", ["--version"]),
        "adb": _tool_status("adb", ["version"]),
        "emulator": _tool_status("emulator", ["-version"]),
        "sdkmanager": _tool_status("sdkmanager", ["--version"]),
    }

    recommendations = [
        {
            "name": "Ground Android changes in current official docs",
            "when": "Before changing Android platform behavior, Play policy-sensitive code, build config, or target SDK behavior.",
            "command": "android docs search '<topic>'",
            "fallback": "Use current official Android Developers documentation if Android CLI is unavailable.",
        },
        {
            "name": "Install and refresh official Android Skills",
            "when": "Before Navigation, edge-to-edge, AGP, XML-to-Compose, R8, emulator, or release-build work.",
            "command": "android update && android skills",
            "fallback": "Follow docs/ANDROID_AGENT_WORKFLOW.md and existing repo patterns.",
        },
        {
            "name": "Use scripted local validation first",
            "when": "Before opening a release PR that touches native Android code.",
            "command": "cd native-android && ./gradlew testDebugUnitTest lint",
            "fallback": "Run the same Gradle wrapper commands directly.",
        },
        {
            "name": "Use Android CLI device automation when installed",
            "when": "For emulator smoke tests and UI reproduction loops.",
            "command": "android emulator list && android run",
            "fallback": "Use adb/emulator plus repo Gradle wrapper.",
        },
    ]

    warnings = []
    if not tools["android_cli"]["available"]:
        warnings.append("Android CLI is not installed on PATH; official docs/skills/device shortcuts are unavailable.")
    if not tools["adb"]["available"]:
        warnings.append("adb is not installed on PATH; local device/emulator verification is limited.")
    if not gradlew.exists():
        warnings.append("native-android/gradlew is missing; Android builds cannot use the repo-pinned Gradle wrapper.")

    return {
        "repo_root": str(repo_root),
        "android_root_exists": android_root.exists(),
        "gradle_wrapper_exists": gradlew.exists(),
        "manifest_exists": manifest.exists(),
        "package": _extract_manifest_package(manifest),
        "gradle_versions": _extract_gradle_versions(build_file),
        "tools": tools,
        "high_roi_recommendations": recommendations,
        "warnings": warnings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON only.")
    args = parser.parse_args(argv)

    report = build_report(args.repo_root.resolve())
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("Android agent workflow readiness")
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
