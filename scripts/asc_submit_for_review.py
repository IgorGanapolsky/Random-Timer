#!/usr/bin/env python3
"""Submit an iOS App Store version for review via App Store Connect API.

This is designed to run in CI with App Store Connect API key credentials.
It performs hard preflight checks and reads back state before reporting success.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional

APP_STORE_CONNECT_API = "https://api.appstoreconnect.apple.com/v1"


def die(msg: str, code: int = 1) -> "None":
    print(f"❌ {msg}", file=sys.stderr)
    raise SystemExit(code)


def info(msg: str) -> None:
    print(f"▸ {msg}")


def _read_private_key_material(key_id: str) -> str:
    key = (os.environ.get("APPSTORE_PRIVATE_KEY") or "").strip()
    if key:
        return key

    key_path = (os.environ.get("APPSTORE_PRIVATE_KEY_PATH") or "").strip()
    if key_path:
        return key_path

    default_key_path = os.path.expanduser(f"~/.appstoreconnect/private_keys/AuthKey_{key_id}.p8")
    if os.path.isfile(default_key_path):
        return default_key_path

    return ""


@dataclass
class ASCAuth:
    key_id: str
    issuer_id: str
    private_key: str  # raw key or file path

    @classmethod
    def from_env(cls) -> "ASCAuth":
        key_id = (os.environ.get("APPSTORE_KEY_ID") or "").strip()
        issuer_id = (os.environ.get("APPSTORE_ISSUER_ID") or "").strip()
        private_key = _read_private_key_material(key_id)
        missing = []
        if not key_id:
            missing.append("APPSTORE_KEY_ID")
        if not issuer_id:
            missing.append("APPSTORE_ISSUER_ID")
        if not private_key:
            missing.append("APPSTORE_PRIVATE_KEY (or APPSTORE_PRIVATE_KEY_PATH or ~/.appstoreconnect/private_keys/AuthKey_<KEY_ID>.p8)")
        if missing:
            die("Missing env vars: " + ", ".join(missing), code=2)
        return cls(key_id=key_id, issuer_id=issuer_id, private_key=private_key)

    def jwt(self) -> str:
        try:
            import jwt  # PyJWT
        except ImportError:
            die("Missing PyJWT. Install: pip install pyjwt cryptography", code=2)

        private_key = self.private_key
        if os.path.isfile(private_key):
            with open(private_key, "r", encoding="utf-8") as f:
                private_key = f.read()

        now = int(time.time())
        exp = now + 20 * 60
        payload = {"iss": self.issuer_id, "iat": now, "exp": exp, "aud": "appstoreconnect-v1"}
        headers = {"alg": "ES256", "kid": self.key_id, "typ": "JWT"}
        return jwt.encode(payload, private_key, algorithm="ES256", headers=headers)


class ASCClient:
    def __init__(self, auth: ASCAuth):
        self._auth = auth
        self._token = None
        self._token_exp = 0

    def _token_value(self) -> str:
        now = time.time()
        if self._token and now < self._token_exp - 30:
            return self._token
        token = self._auth.jwt()
        # Keep a conservative cache window (token exp is 20min)
        self._token = token
        self._token_exp = now + 18 * 60
        return token

    def request(self, method: str, path: str, *, params: dict | None = None, payload: dict | None = None) -> dict:
        try:
            import requests
        except ImportError:
            die("Missing requests. Install: pip install requests", code=2)

        url = f"{APP_STORE_CONNECT_API}{path}"
        headers = {
            "Authorization": f"Bearer {self._token_value()}",
            "Content-Type": "application/json",
        }
        resp = requests.request(method, url, headers=headers, params=params, json=payload, timeout=30)
        if resp.status_code >= 400:
            try:
                body = resp.json()
            except Exception:
                body = {"raw": resp.text}
            raise RuntimeError(f"{method} {path} failed: HTTP {resp.status_code} {body}")
        return resp.json() if resp.content else {}

    def get_all(self, path: str, *, params: dict | None = None) -> list[dict]:
        items: list[dict] = []
        next_path = path
        next_params = dict(params or {})
        while True:
            data = self.request("GET", next_path, params=next_params)
            items.extend(data.get("data", []))
            next_url = (data.get("links") or {}).get("next")
            if not next_url:
                break
            # next is a full URL; convert to API path+query
            if next_url.startswith(APP_STORE_CONNECT_API):
                next_url = next_url[len(APP_STORE_CONNECT_API) :]
            if "?" in next_url:
                next_path, query = next_url.split("?", 1)
                # ASC includes pagination params in the URL; just pass full query via requests by reusing next_url.
                # Simpler: call request with next_path and no params by embedding query in path.
                next_path = f"{next_path}?{query}"
                next_params = {}
            else:
                next_path = next_url
                next_params = {}
        return items


def first(items: Iterable[dict]) -> Optional[dict]:
    for i in items:
        return i
    return None


def ensure_https(url: str, label: str) -> None:
    if not url or not url.strip():
        die(f"{label} is empty")
    if not url.strip().startswith("https://"):
        die(f"{label} must start with https:// (got: {url!r})")


def get_app(client: ASCClient, bundle_id: str) -> dict:
    apps = client.get_all("/apps", params={"filter[bundleId]": bundle_id, "limit": 1})
    app = first(apps)
    if not app:
        die(f"No app found for bundleId {bundle_id!r}")
    return app


def find_or_create_app_store_version(client: ASCClient, app_id: str, version: str) -> tuple[str, str]:
    versions = client.get_all(
        f"/apps/{app_id}/appStoreVersions",
        params={
            "filter[platform]": "IOS",
            "filter[versionString]": version,
            "limit": 10,
            "fields[appStoreVersions]": "versionString,appStoreState",
        },
    )
    existing = first(versions)
    if existing:
        vid = existing["id"]
        state = (existing.get("attributes") or {}).get("appStoreState", "UNKNOWN")
        return vid, state

    info(f"Creating App Store version {version}…")
    created = client.request(
        "POST",
        "/appStoreVersions",
        payload={
            "data": {
                "type": "appStoreVersions",
                "attributes": {"platform": "IOS", "versionString": version},
                "relationships": {"app": {"data": {"type": "apps", "id": app_id}}},
            }
        },
    )
    vid = created["data"]["id"]
    state = (created["data"].get("attributes") or {}).get("appStoreState", "UNKNOWN")
    return vid, state


def get_version_localization(client: ASCClient, version_id: str, locale: str) -> dict:
    locs = client.get_all(
        f"/appStoreVersions/{version_id}/appStoreVersionLocalizations",
        params={
            "filter[locale]": locale,
            "limit": 10,
            "fields[appStoreVersionLocalizations]": "locale,description,keywords,whatsNew,promotionalText",
        },
    )
    loc = first(locs)
    if not loc:
        die(f"Missing App Store version localization for {locale}. Run fastlane metadata upload first.")
    attrs = loc.get("attributes") or {}
    for field in ("description", "keywords", "whatsNew"):
        if not (attrs.get(field) or "").strip():
            die(f"App Store version localization {locale} missing required field: {field}")
    return loc


def screenshot_counts(client: ASCClient, version_localization_id: str) -> dict[str, int]:
    sets = client.get_all(
        f"/appStoreVersionLocalizations/{version_localization_id}/appScreenshotSets",
        params={"limit": 200, "fields[appScreenshotSets]": "screenshotDisplayType"},
    )
    counts: dict[str, int] = {}
    for s in sets:
        sid = s["id"]
        display_type = (s.get("attributes") or {}).get("screenshotDisplayType", "UNKNOWN")
        shots = client.get_all(f"/appScreenshotSets/{sid}/appScreenshots", params={"limit": 200})
        counts[display_type] = len(shots)
    return counts


def verify_screenshots(counts: dict[str, int]) -> None:
    # App Store Connect provides "screenshotDisplayType" keys (e.g. APP_IPHONE_65).
    # We require large iPhone + large iPad coverage (>=3 each) to satisfy store requirements.
    # Keep this check tolerant to Apple naming variations by matching common size hints.
    iphone_hints = ("65", "6_5", "67", "6_7", "69", "6_9")
    ipad_hints = ("13", "12_9", "129")

    iphone_ok = any(
        k.startswith("APP_IPHONE_") and any(h in k for h in iphone_hints) and v >= 3
        for k, v in counts.items()
    )
    ipad_ok = any(
        k.startswith("APP_IPAD_") and any(h in k for h in ipad_hints) and v >= 3
        for k, v in counts.items()
    )

    if not iphone_ok or not ipad_ok:
        die(
            "Screenshot coverage insufficient for large device classes.\n"
            f"  Counts: {counts}\n"
            f"  Need: >=3 screenshots for one large iPhone set (hints: {iphone_hints}) AND "
            f">=3 screenshots for one large iPad set (hints: {ipad_hints})."
        )


def select_valid_build_id(client: ASCClient, app_id: str, marketing_version: str) -> str:
    # /builds can be large; page until we find a VALID build for the desired marketing version.
    # We cap the scan to a reasonable upper bound to avoid runaway API calls.
    max_builds_to_scan = 500
    scanned = 0

    next_path = "/builds"
    next_params: dict[str, Any] = {
        "filter[app]": app_id,
        "include": "preReleaseVersion",
        "sort": "-uploadedDate",
        "limit": 50,
        "fields[builds]": "version,processingState,uploadedDate,preReleaseVersion",
        "fields[preReleaseVersions]": "version",
    }

    while True:
        data = client.request("GET", next_path, params=next_params)
        pre = {}
        for item in data.get("included", []):
            if item.get("type") == "preReleaseVersions":
                pre[item["id"]] = (item.get("attributes") or {}).get("version")

        for b in data.get("data", []):
            scanned += 1
            attrs = b.get("attributes") or {}
            rel = (b.get("relationships") or {}).get("preReleaseVersion", {}).get("data") or {}
            pv = pre.get(rel.get("id"))
            if pv != marketing_version:
                continue
            if attrs.get("processingState") == "VALID":
                return b["id"]

            if scanned >= max_builds_to_scan:
                die(f"No VALID TestFlight build found for version {marketing_version} after scanning {scanned} builds.")

        if scanned >= max_builds_to_scan:
            die(f"No VALID TestFlight build found for version {marketing_version} after scanning {scanned} builds.")

        next_url = (data.get("links") or {}).get("next")
        if not next_url:
            break

        if next_url.startswith(APP_STORE_CONNECT_API):
            next_url = next_url[len(APP_STORE_CONNECT_API) :]
        # Embed ASC's next query params directly in the path for simplicity.
        next_path = next_url
        next_params = {}

    die(f"No VALID TestFlight build found for version {marketing_version}.")
    raise AssertionError("unreachable")


def attach_build(client: ASCClient, version_id: str, build_id: str) -> None:
    info(f"Attaching build {build_id} to App Store version…")
    client.request(
        "PATCH",
        f"/appStoreVersions/{version_id}/relationships/build",
        payload={"data": {"type": "builds", "id": build_id}},
    )


def verify_app_info(client: ASCClient, app_id: str, locale: str) -> None:
    # Category + URLs (support/privacy) are on app info localization.
    data = client.request(
        "GET",
        f"/apps/{app_id}/appInfos",
        params={
            "filter[platform]": "IOS",
            "include": "appInfoLocalizations,primaryCategory",
            "limit": 10,
            "fields[appInfos]": "primaryCategory",
            "fields[appInfoLocalizations]": "locale,privacyPolicyUrl,supportUrl,marketingUrl,name,subtitle",
        },
    )
    app_infos = data.get("data") or []
    if not app_infos:
        die("Missing app info (platform IOS). Complete App Information in App Store Connect.")

    app_info = app_infos[0]
    rel_primary = (app_info.get("relationships") or {}).get("primaryCategory", {}).get("data")
    if not rel_primary:
        die("Primary category is not set (App Information).")

    included = data.get("included") or []
    loc = None
    for inc in included:
        if inc.get("type") == "appInfoLocalizations" and (inc.get("attributes") or {}).get("locale") == locale:
            loc = inc
            break
    if not loc:
        die(f"Missing app info localization for {locale} (App Information).")
    attrs = loc.get("attributes") or {}
    ensure_https(attrs.get("privacyPolicyUrl", ""), "Privacy Policy URL")
    ensure_https(attrs.get("supportUrl", ""), "Support URL")


def verify_pricing(client: ASCClient, app_id: str) -> None:
    # Minimal verification: there must be at least one price and an included priceTier.
    data = client.request("GET", f"/apps/{app_id}/prices", params={"include": "priceTier", "limit": 1})
    prices = data.get("data") or []
    if not prices:
        die("Pricing not set (no prices returned for app).")
    # If included tier id is 0 => free. We don't enforce free/paid; just that it exists.
    included = data.get("included") or []
    tier = first([i for i in included if i.get("type") == "priceTiers"])
    if not tier:
        die("Pricing not set (missing priceTier include).")


def verify_review_detail(client: ASCClient, app_id: str) -> None:
    # Endpoint is singular in ASC: /apps/{id}/appStoreReviewDetail
    try:
        data = client.request("GET", f"/apps/{app_id}/appStoreReviewDetail")
    except Exception:
        # Fallback (some clients expose plural)
        data = client.request("GET", f"/apps/{app_id}/appStoreReviewDetails")
    detail = first(data.get("data") or [])
    if not detail and isinstance(data.get("data"), dict):
        detail = data["data"]
    if not detail:
        die("App Review contact info missing (appStoreReviewDetail not found).")
    attrs = detail.get("attributes") or {}
    if not (attrs.get("contactEmail") or "").strip():
        die("App Review contactEmail is missing.")
    if not (attrs.get("contactPhone") or "").strip():
        die("App Review contactPhone is missing.")


def verify_age_rating(client: ASCClient, app_id: str) -> None:
    # Try both known endpoints; pass if either returns a declaration object.
    for path in (f"/apps/{app_id}/appInfoAgeRatingDeclaration", f"/apps/{app_id}/appStoreAgeRatingDeclaration"):
        try:
            data = client.request("GET", path)
        except Exception:
            continue
        decl = data.get("data")
        if decl:
            return
    die("Age Rating declaration not found. Complete Age Rating in App Store Connect.")


def submit_for_review(client: ASCClient, version_id: str) -> None:
    info("Creating App Store version submission…")
    client.request(
        "POST",
        "/appStoreVersionSubmissions",
        payload={
            "data": {
                "type": "appStoreVersionSubmissions",
                "relationships": {"appStoreVersion": {"data": {"type": "appStoreVersions", "id": version_id}}},
            }
        },
    )


def get_version_state(client: ASCClient, version_id: str) -> str:
    data = client.request(
        "GET",
        f"/appStoreVersions/{version_id}",
        params={"fields[appStoreVersions]": "versionString,appStoreState"},
    )
    attrs = (data.get("data") or {}).get("attributes") or {}
    return attrs.get("appStoreState", "UNKNOWN")


def wait_for_state(client: ASCClient, version_id: str, *, timeout: int, poll_interval: int) -> str:
    deadline = time.time() + timeout
    while True:
        state = get_version_state(client, version_id)
        info(f"App Store version state: {state}")
        if state in ("WAITING_FOR_REVIEW", "IN_REVIEW", "PENDING_DEVELOPER_RELEASE", "READY_FOR_SALE"):
            return state
        if state in ("REJECTED", "DEVELOPER_REJECTED", "INVALID_BINARY", "METADATA_REJECTED", "REMOVED_FROM_SALE"):
            die(f"Submission entered a terminal failure state: {state}")
        if time.time() >= deadline:
            die(f"Timed out waiting for submitted state; last state={state}")
        time.sleep(poll_interval)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Submit an App Store version for review (App Store Connect API).")
    p.add_argument("--bundle-id", default="com.igorganapolsky.randomtimer")
    p.add_argument("--version", required=True, help="CFBundleShortVersionString to submit (e.g. 1.1.0).")
    p.add_argument("--locale", default="en-US")
    p.add_argument("--dry-run", action="store_true", help="Run preflight only; do not attach/submit.")
    p.add_argument("--wait", action="store_true", help="Wait and read back submitted state.")
    p.add_argument("--timeout", type=int, default=900)
    p.add_argument("--poll-interval", type=int, default=20)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    auth = ASCAuth.from_env()
    client = ASCClient(auth)

    app = get_app(client, args.bundle_id)
    app_id = app["id"]
    info(f"App: {args.bundle_id} (id={app_id})")

    # Hard preflight checks (fail fast if store listing is incomplete).
    verify_app_info(client, app_id, args.locale)
    verify_pricing(client, app_id)
    verify_review_detail(client, app_id)
    verify_age_rating(client, app_id)

    version_id, state = find_or_create_app_store_version(client, app_id, args.version)
    info(f"App Store version id={version_id} state={state}")

    # If already in a submitted/in-review state, do nothing.
    if state in ("WAITING_FOR_REVIEW", "IN_REVIEW", "PENDING_DEVELOPER_RELEASE", "READY_FOR_SALE"):
        info(f"Already submitted: {state}")
        return 0

    loc = get_version_localization(client, version_id, args.locale)
    loc_id = loc["id"]

    counts = screenshot_counts(client, loc_id)
    info(f"Screenshot counts: {counts}")
    verify_screenshots(counts)

    if args.dry_run:
        info("Dry-run mode: preflight passed; skipping build attach + submission.")
        return 0

    build_id = select_valid_build_id(client, app_id, args.version)
    attach_build(client, version_id, build_id)
    submit_for_review(client, version_id)

    if args.wait:
        wait_for_state(client, version_id, timeout=args.timeout, poll_interval=args.poll_interval)

    info("Submit-for-review request sent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
