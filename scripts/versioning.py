#!/usr/bin/env python3
"""Mobile version parsing/updating helpers (iOS + Android).

This repo keeps the release SemVer in:
  - Android: native-android/app/build.gradle.kts (versionName)
  - iOS: native-ios/RandomTimer.xcodeproj/project.pbxproj (MARKETING_VERSION)

Build numbers:
  - Android: versionCode (monotonic integer)
  - iOS: CURRENT_PROJECT_VERSION (monotonic integer)
"""

from __future__ import annotations

import dataclasses
import re
from pathlib import Path


SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
)


@dataclasses.dataclass(frozen=True)
class MobileVersions:
    version: str
    android_version_code: int
    ios_build_number: int


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def parse_android_build_gradle_kts(path: Path) -> tuple[str, int]:
    """Return (versionName, versionCode) from build.gradle.kts."""
    text = _read_text(path)
    m_name = re.search(r'^\s*versionName\s*=\s*"([^"]+)"\s*$', text, flags=re.MULTILINE)
    m_code = re.search(r"^\s*versionCode\s*=\s*(\d+)\s*$", text, flags=re.MULTILINE)
    if not m_name or not m_code:
        raise ValueError(f"Could not parse versionName/versionCode from {path}")
    return m_name.group(1).strip(), int(m_code.group(1))


def update_android_build_gradle_kts(path: Path, *, version: str, version_code: int) -> None:
    """Update versionName/versionCode in build.gradle.kts."""
    if not SEMVER_RE.match(version):
        raise ValueError(f"Invalid SemVer: {version}")
    if version_code <= 0:
        raise ValueError("version_code must be > 0")

    text = _read_text(path)
    text2, n1 = re.subn(
        r'(^\s*versionName\s*=\s*")([^"]+)("\s*$)',
        rf'\g<1>{version}\g<3>',
        text,
        flags=re.MULTILINE,
    )
    text3, n2 = re.subn(
        r"(^\s*versionCode\s*=\s*)(\d+)(\s*$)",
        rf"\g<1>{version_code}\g<3>",
        text2,
        flags=re.MULTILINE,
    )
    if n1 == 0 or n2 == 0:
        raise ValueError(f"Failed to update versionName/versionCode in {path}")
    _write_text(path, text3)


def parse_ios_pbxproj(path: Path) -> tuple[str, int]:
    """Return (MARKETING_VERSION, CURRENT_PROJECT_VERSION) from project.pbxproj.

    The pbxproj can contain multiple MARKETING_VERSION entries; they should match.
    """
    text = _read_text(path)
    versions = re.findall(r"^\s*MARKETING_VERSION\s*=\s*([0-9A-Za-z.+-]+);\s*$", text, flags=re.MULTILINE)
    builds = re.findall(r"^\s*CURRENT_PROJECT_VERSION\s*=\s*(\d+);\s*$", text, flags=re.MULTILINE)
    if not versions or not builds:
        raise ValueError(f"Could not parse MARKETING_VERSION/CURRENT_PROJECT_VERSION from {path}")

    v0 = versions[0].strip()
    if any(v.strip() != v0 for v in versions):
        raise ValueError(f"MARKETING_VERSION is inconsistent in {path}: {sorted(set(versions))}")
    b0 = int(builds[0])
    if any(int(b) != b0 for b in builds):
        raise ValueError(f"CURRENT_PROJECT_VERSION is inconsistent in {path}: {sorted(set(builds))}")
    return v0, b0


def update_ios_pbxproj(path: Path, *, version: str, build_number: int) -> None:
    """Update MARKETING_VERSION + CURRENT_PROJECT_VERSION everywhere in pbxproj."""
    if not SEMVER_RE.match(version):
        raise ValueError(f"Invalid SemVer: {version}")
    if build_number <= 0:
        raise ValueError("build_number must be > 0")

    text = _read_text(path)
    text2, n1 = re.subn(
        r"(^\s*MARKETING_VERSION\s*=\s*)([0-9A-Za-z.+-]+)(;\s*$)",
        rf"\g<1>{version}\g<3>",
        text,
        flags=re.MULTILINE,
    )
    text3, n2 = re.subn(
        r"(^\s*CURRENT_PROJECT_VERSION\s*=\s*)(\d+)(;\s*$)",
        rf"\g<1>{build_number}\g<3>",
        text2,
        flags=re.MULTILINE,
    )
    if n1 == 0 or n2 == 0:
        raise ValueError(f"Failed to update MARKETING_VERSION/CURRENT_PROJECT_VERSION in {path}")
    _write_text(path, text3)


def read_repo_versions(repo_root: Path) -> MobileVersions:
    android_path = repo_root / "native-android/app/build.gradle.kts"
    ios_path = repo_root / "native-ios/RandomTimer.xcodeproj/project.pbxproj"
    android_version, android_code = parse_android_build_gradle_kts(android_path)
    ios_version, ios_build = parse_ios_pbxproj(ios_path)
    if android_version != ios_version:
        raise ValueError(
            "Android versionName and iOS MARKETING_VERSION differ: "
            f"{android_version} vs {ios_version}"
        )
    if not SEMVER_RE.match(android_version):
        raise ValueError(f"Invalid SemVer in repo: {android_version}")
    return MobileVersions(
        version=android_version,
        android_version_code=android_code,
        ios_build_number=ios_build,
    )


def bump_semver(version: str, part: str) -> str:
    if not SEMVER_RE.match(version):
        raise ValueError(f"Invalid SemVer: {version}")
    major_s, minor_s, patch_s = version.split(".", 2)
    major = int(major_s)
    minor = int(minor_s)
    patch = int(patch_s.split("-", 1)[0].split("+", 1)[0])

    if part == "major":
        major += 1
        minor = 0
        patch = 0
    elif part == "minor":
        minor += 1
        patch = 0
    elif part == "patch":
        patch += 1
    else:
        raise ValueError("part must be one of: major, minor, patch")
    return f"{major}.{minor}.{patch}"

