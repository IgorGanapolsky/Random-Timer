#!/usr/bin/env python3
"""Autonomous App Store review operations monitor.

Fetches recent App Store customer reviews via App Store Connect API,
builds an SLA-focused triage report, and optionally sends a Slack alert.

Exit codes:
  0 - success
  1 - SLA breaches found when --fail-on-sla is enabled
  2 - configuration/API/runtime error
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

APP_STORE_CONNECT_API = "https://api.appstoreconnect.apple.com/v1"
DEFAULT_BUNDLE_ID = "com.igorganapolsky.randomtimer"


def _die(msg: str) -> None:
    print(f"❌ {msg}", file=sys.stderr)
    raise SystemExit(2)


def _read_private_key_material(key_id: str) -> str:
    value = (os.environ.get("APPSTORE_PRIVATE_KEY") or "").strip()
    if not value:
        value = (os.environ.get("APPSTORE_PRIVATE_KEY_PATH") or "").strip()
    if not value:
        default_path = os.path.expanduser(f"~/.appstoreconnect/private_keys/AuthKey_{key_id}.p8")
        if os.path.isfile(default_path):
            value = default_path

    if not value:
        return ""

    expanded = os.path.expanduser(value)
    if os.path.isfile(expanded):
        with open(expanded, "r", encoding="utf-8") as f:
            return f.read()
    return value


class AscClient:
    def __init__(self) -> None:
        self._token: Optional[str] = None
        self._token_expiry = 0

    def _get_token(self) -> str:
        now = int(time.time())
        if self._token and now < self._token_expiry - 30:
            return self._token

        try:
            import jwt  # PyJWT
        except ImportError:
            _die("Missing dependency: pyjwt (pip install pyjwt cryptography)")

        key_id = (os.environ.get("APPSTORE_KEY_ID") or "").strip()
        issuer_id = (os.environ.get("APPSTORE_ISSUER_ID") or "").strip()
        private_key = _read_private_key_material(key_id)

        missing: List[str] = []
        if not key_id:
            missing.append("APPSTORE_KEY_ID")
        if not issuer_id:
            missing.append("APPSTORE_ISSUER_ID")
        if not private_key:
            missing.append("APPSTORE_PRIVATE_KEY (or APPSTORE_PRIVATE_KEY_PATH)")
        if missing:
            _die(f"Missing required env vars: {', '.join(missing)}")

        payload = {
            "iss": issuer_id,
            "iat": now,
            "exp": now + 1200,
            "aud": "appstoreconnect-v1",
        }
        headers = {"alg": "ES256", "kid": key_id, "typ": "JWT"}
        self._token = jwt.encode(payload, private_key, algorithm="ES256", headers=headers)
        self._token_expiry = now + 1200
        return self._token

    def get(self, path_or_url: str, params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        try:
            import requests
        except ImportError:
            _die("Missing dependency: requests (pip install requests)")

        if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
            url = path_or_url
        else:
            url = f"{APP_STORE_CONNECT_API}{path_or_url}"

        resp = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {self._get_token()}",
                "Content-Type": "application/json",
            },
            params=params or {},
            timeout=30,
        )
        if resp.status_code >= 400:
            _die(
                "App Store Connect API error\n"
                f"GET {url}\n"
                f"HTTP {resp.status_code}\n"
                f"Body: {resp.text[:2000]}"
            )
        return resp.json()


@dataclass
class ReviewItem:
    id: str
    rating: int
    title: str
    body: str
    territory: str
    created_date: Optional[str]
    has_response: bool


def _parse_int(value: Any, fallback: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return fallback


def _parse_created_date(attrs: Dict[str, Any]) -> Optional[str]:
    for key in ("createdDate", "lastModifiedDate", "date"):
        raw = (attrs.get(key) or "").strip()
        if raw:
            return raw
    return None


def _normalize_text(value: Any) -> str:
    return str(value or "").strip()


def _parse_review(item: Dict[str, Any]) -> ReviewItem:
    attrs = item.get("attributes", {}) or {}
    rel = item.get("relationships", {}) or {}
    response_rel = (rel.get("response") or {}).get("data")

    rating = _parse_int(attrs.get("rating") or attrs.get("value") or 0)
    title = _normalize_text(attrs.get("title") or attrs.get("headline"))
    body = _normalize_text(attrs.get("body") or attrs.get("review") or attrs.get("text"))
    territory = _normalize_text(attrs.get("territory") or attrs.get("countryCode") or "unknown")

    return ReviewItem(
        id=str(item.get("id") or ""),
        rating=rating,
        title=title,
        body=body,
        territory=territory,
        created_date=_parse_created_date(attrs),
        has_response=bool(response_rel),
    )


def _iso_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _parse_iso_datetime(value: Optional[str]) -> Optional[dt.datetime]:
    if not value:
        return None
    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        return dt.datetime.fromisoformat(raw)
    except ValueError:
        return None


def _hours_since(value: Optional[str], now: dt.datetime) -> Optional[float]:
    parsed = _parse_iso_datetime(value)
    if not parsed:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    delta = now - parsed.astimezone(dt.timezone.utc)
    return delta.total_seconds() / 3600.0


def _fetch_app_id(client: AscClient, bundle_id: str) -> str:
    payload = client.get("/apps", params={"filter[bundleId]": bundle_id, "limit": "1"})
    data = payload.get("data", []) or []
    if not data:
        _die(f"No app found for bundle id '{bundle_id}'")
    return str(data[0].get("id"))


def _fetch_reviews(client: AscClient, app_id: str, limit: int) -> List[ReviewItem]:
    reviews: List[ReviewItem] = []
    next_url: Optional[str] = None

    while True:
        if next_url:
            payload = client.get(next_url)
        else:
            payload = client.get(
                f"/apps/{app_id}/customerReviews",
                params={
                    "limit": str(min(limit, 200)),
                    "sort": "-createdDate",
                    "fields[customerReviews]": "rating,title,body,territory,createdDate,response",
                },
            )

        for item in payload.get("data", []) or []:
            reviews.append(_parse_review(item))
            if len(reviews) >= limit:
                return reviews

        next_url = (payload.get("links") or {}).get("next")
        if not next_url:
            break

    return reviews


def _slack_post(webhook_url: str, text: str) -> None:
    try:
        import requests
    except ImportError:
        _die("Missing dependency: requests (pip install requests)")

    resp = requests.post(webhook_url, json={"text": text}, timeout=15)
    if resp.status_code >= 400:
        _die(f"Slack webhook failed: HTTP {resp.status_code} body={resp.text[:400]}")


def _render_markdown(report: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# ASC Reviews Ops Report")
    lines.append("")
    lines.append(f"- Generated: {report['generatedAt']}")
    lines.append(f"- Bundle ID: `{report['bundleId']}`")
    lines.append(f"- App ID: `{report['appId']}`")
    lines.append(f"- Reviews scanned: {report['totalReviews']}")
    lines.append(f"- Average rating (sample): {report['averageRating']}")
    lines.append("")
    lines.append("## Ratings Breakdown")
    lines.append("")
    lines.append("| Rating | Count |")
    lines.append("|---:|---:|")
    for rating in [5, 4, 3, 2, 1]:
        lines.append(f"| {rating} | {report['ratings'].get(str(rating), 0)} |")

    lines.append("")
    lines.append("## SLA Triage (1-3 star without response)")
    lines.append("")
    lines.append(f"- Unresolved low-star reviews: {report['unresolvedLowStarCount']}")
    lines.append(f"- SLA breaches (> {report['slaHours']}h): {report['slaBreachCount']}")

    breaches = report.get("slaBreaches", []) or []
    if breaches:
        lines.append("")
        lines.append("| Review ID | Rating | Territory | Age (h) | Title |")
        lines.append("|---|---:|---|---:|---|")
        for it in breaches:
            title = (it.get("title") or "").replace("|", "/")
            lines.append(
                f"| `{it.get('id')}` | {it.get('rating')} | {it.get('territory')} | {it.get('ageHours')} | {title[:90]} |"
            )

    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Monitor App Store customer review operations.")
    p.add_argument("--bundle-id", default=DEFAULT_BUNDLE_ID, help=f"iOS bundle id (default: {DEFAULT_BUNDLE_ID})")
    p.add_argument("--limit", type=int, default=200, help="Max reviews to scan (default: 200)")
    p.add_argument("--sla-hours", type=int, default=24, help="SLA threshold in hours for low-star response (default: 24)")
    p.add_argument("--json-out", required=True, help="Path to write JSON report")
    p.add_argument("--markdown-out", help="Path to write markdown report")
    p.add_argument("--slack-webhook", default=(os.environ.get("ASC_REVIEWS_SLACK_WEBHOOK") or "").strip(), help="Slack webhook URL (or set ASC_REVIEWS_SLACK_WEBHOOK)")
    p.add_argument("--fail-on-sla", action="store_true", help="Exit 1 when SLA breaches exist")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    client = AscClient()
    app_id = _fetch_app_id(client, args.bundle_id)
    reviews = _fetch_reviews(client, app_id, max(1, args.limit))
    now = dt.datetime.now(dt.timezone.utc)

    ratings: Dict[str, int] = {str(i): 0 for i in range(1, 6)}
    total_rating = 0
    rated_count = 0
    unresolved_low_star: List[Dict[str, Any]] = []

    for rv in reviews:
        if 1 <= rv.rating <= 5:
            ratings[str(rv.rating)] += 1
            total_rating += rv.rating
            rated_count += 1

        if rv.rating <= 3 and not rv.has_response:
            age_hours = _hours_since(rv.created_date, now)
            unresolved_low_star.append(
                {
                    "id": rv.id,
                    "rating": rv.rating,
                    "territory": rv.territory,
                    "title": rv.title,
                    "createdDate": rv.created_date,
                    "ageHours": round(age_hours, 1) if age_hours is not None else None,
                }
            )

    sla_breaches = [
        item
        for item in unresolved_low_star
        if item.get("ageHours") is not None and float(item["ageHours"]) > float(args.sla_hours)
    ]

    avg = round(total_rating / rated_count, 3) if rated_count else 0.0

    report: Dict[str, Any] = {
        "generatedAt": _iso_now(),
        "bundleId": args.bundle_id,
        "appId": app_id,
        "totalReviews": len(reviews),
        "averageRating": avg,
        "ratings": ratings,
        "slaHours": args.sla_hours,
        "unresolvedLowStarCount": len(unresolved_low_star),
        "slaBreachCount": len(sla_breaches),
        "slaBreaches": sla_breaches,
        "topUnresolved": unresolved_low_star[:20],
    }

    os.makedirs(os.path.dirname(os.path.abspath(args.json_out)), exist_ok=True)
    with open(args.json_out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=True, indent=2)

    if args.markdown_out:
        os.makedirs(os.path.dirname(os.path.abspath(args.markdown_out)), exist_ok=True)
        with open(args.markdown_out, "w", encoding="utf-8") as f:
            f.write(_render_markdown(report))

    print("══ ASC Reviews Ops ═══════════════════════════════")
    print(f"Bundle ID:             {args.bundle_id}")
    print(f"App ID:                {app_id}")
    print(f"Reviews scanned:       {len(reviews)}")
    print(f"Average rating sample: {avg}")
    print(f"Unresolved 1-3 star:   {len(unresolved_low_star)}")
    print(f"SLA breaches >{args.sla_hours}h:   {len(sla_breaches)}")
    print("══════════════════════════════════════════════════")

    if args.slack_webhook:
        slack_text = (
            f"ASC reviews ops ({args.bundle_id})\\n"
            f"Reviews scanned: {len(reviews)} | Avg: {avg}\\n"
            f"Unresolved 1-3 star: {len(unresolved_low_star)} | SLA breaches >{args.sla_hours}h: {len(sla_breaches)}"
        )
        _slack_post(args.slack_webhook, slack_text)
        print("Slack alert sent")

    if args.fail_on_sla and sla_breaches:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
