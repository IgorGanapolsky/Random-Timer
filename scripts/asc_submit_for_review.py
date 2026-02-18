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

FASTLANE_METADATA_DIR = os.path.join("native-ios", "fastlane", "metadata")


def die(msg: str, code: int = 1) -> "None":
    print(f"❌ {msg}", file=sys.stderr)
    raise SystemExit(code)


def info(msg: str) -> None:
    print(f"▸ {msg}")


def _read_text_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""


def resolve_metadata_url(*, locale: str, kind: str) -> str:
    """Resolve a URL from env override or fastlane metadata file.

    kind: "support_url" | "privacy_url" | "marketing_url"
    """
    env_key = {
        "support_url": "ASC_SUPPORT_URL",
        "privacy_url": "ASC_PRIVACY_URL",
        "marketing_url": "ASC_MARKETING_URL",
    }.get(kind)
    if not env_key:
        return ""

    env_val = (os.environ.get(env_key) or "").strip()
    if env_val:
        return env_val

    path = os.path.join(FASTLANE_METADATA_DIR, locale, f"{kind}.txt")
    return _read_text_file(path)


def _get_url(attrs: dict[str, Any], *keys: str) -> str:
    for key in keys:
        val = (attrs.get(key) or "").strip()
        if val:
            return val
    return ""


def _is_unknown_attr_error(exc: Exception, *, attr_key: str) -> bool:
    msg = str(exc)
    return ("ATTRIBUTE.UNKNOWN" in msg) and (f"/data/attributes/{attr_key}" in msg or f"'{attr_key}'" in msg)


def patch_resource_attributes(client: "ASCClient", *, path: str, type_name: str, resource_id: str, attrs: dict) -> None:
    client.request(
        "PATCH",
        path,
        payload={
            "data": {
                "type": type_name,
                "id": resource_id,
                "attributes": attrs,
            }
        },
    )


def _patch_first_supported_attr(
    client: "ASCClient",
    *,
    path: str,
    type_name: str,
    resource_id: str,
    attrs: dict[str, Any],
    desired: dict[str, str],
    candidates: list[str],
) -> dict[str, Any]:
    """Try to PATCH using the first attribute key supported by ASC's current schema.

    We prefer keys present in the current attributes payload; otherwise we attempt each candidate
    key and continue on ATTRIBUTE.UNKNOWN errors.
    """
    # Prefer keys that already exist in the schema payload.
    for key in candidates:
        if key in attrs and desired.get(key):
            patch_resource_attributes(client, path=path, type_name=type_name, resource_id=resource_id, attrs={key: desired[key]})
            refreshed = client.request("GET", path).get("data") or {}
            return (refreshed.get("attributes") or {}) if isinstance(refreshed, dict) else attrs

    # Otherwise, probe each candidate.
    for key in candidates:
        val = desired.get(key)
        if not val:
            continue
        try:
            patch_resource_attributes(client, path=path, type_name=type_name, resource_id=resource_id, attrs={key: val})
            refreshed = client.request("GET", path).get("data") or {}
            return (refreshed.get("attributes") or {}) if isinstance(refreshed, dict) else attrs
        except Exception as e:
            if _is_unknown_attr_error(e, attr_key=key):
                continue
            raise

    return attrs


def ensure_app_info_urls(client: "ASCClient", *, loc_id: str, locale: str, attrs: dict[str, Any]) -> dict[str, Any]:
    """Ensure support/privacy URLs are set on the App Info localization.

    If missing, try to fill from env/fastlane metadata and read back.
    """
    desired_support = resolve_metadata_url(locale=locale, kind="support_url")
    desired_privacy = resolve_metadata_url(locale=locale, kind="privacy_url")

    support_val = _get_url(attrs, "supportUrl", "supportURL")
    privacy_val = _get_url(attrs, "privacyPolicyUrl", "privacyPolicyURL")

    desired: dict[str, str] = {}
    if not support_val and desired_support:
        desired["supportURL"] = desired_support
        desired["supportUrl"] = desired_support
    if not privacy_val and desired_privacy:
        desired["privacyPolicyUrl"] = desired_privacy
        desired["privacyPolicyURL"] = desired_privacy

    keys = []
    if not support_val and desired_support:
        keys.append("support")
    if not privacy_val and desired_privacy:
        keys.append("privacy")

    if keys:
        info(f"Filling missing App Info URL fields for {locale}: {', '.join(keys)}")
        try:
            updated = _patch_first_supported_attr(
                client,
                path=f"/appInfoLocalizations/{loc_id}",
                type_name="appInfoLocalizations",
                resource_id=loc_id,
                attrs=attrs,
                desired=desired,
                candidates=["supportURL", "supportUrl", "privacyPolicyUrl", "privacyPolicyURL"],
            )
            # Preserve the resolved values even if ASC uses different key casing.
            if desired_support and not _get_url(updated, "supportUrl", "supportURL"):
                updated["supportURL"] = desired_support
            if desired_privacy and not _get_url(updated, "privacyPolicyUrl", "privacyPolicyURL"):
                updated["privacyPolicyUrl"] = desired_privacy
            return updated
        except Exception as e:
            die(f"Failed to update App Info URLs for locale {locale}: {e}")

    return attrs

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

def verify_app_info(client: ASCClient, app_id: str, locale: str) -> dict[str, Any]:
    # App Info holds category + localized strings/URLs like privacy policy/support URL.
    #
    # ASC API query params and field names can shift over time; keep this request
    # conservative (no schema-fragile filters/fields) and validate required values
    # from the returned objects.
    data = client.request(
        "GET",
        f"/apps/{app_id}/appInfos",
        params={
            "include": "appInfoLocalizations,primaryCategory",
            "limit": 50,
        },
    )

    app_infos = data.get("data") or []
    if not app_infos:
        die("Missing app info. Complete App Information in App Store Connect.")

    # Prefer the iOS appInfo if multiple platforms exist; otherwise fall back to first dict.
    app_info: dict[str, Any] | None = None
    for ai in app_infos:
        if not isinstance(ai, dict):
            continue
        if (ai.get("attributes") or {}).get("platform") == "IOS":
            app_info = ai
            break
    if not app_info:
        for ai in app_infos:
            if isinstance(ai, dict):
                app_info = ai
                break
    if not app_info:
        die("Missing app info object. Complete App Information in App Store Connect.")

    rel_primary = (app_info.get("relationships") or {}).get("primaryCategory", {}).get("data")
    if not rel_primary:
        die("Primary category is not set (App Information).")

    rel_loc_ids: set[str] = set()
    rel_locs = (app_info.get("relationships") or {}).get("appInfoLocalizations", {}).get("data") or []
    for item in rel_locs:
        if isinstance(item, dict):
            loc_id = item.get("id")
            if isinstance(loc_id, str) and loc_id:
                rel_loc_ids.add(loc_id)

    included = data.get("included") or []
    loc: dict[str, Any] | None = None
    for inc in included:
        if not isinstance(inc, dict) or inc.get("type") != "appInfoLocalizations":
            continue
        if rel_loc_ids and inc.get("id") not in rel_loc_ids:
            continue
        if (inc.get("attributes") or {}).get("locale") == locale:
            loc = inc
            break
    # Fallback: if relationship IDs didn't match (or weren't present), relax to any included locale.
    if not loc:
        for inc in included:
            if not isinstance(inc, dict) or inc.get("type") != "appInfoLocalizations":
                continue
            if (inc.get("attributes") or {}).get("locale") == locale:
                loc = inc
                break
    if not loc:
        die(f"Missing app info localization for {locale} (App Information).")

    loc_id = str(loc.get("id") or "").strip()
    if not loc_id:
        die(f"Missing app info localization id for {locale} (App Information).")

    loc_attrs = loc.get("attributes") or {}
    info_attrs = app_info.get("attributes") or {}
    loc_attrs = ensure_app_info_urls(client, loc_id=loc_id, locale=locale, attrs=loc_attrs)
    privacy = _get_url(loc_attrs, "privacyPolicyUrl", "privacyPolicyURL") or _get_url(info_attrs, "privacyPolicyUrl", "privacyPolicyURL")
    support = _get_url(loc_attrs, "supportUrl", "supportURL") or _get_url(info_attrs, "supportUrl", "supportURL")
    ensure_https(privacy, "Privacy Policy URL")
    ensure_https(support, "Support URL")

    # Return localization-like attrs with resolved URLs for downstream checks.
    resolved = dict(loc_attrs)
    if privacy and not resolved.get("privacyPolicyUrl"):
        resolved["privacyPolicyUrl"] = privacy
    if support and not _get_url(resolved, "supportUrl", "supportURL"):
        resolved["supportURL"] = support
    return resolved


def verify_pricing(client: ASCClient, app_id: str) -> None:
    # Pricing must be configured (free or paid) before submission. ASC exposes this
    # via either the legacy /apps/{id}/prices relationship or the newer AppPriceSchedule model.
    #
    # Strategy:
    # 1. If legacy /apps/{id}/prices exists and returns data -> OK
    # 2. If an appPriceSchedule exists and has manualPrices/automaticPrices -> OK
    # 3. If no pricing is found, attempt to create a Free price schedule (tier 0) so submission
    #    isn't blocked, then read back to verify.

    # Legacy API: prices relationship on app (older accounts).
    try:
        legacy = client.request("GET", f"/apps/{app_id}/prices", params={"include": "priceTier", "limit": 1})
        if legacy.get("data"):
            return
    except Exception:
        legacy = None

    schedule: dict[str, Any] | None = None
    schedule_id: str | None = None
    base_territory_id: str | None = None

    # Current API: some accounts expose a singular schedule relationship off the app.
    try:
        data = client.request(
            "GET",
            f"/apps/{app_id}/appPriceSchedule",
            params={"include": "baseTerritory", "limit": 10},
        )
        candidate = data.get("data")
        if isinstance(candidate, dict) and candidate.get("id"):
            schedule = candidate
    except Exception:
        schedule = None

    # Common API: schedules are top-level resources filtered by app.
    if not schedule:
        try:
            data = client.request(
                "GET",
                "/appPriceSchedules",
                params={"filter[app]": app_id, "include": "baseTerritory", "limit": 10},
            )
            schedule_list = data.get("data") or []
            for item in schedule_list:
                if isinstance(item, dict) and item.get("id"):
                    schedule = item
                    break
        except Exception:
            schedule = None

    if schedule and schedule.get("id"):
        schedule_id = schedule["id"]
        rel_base = (schedule.get("relationships") or {}).get("baseTerritory", {}).get("data")
        if isinstance(rel_base, dict):
            base_territory_id = rel_base.get("id")

        # Confirm there is at least one price entry, either manual or automatic.
        manual_err = None
        automatic_err = None
        try:
            manual = client.request("GET", f"/appPriceSchedules/{schedule_id}/manualPrices", params={"limit": 1}).get(
                "data"
            )
        except Exception as e:
            manual = None
            manual_err = str(e)
        if manual:
            return

        try:
            automatic = client.request(
                "GET", f"/appPriceSchedules/{schedule_id}/automaticPrices", params={"limit": 1}
            ).get("data")
        except Exception as e:
            automatic = None
            automatic_err = str(e)
        if automatic:
            return

        if manual_err is not None or automatic_err is not None:
            info(
                "Could not verify pricing via appPriceSchedule endpoints; attempting to create Free pricing.\n"
                f"  manualPrices error: {manual_err}\n"
                f"  automaticPrices error: {automatic_err}"
            )

    territory = (base_territory_id or "USA").strip() or "USA"

    # Find a "free" price point.
    free_point_id: str | None = None
    try:
        points = client.request(
            "GET",
            f"/apps/{app_id}/appPricePoints",
            params={"filter[territory]": territory, "limit": 200},
        )
        for item in points.get("data") or []:
            if not isinstance(item, dict):
                continue
            attrs = item.get("attributes") or {}
            price = str(attrs.get("customerPrice") or "").strip()
            if price in ("0", "0.0", "0.00", "0.000", "0.0000"):
                free_point_id = item.get("id")
                break
    except Exception:
        free_point_id = None

    if not free_point_id:
        die("Pricing not set (could not find Free price point and legacy /prices is unavailable).")

    info(f"Pricing not set; creating Free price schedule (base territory {territory})…")
    # Inline creation IDs must be local IDs in the form '${local-id}'.
    manual_price_id = "${manualPrice0}"
    payload = {
        "data": {
            "type": "appPriceSchedules",
            "relationships": {
                "app": {"data": {"type": "apps", "id": app_id}},
                "baseTerritory": {"data": {"type": "territories", "id": territory}},
                "manualPrices": {"data": [{"type": "appPrices", "id": manual_price_id}]},
            },
        },
        "included": [
            {
                "type": "appPrices",
                "id": manual_price_id,
                "attributes": {"startDate": None},
                "relationships": {"appPricePoint": {"data": {"type": "appPricePoints", "id": free_point_id}}},
            }
        ],
    }
    created_schedule_id: str | None = None
    try:
        created = client.request("POST", "/appPriceSchedules", payload=payload)
        if isinstance(created, dict):
            data = created.get("data")
            if isinstance(data, dict):
                created_schedule_id = data.get("id")
    except Exception as e:
        die(f"Pricing not set and failed to create Free price schedule: {e}")

    # Read-back verification: prefer direct GET by id (list filtering can be eventually consistent).
    if created_schedule_id:
        for _ in range(6):
            try:
                created_obj = client.request("GET", f"/appPriceSchedules/{created_schedule_id}")
                if (created_obj.get("data") or {}).get("id") == created_schedule_id:
                    return
            except Exception:
                pass
            time.sleep(2)

    # Fallback: poll list until the new schedule appears.
    for _ in range(6):
        try:
            data = client.request("GET", "/appPriceSchedules", params={"filter[app]": app_id, "limit": 10})
            schedules = data.get("data") or []
        except Exception:
            schedules = []
        if schedules:
            return
        time.sleep(2)

    die("Pricing not set (Free schedule creation did not appear in read-back).")


def verify_review_detail(client: ASCClient, version_id: str) -> None:
    # App Store Connect models the review contact info as an AppStoreReviewDetail
    # resource associated with the App Store Version.
    try:
        data = client.request("GET", f"/appStoreVersions/{version_id}/appStoreReviewDetail")
    except Exception as e:
        die(f"App Review contact info missing (appStoreReviewDetail not found): {e}")
    detail = data.get("data") or {}
    attrs = (detail.get("attributes") or {}) if isinstance(detail, dict) else {}
    if not (attrs.get("contactEmail") or "").strip():
        die("App Review contactEmail is missing.")
    if not (attrs.get("contactPhone") or "").strip():
        die("App Review contactPhone is missing.")


def verify_age_rating(client: ASCClient, app_id: str, version_id: str | None = None) -> None:
    # Age rating declarations have moved across resources over time (apps vs versions).
    # Try multiple known relationship endpoints; pass if any returns a declaration object.
    attempts: list[tuple[str, str]] = []

    for path in (f"/apps/{app_id}/appInfoAgeRatingDeclaration", f"/apps/{app_id}/appStoreAgeRatingDeclaration"):
        attempts.append(("app", path))

    if version_id:
        for path in (
            f"/appStoreVersions/{version_id}/appInfoAgeRatingDeclaration",
            f"/appStoreVersions/{version_id}/appStoreAgeRatingDeclaration",
        ):
            attempts.append(("version", path))

    # Some accounts expose age rating declarations off AppInfo.
    app_info_id: str | None = None
    errors: list[str] = []
    try:
        payload = client.request("GET", f"/apps/{app_id}/appInfos", params={"limit": 1})
        info_obj = first(payload.get("data") or [])
        if isinstance(info_obj, dict) and info_obj.get("id"):
            app_info_id = info_obj["id"]
    except Exception as e:
        errors.append(f"app /apps/{app_id}/appInfos: {e}")

    if app_info_id:
        for path in (
            f"/appInfos/{app_info_id}/appInfoAgeRatingDeclaration",
            f"/appInfos/{app_info_id}/appStoreAgeRatingDeclaration",
        ):
            attempts.append(("appInfo", path))

    for scope, path in attempts:
        try:
            data = client.request("GET", path)
        except Exception as e:
            errors.append(f"{scope} {path}: {e}")
            continue
        decl = data.get("data")
        if decl:
            return

    detail = "\n  ".join(errors) if errors else "(no endpoints attempted)"
    die("Age Rating declaration not found. Complete Age Rating in App Store Connect.\n  " + detail)


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
    app_info_loc_attrs = verify_app_info(client, app_id, args.locale)
    verify_pricing(client, app_id)

    version_id, state = find_or_create_app_store_version(client, app_id, args.version)
    info(f"App Store version id={version_id} state={state}")
    verify_review_detail(client, version_id)
    verify_age_rating(client, app_id, version_id)

    # If already in a submitted/in-review state, do nothing.
    if state in ("WAITING_FOR_REVIEW", "IN_REVIEW", "PENDING_DEVELOPER_RELEASE", "READY_FOR_SALE"):
        info(f"Already submitted: {state}")
        return 0

    loc = get_version_localization(client, version_id, args.locale)
    loc_id = loc["id"]
    loc_attrs = loc.get("attributes") or {}

    # Support URL may live on App Store version localization (newer ASC API) or on App Info localization
    # (older ASC API). Accept either, but require a non-empty https:// URL.
    support_url = (
        (loc_attrs.get("supportUrl") or "").strip()
        or (loc_attrs.get("supportURL") or "").strip()
        or (app_info_loc_attrs.get("supportUrl") or "").strip()
        or (app_info_loc_attrs.get("supportURL") or "").strip()
    )
    ensure_https(support_url, "Support URL")

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
