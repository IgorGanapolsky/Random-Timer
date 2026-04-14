#!/usr/bin/env python3
"""Verify that a Google Play app listing is publicly visible."""

from __future__ import annotations

import argparse
import re
import sys
import time
from dataclasses import dataclass

import requests


DEFAULT_TIMEOUT = 900
DEFAULT_POLL_INTERVAL = 60


@dataclass
class PublicListingResult:
    passed: bool
    status: str
    details: str


def build_store_url(package: str, country: str) -> str:
    normalized = (country or "US").strip().upper()
    return f"https://play.google.com/store/apps/details?id={package}&hl=en_{normalized}&gl={normalized}"


def extract_displayed_version(page_html: str) -> str | None:
    patterns = (
        r'"141":\[\[\["([^"]+)"\]\]',
        r'\[\[\["([0-9]+\.[0-9]+\.[0-9]+)"\]\],\[\[\[[0-9]+\]\],\[\[\[[0-9]+,"[0-9.]+"\]\]\]\]',
    )
    for pattern in patterns:
        match = re.search(pattern, page_html, re.S)
        if match:
            return match.group(1)
    return None


def verify_public_listing(url: str, expected_version: str = "") -> PublicListingResult:
    try:
        response = requests.get(
            url,
            allow_redirects=True,
            timeout=30,
            headers={"User-Agent": "Random-Timer-Release-Verification/1.0"},
        )
    except requests.RequestException as exc:
        return PublicListingResult(False, "ERROR", f"Play public listing request failed: {exc}")

    status = response.status_code
    date_header = response.headers.get("date", "unknown")
    if status == 200:
        observed_version = extract_displayed_version(response.text)
        details = [f"HTTP 200 on {date_header}"]
        if observed_version:
            details.append(f"public_version={observed_version}")
        if expected_version:
            details.append(f"expected_version={expected_version}")
            if not observed_version:
                return PublicListingResult(
                    False,
                    "VERSION_UNPARSEABLE",
                    " ".join(details + ["but could not extract public version from Play HTML"]),
                )
            if observed_version != expected_version:
                return PublicListingResult(
                    False,
                    "VERSION_MISMATCH",
                    " ".join(details),
                )
        return PublicListingResult(True, "PUBLIC", " ".join(details))
    return PublicListingResult(False, f"HTTP_{status}", f"HTTP {status} on {date_header}")


def poll_until_visible(
    url: str,
    timeout: int,
    poll_interval: int,
    expected_version: str = "",
) -> PublicListingResult:
    deadline = time.time() + timeout

    while True:
        result = verify_public_listing(url, expected_version=expected_version)
        if result.passed:
            return result

        remaining = deadline - time.time()
        if remaining <= 0:
            terminal_status = result.status if result.status not in {"HTTP_404", "HTTP_403", "HTTP_500"} else "TIMEOUT"
            return PublicListingResult(
                False,
                terminal_status,
                f"{result.details} (timed out after {timeout}s)",
            )

        time.sleep(min(poll_interval, max(0, remaining)))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify that the Google Play public listing is visible."
    )
    parser.add_argument("--package", required=True, help="Android package name")
    parser.add_argument("--country", default="US", help="Two-letter storefront country code")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--poll-interval", type=int, default=DEFAULT_POLL_INTERVAL)
    parser.add_argument(
        "--url",
        help="Explicit store URL. If omitted, generated from --package and --country.",
    )
    parser.add_argument(
        "--expected-version",
        default="",
        help="Require the public Play page to show this app version before passing.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    url = args.url or build_store_url(args.package, args.country)
    result = poll_until_visible(
        url,
        timeout=args.timeout,
        poll_interval=args.poll_interval,
        expected_version=args.expected_version,
    )

    print()
    print("══ Play Public Listing Verification ═════════════════")
    print(f"URL:    {url}")
    print(f"Status: {result.status}")
    print(f"Detail: {result.details}")
    print("══════════════════════════════════════════════════════")
    print()

    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
