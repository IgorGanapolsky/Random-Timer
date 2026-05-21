#!/usr/bin/env python3
"""Verify public App Store and Google Play versions by storefront read-back.

Expected versions default to the **latest GitHub release tag** (not repo marketing
versions on integration branches). Override with ``--expected-version`` or
``--expected-source repo`` when comparing storefronts to checked-out sources.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import verify_play_public_listing as play

DEFAULT_IOS_APP_ID = "6758355312"
DEFAULT_ANDROID_PACKAGE = "com.iganapolsky.randomtimer"
DEFAULT_COUNTRY = "US"
DEFAULT_TIMEOUT = 900
DEFAULT_POLL_INTERVAL = 60


@dataclass
class StoreVersionResult:
    platform: str
    passed: bool
    status: str
    url: str
    expected_version: str
    observed_version: str
    details: str


def read_ios_version(repo_root: Path = ROOT) -> str:
    project = repo_root / "native-ios/RandomTimer.xcodeproj/project.pbxproj"
    text = project.read_text(encoding="utf-8")
    versions = set(re.findall(r"MARKETING_VERSION\s*=\s*([0-9]+(?:\.[0-9]+)+);", text))
    if not versions:
        raise RuntimeError(f"Could not read MARKETING_VERSION from {project}")
    if len(versions) != 1:
        raise RuntimeError(f"Multiple iOS MARKETING_VERSION values found: {sorted(versions)}")
    return versions.pop()


def read_android_version(repo_root: Path = ROOT) -> str:
    gradle = repo_root / "native-android/app/build.gradle.kts"
    text = gradle.read_text(encoding="utf-8")
    match = re.search(r'versionName\s*=\s*"([^"]+)"', text)
    if not match:
        raise RuntimeError(f"Could not read versionName from {gradle}")
    return match.group(1)


def read_github_latest_release_version(repo_root: Path = ROOT) -> str:
    """Return X.Y.Z from ``gh release view`` for the repo at ``repo_root``."""
    try:
        proc = subprocess.run(
            ["gh", "release", "view", "--json", "tagName"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
            timeout=120,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "gh CLI is required for --expected-source github_latest_release "
            "(install GitHub CLI and authenticate, e.g. gh auth login)"
        ) from exc
    except subprocess.CalledProcessError as exc:
        err = (exc.stderr or exc.stdout or "").strip() or str(exc)
        raise RuntimeError(f"gh release view failed: {err}") from exc

    data = json.loads(proc.stdout)
    tag = str(data.get("tagName") or "").strip()
    if not tag:
        raise RuntimeError("gh release view returned empty tagName (no GitHub release?)")

    version = tag[1:] if tag.startswith("v") else tag
    if not re.fullmatch(r"\d+(?:\.\d+)+", version):
        raise RuntimeError(f"Unexpected release tag format: {tag!r} -> {version!r}")
    return version


def _fill_missing_expected_from_repo(
    platform: str, ios: str, android: str, repo_root: Path
) -> tuple[str, str]:
    if platform in {"ios", "both"} and not ios:
        ios = read_ios_version(repo_root)
    if platform in {"android", "both"} and not android:
        android = read_android_version(repo_root)
    return ios, android


def _expected_from_repo_sources(platform: str, repo_root: Path) -> tuple[str, str]:
    ios = read_ios_version(repo_root) if platform in {"ios", "both"} else ""
    android = read_android_version(repo_root) if platform in {"android", "both"} else ""
    return ios, android


def _expected_from_shared_release(platform: str, shared: str) -> tuple[str, str]:
    ios = shared if platform in {"ios", "both"} else ""
    android = shared if platform in {"android", "both"} else ""
    return ios, android


def resolve_expected_versions(
    *,
    platform: str,
    expected_version: str,
    ios_expected_version: str,
    android_expected_version: str,
    expected_source: str,
    repo_root: Path,
) -> tuple[str, str, str]:
    """Return (ios_expected, android_expected, evidence_label)."""
    ios = ios_expected_version or expected_version
    android = android_expected_version or expected_version
    explicit_any = bool(expected_version or ios_expected_version or android_expected_version)

    if explicit_any:
        ios, android = _fill_missing_expected_from_repo(platform, ios, android, repo_root)
        return ios, android, "explicit_cli"

    if expected_source == "repo":
        ios, android = _expected_from_repo_sources(platform, repo_root)
        return ios, android, "repo_sources"

    shared = read_github_latest_release_version(repo_root)
    ios, android = _expected_from_shared_release(platform, shared)
    return ios, android, "github_latest_release"


def build_app_store_lookup_url(app_id: str, country: str) -> str:
    normalized = (country or DEFAULT_COUNTRY).strip().upper()
    return f"https://itunes.apple.com/lookup?id={app_id}&country={normalized}"


def verify_app_store_public_version(
    app_id: str,
    expected_version: str,
    country: str = DEFAULT_COUNTRY,
) -> StoreVersionResult:
    url = build_app_store_lookup_url(app_id, country)
    try:
        response = requests.get(
            url,
            timeout=30,
            headers={"User-Agent": "Random-Timer-Store-Version-Readback/1.0"},
        )
    except requests.RequestException as exc:
        return StoreVersionResult("ios", False, "ERROR", url, expected_version, "", str(exc))

    date_header = response.headers.get("date", "unknown")
    if response.status_code != 200:
        return StoreVersionResult(
            "ios",
            False,
            f"HTTP_{response.status_code}",
            url,
            expected_version,
            "",
            f"HTTP {response.status_code} on {date_header}",
        )

    try:
        payload = response.json()
    except ValueError as exc:
        return StoreVersionResult("ios", False, "INVALID_JSON", url, expected_version, "", str(exc))

    results = payload.get("results") or []
    if not results:
        return StoreVersionResult(
            "ios",
            False,
            "NOT_FOUND",
            url,
            expected_version,
            "",
            f"No App Store result on {date_header}",
        )

    item = results[0]
    observed = str(item.get("version") or "")
    release_date = str(item.get("currentVersionReleaseDate") or "unknown")
    details = (
        f"HTTP 200 on {date_header} public_version={observed} release_date={release_date} "
        "ios_semantics=itunes_lookup_public_version_field_not_App_Store_Connect_ground_truth"
    )
    if observed != expected_version:
        return StoreVersionResult(
            "ios",
            False,
            "VERSION_MISMATCH",
            url,
            expected_version,
            observed,
            details,
        )
    return StoreVersionResult("ios", True, "PUBLIC", url, expected_version, observed, details)


def verify_play_public_version(
    package: str,
    expected_version: str,
    country: str = DEFAULT_COUNTRY,
) -> StoreVersionResult:
    url = play.build_store_url(package, country)
    result = play.verify_public_listing(url, expected_version=expected_version)
    observed = ""
    match = re.search(r"public_version=([0-9]+(?:\.[0-9]+)+)", result.details)
    if match:
        observed = match.group(1)
    return StoreVersionResult(
        "android",
        result.passed,
        result.status,
        url,
        expected_version,
        observed,
        result.details,
    )


def poll_until_public(
    verify_once,
    timeout: int,
    poll_interval: int,
) -> list[StoreVersionResult]:
    deadline = time.time() + timeout
    latest: list[StoreVersionResult] = []

    while True:
        latest = verify_once()
        if all(item.passed for item in latest):
            return latest

        remaining = deadline - time.time()
        if remaining <= 0:
            timed_out: list[StoreVersionResult] = []
            for item in latest:
                if item.passed:
                    timed_out.append(item)
                else:
                    timed_out.append(
                        StoreVersionResult(
                            item.platform,
                            False,
                            item.status if item.status == "VERSION_MISMATCH" else "TIMEOUT",
                            item.url,
                            item.expected_version,
                            item.observed_version,
                            f"{item.details} (timed out after {timeout}s)",
                        )
                    )
            return timed_out

        time.sleep(min(poll_interval, max(0, remaining)))


def print_results(results: list[StoreVersionResult], expected_source_label: str) -> bool:
    print()
    print("== Public Store Version Read-Back ==")
    print(f"expected_source: {expected_source_label}")
    all_passed = True
    for item in results:
        marker = "PASS" if item.passed else "FAIL"
        all_passed = all_passed and item.passed
        print(f"{marker} {item.platform}: status={item.status}")
        print(f"  url: {item.url}")
        print(f"  expected_version: {item.expected_version}")
        print(f"  observed_version: {item.observed_version or 'unknown'}")
        print(f"  details: {item.details}")
    print("====================================")
    print()
    return all_passed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", choices=["ios", "android", "both"], default="both")
    parser.add_argument("--expected-version", default="", help="Expected public version for both stores")
    parser.add_argument("--ios-expected-version", default="", help="Override expected iOS version")
    parser.add_argument("--android-expected-version", default="", help="Override expected Android version")
    parser.add_argument(
        "--expected-source",
        choices=["github_latest_release", "repo"],
        default="github_latest_release",
        help=(
            "Where to read expected versions when --expected-version is not set: "
            "latest GitHub release tag (default) or native repo versionName/MARKETING_VERSION."
        ),
    )
    parser.add_argument("--ios-app-id", default=DEFAULT_IOS_APP_ID)
    parser.add_argument("--android-package", default=DEFAULT_ANDROID_PACKAGE)
    parser.add_argument("--country", default=DEFAULT_COUNTRY)
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--poll-interval", type=int, default=DEFAULT_POLL_INTERVAL)
    parser.add_argument("--json-out", default="", help="Optional path for JSON evidence output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ios_expected, android_expected, expected_source_label = resolve_expected_versions(
        platform=args.platform,
        expected_version=args.expected_version,
        ios_expected_version=args.ios_expected_version,
        android_expected_version=args.android_expected_version,
        expected_source=args.expected_source,
        repo_root=ROOT,
    )

    def verify_once() -> list[StoreVersionResult]:
        checks: list[StoreVersionResult] = []
        if args.platform in {"ios", "both"}:
            checks.append(
                verify_app_store_public_version(
                    args.ios_app_id,
                    ios_expected,
                    country=args.country,
                )
            )
        if args.platform in {"android", "both"}:
            checks.append(
                verify_play_public_version(
                    args.android_package,
                    android_expected,
                    country=args.country,
                )
            )
        return checks

    results = poll_until_public(verify_once, args.timeout, args.poll_interval)
    passed = print_results(results, expected_source_label)

    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(
                {
                    "passed": passed,
                    "expected_source": expected_source_label,
                    "results": [asdict(item) for item in results],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
