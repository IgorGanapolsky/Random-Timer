#!/usr/bin/env python3
"""Read Apple refund events from Cloudflare KV and produce a refund summary.

Reads from the REFUND_EVENTS KV namespace populated by the
server/apple-webhook Cloudflare Worker.

Required environment variables:
  CLOUDFLARE_API_TOKEN    — API token with KV:Read permission
  CLOUDFLARE_ACCOUNT_ID  — Cloudflare account ID
  CLOUDFLARE_KV_NAMESPACE_ID — KV namespace ID for REFUND_EVENTS

Optional:
  CLOUDFLARE_KV_NAMESPACE_ID — if not set, falls back to
                               REFUND_EVENTS_NAMESPACE_ID or errors out.

Usage:
  python scripts/check_refunds.py
  python scripts/check_refunds.py --days 7
  python scripts/check_refunds.py --json-stdout
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any, Dict, List, Optional

SCRIPTS = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

try:
    from repo_dotenv import load_repo_dotenv
    load_repo_dotenv(REPO_ROOT)
except Exception:
    pass

# ──────────────────────────────────────────────────────────────────────────────
# Cloudflare KV REST API helpers
# ──────────────────────────────────────────────────────────────────────────────

_CF_BASE = "https://api.cloudflare.com/client/v4"


def _cf_headers(token: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def _cf_get(url: str, token: str) -> Any:
    req = urllib.request.Request(url, headers=_cf_headers(token))
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Cloudflare API error {exc.code}: {exc.read().decode()}") from exc


def list_kv_keys(
    token: str, account_id: str, namespace_id: str, prefix: str = "", cursor: str = ""
) -> Dict[str, Any]:
    """List keys in a KV namespace, with optional prefix filter."""
    url = (
        f"{_CF_BASE}/accounts/{account_id}/storage/kv/namespaces/{namespace_id}/keys"
        f"?limit=1000"
    )
    if prefix:
        url += f"&prefix={urllib.parse.quote(prefix)}"
    if cursor:
        url += f"&cursor={urllib.parse.quote(cursor)}"
    return _cf_get(url, token)


def get_kv_value(
    token: str, account_id: str, namespace_id: str, key: str
) -> Optional[str]:
    """Fetch a single KV value by key."""
    import urllib.parse
    url = (
        f"{_CF_BASE}/accounts/{account_id}/storage/kv/namespaces/{namespace_id}"
        f"/values/{urllib.parse.quote(key, safe='')}"
    )
    req = urllib.request.Request(url, headers=_cf_headers(token))
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode()
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise RuntimeError(f"Cloudflare KV get error {exc.code}: {exc.read().decode()}") from exc


# ──────────────────────────────────────────────────────────────────────────────
# Refund analysis logic
# ──────────────────────────────────────────────────────────────────────────────

import urllib.parse  # noqa: E402  (needs to be after the stdlib block above)


def _credentials() -> tuple[str, str, str]:
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "").strip()
    namespace_id = (
        os.environ.get("CLOUDFLARE_KV_NAMESPACE_ID", "").strip()
        or os.environ.get("REFUND_EVENTS_NAMESPACE_ID", "").strip()
    )
    return token, account_id, namespace_id


def fetch_all_refund_events(
    token: str, account_id: str, namespace_id: str
) -> List[Dict[str, Any]]:
    """Page through KV keys with prefix 'refund:' and fetch all values."""
    events: List[Dict[str, Any]] = []
    cursor = ""
    while True:
        resp = list_kv_keys(token, account_id, namespace_id, prefix="refund:", cursor=cursor)
        if not resp.get("success"):
            errors = resp.get("errors", [])
            raise RuntimeError(f"KV list_keys failed: {errors}")
        keys = [k["name"] for k in resp.get("result", [])]
        for key in keys:
            value = get_kv_value(token, account_id, namespace_id, key)
            if value:
                try:
                    events.append(json.loads(value))
                except json.JSONDecodeError:
                    pass
        result_info = resp.get("result_info", {})
        cursor = result_info.get("cursor", "")
        if not cursor:
            break
    return events


def fetch_all_lifecycle_events(
    token: str, account_id: str, namespace_id: str
) -> List[Dict[str, Any]]:
    """Fetch subscription lifecycle events from KV."""
    events: List[Dict[str, Any]] = []
    cursor = ""
    while True:
        resp = list_kv_keys(
            token, account_id, namespace_id, prefix="subscription_lifecycle:", cursor=cursor
        )
        if not resp.get("success"):
            errors = resp.get("errors", [])
            raise RuntimeError(f"KV list_keys failed: {errors}")
        keys = [k["name"] for k in resp.get("result", [])]
        for key in keys:
            value = get_kv_value(token, account_id, namespace_id, key)
            if value:
                try:
                    events.append(json.loads(value))
                except json.JSONDecodeError:
                    pass
        result_info = resp.get("result_info", {})
        cursor = result_info.get("cursor", "")
        if not cursor:
            break
    return events


def _within_window(iso_date: Optional[str], days: int) -> bool:
    if not iso_date:
        return True  # Include unknown-date events rather than silently drop them
    try:
        event_dt = dt.datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
        cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)
        return event_dt >= cutoff
    except ValueError:
        return True


def build_refund_summary(
    refund_events: List[Dict[str, Any]],
    lifecycle_events: List[Dict[str, Any]],
    days: int,
) -> Dict[str, Any]:
    """Aggregate refund and lifecycle data into a summary dict."""
    window_refunds = [
        e for e in refund_events
        if _within_window(e.get("refund_date") or e.get("received_at"), days)
    ]

    # Refund breakdown by product_id.
    by_product: Dict[str, int] = {}
    by_reason: Dict[str, int] = {}
    by_env: Dict[str, int] = {}

    for ev in window_refunds:
        pid = ev.get("product_id", "unknown")
        by_product[pid] = by_product.get(pid, 0) + 1

        reason = ev.get("refund_reason", "unknown")
        reason_str = str(reason) if reason is not None else "unknown"
        by_reason[reason_str] = by_reason.get(reason_str, 0) + 1

        env_name = ev.get("environment", "unknown")
        by_env[env_name] = by_env.get(env_name, 0) + 1

    # Lifecycle event summary.
    window_lifecycle = [
        e for e in lifecycle_events
        if _within_window(e.get("received_at"), days)
    ]
    by_type: Dict[str, int] = {}
    for ev in window_lifecycle:
        nt = ev.get("notification_type", "unknown")
        by_type[nt] = by_type.get(nt, 0) + 1

    # Production-only refund count (exclude sandbox).
    production_refunds = [
        e for e in window_refunds
        if str(e.get("environment", "")).upper() == "PRODUCTION"
    ]

    return {
        "status": "ok",
        "source": "cloudflare_kv_apple_webhook",
        "window_days": days,
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "refund_count_total": len(window_refunds),
        "refund_count_production": len(production_refunds),
        "refund_count_sandbox": len(window_refunds) - len(production_refunds),
        "refund_by_product": by_product,
        "refund_by_reason": by_reason,
        "refund_by_environment": by_env,
        "subscription_lifecycle_count": len(window_lifecycle),
        "subscription_lifecycle_by_type": by_type,
        "metric_id": "cloudflare_kv_apple_asn_v2_refund_window",
        "note": (
            "Refund events captured via Apple App Store Server Notifications V2 "
            "(server/apple-webhook Cloudflare Worker). Counts reflect events received "
            f"within the last {days} day(s), not store-reported units."
        ),
    }


def run(days: int = 30) -> Dict[str, Any]:
    token, account_id, namespace_id = _credentials()

    if not token or not account_id or not namespace_id:
        missing = []
        if not token:
            missing.append("CLOUDFLARE_API_TOKEN")
        if not account_id:
            missing.append("CLOUDFLARE_ACCOUNT_ID")
        if not namespace_id:
            missing.append("CLOUDFLARE_KV_NAMESPACE_ID")
        return {
            "status": "skipped",
            "reason": f"Missing env vars: {', '.join(missing)}",
            "refund_count_total": None,
            "refund_count_production": None,
        }

    try:
        refund_events = fetch_all_refund_events(token, account_id, namespace_id)
        lifecycle_events = fetch_all_lifecycle_events(token, account_id, namespace_id)
        return build_refund_summary(refund_events, lifecycle_events, days)
    except Exception as exc:
        return {
            "status": "error",
            "reason": str(exc),
            "refund_count_total": None,
            "refund_count_production": None,
        }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read Apple refund events from Cloudflare KV and report summary"
    )
    parser.add_argument("--days", type=int, default=30, help="Lookback window in days")
    parser.add_argument("--json-stdout", action="store_true", help="Print JSON to stdout")
    args = parser.parse_args()

    result = run(days=args.days)

    print("=" * 60)
    print("  APPLE REFUND SUMMARY (Cloudflare KV / ASN V2)")
    print("=" * 60)
    print(f"  Status         : {result.get('status')}")
    if result.get("status") not in ("ok",):
        print(f"  Reason         : {result.get('reason')}")
    else:
        print(f"  Window         : {result.get('window_days')} days")
        print(f"  Refunds total  : {result.get('refund_count_total')}")
        print(f"  Refunds prod   : {result.get('refund_count_production')}")
        print(f"  Refunds sandbox: {result.get('refund_count_sandbox')}")
        print(f"  By product     : {result.get('refund_by_product')}")
        print(f"  By reason      : {result.get('refund_by_reason')}")
        print(f"  Lifecycle evts : {result.get('subscription_lifecycle_count')}")
        print(f"  Lifecycle types: {result.get('subscription_lifecycle_by_type')}")
    print("=" * 60)

    if args.json_stdout:
        print(json.dumps(result, indent=2))

    return 0 if result.get("status") in ("ok", "skipped") else 1


if __name__ == "__main__":
    raise SystemExit(main())
