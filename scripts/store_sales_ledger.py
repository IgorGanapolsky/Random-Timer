#!/usr/bin/env python3
"""Optional store ledger snippets for executive_metrics (not PostHog proxies).

- iOS: App Store Connect Sales Reports API (daily SALES SUMMARY), when
  APPSTORE_VENDOR_NUMBER is set alongside standard ASC auth env vars.
  APPSTORE_CONNECT_VENDOR_NUMBER is accepted as a legacy alias for local runs.
  Aggregates numeric columns across downloaded TSV reports for the lookback window.

Does not print secrets. See docs/OPERATIONAL_RELIABILITY.md for proxy vs ledger rules.
"""

from __future__ import annotations

import csv
import datetime as dt
import gzip
import io
import os
import re
import sys
from pathlib import Path
from typing import Any

_SCRIPTS = Path(__file__).resolve().parent
for _p in (_SCRIPTS, _SCRIPTS / "asc"):
    _s = str(_p)
    if _s not in sys.path:
        sys.path.insert(0, _s)

IOS_APP_ID = "6758355312"

ASC_SALES_METRIC_BUNDLE_ID = "asc_sales_daily_summary_tsv_v1"
ASC_VENDOR_ENV = "APPSTORE_VENDOR_NUMBER"
ASC_LEGACY_VENDOR_ENV = "APPSTORE_CONNECT_VENDOR_NUMBER"


def _norm_header(h: str) -> str:
    return re.sub(r"\s+", " ", (h or "").strip().lower())


def _parse_sales_tsv_rows(text: str) -> tuple[list[str], list[list[str]]]:
    """Apple sales files are typically tab-separated with a header row."""
    sample = text[:4096]
    delim = "\t" if sample.count("\t") >= sample.count(",") else ","
    reader = csv.reader(io.StringIO(text), delimiter=delim)
    rows = list(reader)
    if not rows:
        return [], []
    header = [_norm_header(c) for c in rows[0]]
    data = [r for r in rows[1:] if any((c or "").strip() for c in r)]
    return header, data


def _decode_sales_report_body(raw: bytes) -> str:
    """ASC salesReports returns gzip bytes on success, but keep TSV fallback tolerant."""
    try:
        return gzip.decompress(raw).decode("utf-8-sig")
    except OSError:
        return raw.decode("utf-8-sig", errors="replace")


def _find_col(header: list[str], *candidates: str) -> int | None:
    cand = [_norm_header(c) for c in candidates]
    for i, h in enumerate(header):
        if h in cand:
            return i
    for i, h in enumerate(header):
        for c in cand:
            if c and h.startswith(f"{c} "):
                return i
    return None


def _vendor_number_from_env() -> tuple[str, str | None]:
    vendor = (os.environ.get(ASC_VENDOR_ENV) or "").strip()
    if vendor:
        return vendor, ASC_VENDOR_ENV
    legacy_vendor = (os.environ.get(ASC_LEGACY_VENDOR_ENV) or "").strip()
    if legacy_vendor:
        return legacy_vendor, ASC_LEGACY_VENDOR_ENV
    return "", None


def _float_cell(val: str) -> float:
    try:
        return float((val or "").replace(",", "").strip() or 0.0)
    except ValueError:
        return 0.0


def _int_cell(val: str) -> int:
    try:
        return int(float((val or "").replace(",", "").strip() or 0))
    except ValueError:
        return 0


def fetch_ios_sales_daily_summary(days: int) -> dict[str, Any]:
    """Sum units and money columns from ASC daily SALES SUMMARY reports."""
    vendor, vendor_env = _vendor_number_from_env()
    if not vendor:
        return {
            "status": "skipped",
            "reason": f"{ASC_VENDOR_ENV} not set",
            "metric_bundle_id": ASC_SALES_METRIC_BUNDLE_ID,
        }

    try:
        import requests
    except ImportError:
        return {
            "status": "skipped",
            "reason": "requests not installed",
            "metric_bundle_id": ASC_SALES_METRIC_BUNDLE_ID,
        }

    try:
        from asc_client import APP_STORE_CONNECT_API, ASCAuth
    except ImportError:
        return {
            "status": "skipped",
            "reason": "asc_client not importable",
            "metric_bundle_id": ASC_SALES_METRIC_BUNDLE_ID,
        }

    try:
        auth = ASCAuth.from_env()
    except Exception as exc:
        return {
            "status": "skipped",
            "reason": str(exc),
            "metric_bundle_id": ASC_SALES_METRIC_BUNDLE_ID,
        }

    today = dt.date.today()
    sum_proceeds = 0.0
    sum_customer = 0.0
    sum_units = 0
    days_with_data = 0
    http_errors: list[str] = []
    parse_errors: list[str] = []

    for i in range(1, days + 1):
        report_day = today - dt.timedelta(days=i)
        report_date = report_day.isoformat()
        params = {
            "filter[reportType]": "SALES",
            "filter[frequency]": "DAILY",
            "filter[reportSubType]": "SUMMARY",
            "filter[version]": "1_0",
            "filter[vendorNumber]": vendor,
            "filter[reportDate]": report_date,
        }
        try:
            headers = {
                "Authorization": f"Bearer {auth.jwt()}",
                "Accept": "application/a-gzip",
            }
            list_resp = requests.get(
                f"{APP_STORE_CONNECT_API}/salesReports",
                headers=headers,
                params=params,
                timeout=90,
            )
        except Exception as exc:
            http_errors.append(f"{report_date}: request {exc}")
            continue

        if list_resp.status_code == 404:
            continue
        if list_resp.status_code >= 300:
            http_errors.append(f"{report_date}: HTTP {list_resp.status_code}")
            continue

        try:
            text = _decode_sales_report_body(list_resp.content)
            hdr, rows = _parse_sales_tsv_rows(text)
            if not hdr:
                parse_errors.append(f"{report_date}: empty header")
                continue
            idx_units = _find_col(hdr, "units", "quantity", "qty")
            idx_proceeds = _find_col(
                hdr,
                "developer proceeds",
                "proceeds",
                "partner share",
                "earnings",
            )
            idx_customer = _find_col(hdr, "customer price", "end customer price")
            day_units = 0
            day_proceeds = 0.0
            day_customer = 0.0
            app_col = _find_col(hdr, "apple identifier", "app apple id", "parent identifier")
            for row in rows:
                if app_col is not None and app_col < len(row):
                    cell = (row[app_col] or "").strip()
                    if cell and cell != IOS_APP_ID:
                        continue
                if idx_units is not None and idx_units < len(row):
                    day_units += _int_cell(row[idx_units])
                if idx_proceeds is not None and idx_proceeds < len(row):
                    day_proceeds += _float_cell(row[idx_proceeds])
                if idx_customer is not None and idx_customer < len(row):
                    day_customer += _float_cell(row[idx_customer])
            if day_units or day_proceeds or day_customer:
                days_with_data += 1
            sum_units += day_units
            sum_proceeds += day_proceeds
            sum_customer += day_customer
        except Exception as exc:
            parse_errors.append(f"{report_date}: {exc}")

    note = (
        "Ledger from App Store Connect salesReports (SALES, DAILY, SUMMARY, 1_0). "
        "Sums TSV columns matching developer proceeds / customer price / units when present; "
        f"filtered to Apple identifier {IOS_APP_ID} when a matching column exists. "
        "Territory/tax timing per Apple reporting; not bank settlement."
    )

    status = "ok"
    if http_errors or parse_errors:
        status = "partial" if days_with_data else "error"

    out: dict[str, Any] = {
        "status": status,
        "metric_bundle_id": ASC_SALES_METRIC_BUNDLE_ID,
        "vendor_configured": True,
        "vendor_env": vendor_env,
        "window_days_requested": days,
        "days_with_nonzero_rows": days_with_data,
        "sum_units": sum_units,
        "sum_developer_proceeds_or_partner_share": round(sum_proceeds, 4)
        if sum_proceeds
        else sum_proceeds,
        "sum_customer_price": round(sum_customer, 4) if sum_customer else sum_customer,
        "note": note,
    }
    if http_errors:
        out["http_errors_sample"] = http_errors[:15]
    if parse_errors:
        out["parse_errors_sample"] = parse_errors[:15]
    if days_with_data == 0 and not http_errors and not parse_errors:
        out["note"] += " No report rows in window (or no sales yet)."
    elif status == "partial":
        out["note"] += " Ledger collection partially succeeded; error samples are attached."
    elif status == "error":
        out["note"] += " Ledger collection failed for every non-empty requested report; error samples are attached."
    return out
