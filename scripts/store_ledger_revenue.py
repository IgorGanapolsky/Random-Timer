#!/usr/bin/env python3
"""Store ledger revenue snapshot: App Store Connect daily sales (TSV) + Android placeholder.

iOS uses GET /v1/salesReports (SALES / SUMMARY / DAILY), gzip TSV. Proceeds per row =
Units × Developer Proceeds (per unit), scoped to this app by Apple Identifier, SKU, or
Parent Identifier. Requires APPSTORE_VENDOR_NUMBER (8-digit vendor from ASC).

Android: Play does not expose the same consolidated ledger via androidpublisher v3 here;
status skipped with reason (PostHog / Console remain the proxies).
"""

from __future__ import annotations

import csv
import gzip
import io
import os
import sys
import time
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Optional

_SCRIPTS = Path(__file__).resolve().parent
for _p in (_SCRIPTS, _SCRIPTS / "asc"):
    _s = str(_p)
    if _s not in sys.path:
        sys.path.insert(0, _s)

IOS_APP_ID = "6758355312"
DEFAULT_APP_SKU = "randomtimer2026"
APP_STORE_CONNECT_API = "https://api.appstoreconnect.apple.com/v1"

STORE_LEDGER_METRIC_BUNDLE_ID = "store_ledger_revenue_v1"
ANDROID_LEDGER_NA_METRIC_ID = "store_ledger_revenue_android_not_exposed_androidpublisher_v1"


def _asc_get_with_retries(
    requests_mod: Any,
    url: str,
    headers: dict[str, str],
    params: dict[str, Any] | None = None,
    *,
    attempts: int = 3,
    timeout: float = 120.0,
) -> Any:
    last_exc: Exception | None = None
    for i in range(attempts):
        try:
            return requests_mod.get(url, headers=headers, params=params, timeout=timeout)
        except requests_mod.RequestException as exc:
            last_exc = exc
            if i < attempts - 1:
                time.sleep(2.0 * (i + 1))
    assert last_exc is not None
    raise last_exc


def _decode_sales_report_body(resp: Any) -> str:
    """ASC returns gzip TSV or occasionally JSON with a URL; normalize to decoded text."""
    import requests as rq

    raw: bytes = resp.content or b""
    ctype = (resp.headers.get("Content-Type") or "").lower()

    if "json" in ctype and raw:
        try:
            payload = resp.json()
        except Exception:
            payload = None
        if isinstance(payload, dict):
            data = payload.get("data")
            if isinstance(data, list) and data:
                attrs = (data[0] or {}).get("attributes") or {}
                url = attrs.get("url")
                if isinstance(url, str) and url.startswith("http"):
                    r2 = rq.get(url, timeout=120)
                    r2.raise_for_status()
                    raw = r2.content
                    ctype = (r2.headers.get("Content-Type") or "").lower()

    if not raw:
        return ""

    if "gzip" in ctype or (len(raw) >= 2 and raw[0:2] == b"\x1f\x8b"):
        try:
            with gzip.GzipFile(fileobj=io.BytesIO(raw), mode="rb") as gz:
                return gz.read().decode("utf-8", errors="replace")
        except (OSError, EOFError):
            pass

    return raw.decode("utf-8", errors="replace")


def _normalize_apple_id(value: str) -> str:
    s = (value or "").strip()
    if s.endswith(".0") and s[:-2].isdigit():
        s = s[:-2]
    return s


def _row_matches_app(row: dict[str, str], app_apple_id: str, app_sku: str) -> bool:
    aid = _normalize_apple_id(row.get("Apple Identifier", ""))
    sku = (row.get("SKU", "") or "").strip()
    parent = (row.get("Parent Identifier", "") or "").strip()
    target_id = _normalize_apple_id(app_apple_id)
    return aid == target_id or sku == app_sku or parent == app_sku


def _find_column(header: list[str], *candidates: str) -> Optional[int]:
    norm = [h.strip().replace("\ufeff", "") for h in header]
    for cand in candidates:
        for i, h in enumerate(norm):
            if h == cand:
                return i
    return None


def parse_sales_summary_tsv(
    text: str,
    *,
    app_apple_id: str,
    app_sku: str,
) -> dict[str, Any]:
    """Parse ASC daily sales summary TSV; sum Units × Developer Proceeds (per unit) for scoped rows."""
    if not text.strip():
        return {
            "rows_total": 0,
            "rows_matched": 0,
            "proceeds_by_currency": {},
            "units_sum_matched": 0.0,
        }

    lines = text.splitlines()
    if not lines:
        return {
            "rows_total": 0,
            "rows_matched": 0,
            "proceeds_by_currency": {},
            "units_sum_matched": 0.0,
        }

    reader = csv.reader(lines, delimiter="\t")
    rows_iter = iter(reader)
    try:
        header_raw = next(rows_iter)
    except StopIteration:
        return {
            "rows_total": 0,
            "rows_matched": 0,
            "proceeds_by_currency": {},
            "units_sum_matched": 0.0,
        }

    header = [h.strip().replace("\ufeff", "") for h in header_raw]

    units_i = _find_column(header, "Units")
    proceeds_i = _find_column(
        header,
        "Developer Proceeds (per unit)",
        "Developer Proceeds",
    )
    curr_i = _find_column(header, "Currency of Proceeds")

    proceeds_by_currency: dict[str, float] = defaultdict(float)
    rows_total = 0
    rows_matched = 0
    units_sum = 0.0

    if units_i is None or proceeds_i is None:
        return {
            "rows_total": 0,
            "rows_matched": 0,
            "proceeds_by_currency": {},
            "units_sum_matched": 0.0,
            "parse_note": "missing Units or Developer Proceeds column in TSV header",
            "header_sample": header[:20],
        }

    for parts in reader:
        if not parts or all(not (c or "").strip() for c in parts):
            continue
        rows_total += 1
        row_map = {header[i]: (parts[i] if i < len(parts) else "") for i in range(len(header))}
        if not _row_matches_app(row_map, app_apple_id, app_sku):
            continue
        rows_matched += 1
        try:
            u = float((parts[units_i] if units_i < len(parts) else "0") or 0)
        except ValueError:
            u = 0.0
        try:
            per = float((parts[proceeds_i] if proceeds_i < len(parts) else "0") or 0)
        except ValueError:
            per = 0.0
        ext = u * per
        units_sum += u
        ccy = "UNK"
        if curr_i is not None and curr_i < len(parts):
            ccy = (parts[curr_i] or "UNK").strip() or "UNK"
        proceeds_by_currency[ccy] += ext

    return {
        "rows_total": rows_total,
        "rows_matched": rows_matched,
        "proceeds_by_currency": dict(proceeds_by_currency),
        "units_sum_matched": round(units_sum, 4),
    }


def collect_ios_ledger_revenue(
    days: int,
    *,
    report_lag_days: int = 3,
    get_with_retries: Optional[Callable[..., Any]] = None,
) -> dict[str, Any]:
    """Fetch daily SALES SUMMARY reports for a rolling window (UTC dates)."""
    vendor = (os.environ.get("APPSTORE_VENDOR_NUMBER") or "").strip()
    app_sku = (os.environ.get("APPSTORE_LEDGER_APP_SKU") or DEFAULT_APP_SKU).strip()

    out: dict[str, Any] = {
        "status": "skipped",
        "metric_bundle_id": "asc_sales_summary_daily_ledger_v1",
        "app_apple_id": IOS_APP_ID,
        "app_sku": app_sku,
        "window_days_requested": days,
        "report_lag_days": report_lag_days,
        "vendor_number_configured": bool(vendor),
        "days_fetched_ok": 0,
        "days_404": 0,
        "days_http_error": 0,
        "errors": [],
    }

    if days < 1:
        out["reason"] = "days must be >= 1"
        return out

    if not vendor:
        out["reason"] = "missing APPSTORE_VENDOR_NUMBER (App Store Connect → Sales and Trends → vendor number)"
        return out

    try:
        from asc_client import ASCAuth
    except ImportError as e:
        out["reason"] = f"asc_client not importable: {e}"
        return out

    try:
        import requests
    except ImportError as e:
        out["reason"] = f"requests not installed: {e}"
        return out

    gw = get_with_retries or _asc_get_with_retries

    try:
        auth = ASCAuth.from_env()
    except Exception as e:
        out["reason"] = str(e)
        return out

    token = auth.jwt()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/a-gzip, application/json;q=0.9, */*;q=0.8",
    }

    today_utc = datetime.now(timezone.utc).date()
    # Use calendar dates in UTC for ASC reportDate filter.
    end_d = today_utc - timedelta(days=report_lag_days)
    start_d = end_d - timedelta(days=max(days, 1) - 1)

    agg_currency: dict[str, float] = defaultdict(float)
    total_rows = 0
    total_matched = 0
    units_total = 0.0

    d = start_d
    while d <= end_d:
        params = {
            "filter[vendorNumber]": vendor,
            "filter[reportType]": "SALES",
            "filter[reportSubType]": "SUMMARY",
            "filter[frequency]": "DAILY",
            "filter[reportDate]": d.isoformat(),
            "filter[version]": "1_0",
        }
        try:
            resp = gw(requests, f"{APP_STORE_CONNECT_API}/salesReports", headers=headers, params=params)
        except Exception as e:
            out["errors"].append(f"{d.isoformat()}: {e}")
            out["days_http_error"] += 1
            d += timedelta(days=1)
            continue

        if resp.status_code == 404:
            out["days_404"] += 1
            d += timedelta(days=1)
            continue

        if resp.status_code >= 400:
            out["days_http_error"] += 1
            snippet = (resp.text or "")[:500]
            out["errors"].append(f"{d.isoformat()}: HTTP {resp.status_code} {snippet}")
            d += timedelta(days=1)
            continue

        text = _decode_sales_report_body(resp)
        parsed = parse_sales_summary_tsv(text, app_apple_id=IOS_APP_ID, app_sku=app_sku)
        total_rows += parsed.get("rows_total", 0)
        total_matched += parsed.get("rows_matched", 0)
        units_total += float(parsed.get("units_sum_matched") or 0)
        for c, v in (parsed.get("proceeds_by_currency") or {}).items():
            agg_currency[c] += float(v)
        out["days_fetched_ok"] += 1
        d += timedelta(days=1)

    out["status"] = "ok" if out["days_fetched_ok"] else "error"
    if out["status"] == "error" and not out["errors"] and out["days_404"] > 0:
        out["reason"] = "no daily reports returned in window (404 for all days — check vendor number or lag)"
    out["report_date_start"] = start_d.isoformat()
    out["report_date_end"] = end_d.isoformat()
    out["proceeds_by_currency"] = {k: round(v, 4) for k, v in sorted(agg_currency.items())}
    out["developer_proceeds_total_rows"] = total_rows
    out["developer_proceeds_matched_rows"] = total_matched
    out["units_sum_matched_window"] = round(units_total, 4)
    out["note"] = (
        "Ledger: Apple SALES SUMMARY DAILY, version 1_0. Proceeds = sum over window of "
        "(Units × Developer Proceeds per unit) for rows tied to this app (Apple Identifier, "
        "SKU, or Parent Identifier). Not net of tax remittance; multi-currency kept separate. "
        f"Recent calendar days omitted (lag={report_lag_days}) for completeness."
    )
    return out


def collect_android_ledger_revenue(_days: int) -> dict[str, Any]:
    return {
        "status": "skipped",
        "metric_bundle_id": ANDROID_LEDGER_NA_METRIC_ID,
        "reason": (
            "Google Play consolidated ledger (estimated sales / earnings) is not available "
            "through androidpublisher v3 in this snapshot; use Play Console exports or "
            "PostHog paywall revenue as a proxy."
        ),
    }


def collect_store_ledger_revenue(
    days: int,
    *,
    report_lag_days: int = 3,
    get_with_retries: Optional[Callable[..., Any]] = None,
) -> dict[str, Any]:
    return {
        "metric_bundle_id": STORE_LEDGER_METRIC_BUNDLE_ID,
        "window_days": days,
        "ios": collect_ios_ledger_revenue(days, report_lag_days=report_lag_days, get_with_retries=get_with_retries),
        "android": collect_android_ledger_revenue(days),
    }
