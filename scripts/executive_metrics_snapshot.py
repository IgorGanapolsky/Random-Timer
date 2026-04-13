#!/usr/bin/env python3
"""Single executive snapshot: PostHog (product) + store APIs + Crashlytics (BigQuery).

Outputs marketing/data/executive_metrics.json. Intended to run locally (.env) or in CI
(GitHub Actions secrets). No secrets are printed.

Audience (PostHog): PRAGMATIC_LIVE — non-debug, real device, not internal, store-production
distribution_channel only (plus legacy untagged events). Optional POSTHOG_EXECUTIVE_EXCLUDE_PERSON_IDS.
See docs/OBSERVABILITY.md and marketing/data/README.md.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

SCRIPTS = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

from repo_dotenv import load_repo_dotenv  # noqa: E402

# distribution_channel set by iOS/Android SDKs; legacy events omit it (treated as legacy).
_DISTRIBUTION_EXCLUDE = (
    "'testflight', 'non_play_install', 'dev', 'emulator', 'simulator', 'ui_test'"
)

PRAGMATIC_LIVE = f"""(
  lower(coalesce(properties.build_type, 'release')) != 'debug'
  AND lower(coalesce(properties.runtime_target, 'device')) NOT IN ('simulator', 'emulator')
  AND coalesce(toString(properties.is_internal), 'false') != 'true'
  AND coalesce(toString(properties.distribution_channel), 'legacy') NOT IN ({_DISTRIBUTION_EXCLUDE})
)"""


_REDACT_PERSON_ID_NOT_IN = re.compile(r" AND person_id NOT IN \([^)]*\)")


def _redact_audience_sql_for_json(sql: str) -> str:
    """Do not persist excluded PostHog person UUIDs into committed JSON artifacts."""
    return _REDACT_PERSON_ID_NOT_IN.sub(
        " AND person_id NOT IN (<redacted: POSTHOG_EXECUTIVE_EXCLUDE_PERSON_IDS>)",
        sql,
    )


def _posthog_person_id_exclusion_sql() -> str:
    """Optional comma-separated PostHog person UUIDs to drop from executive counts (e.g. CEO test devices)."""
    raw = os.environ.get("POSTHOG_EXECUTIVE_EXCLUDE_PERSON_IDS", "").strip()
    if not raw:
        return ""
    safe_ids: list[str] = []
    for part in raw.split(","):
        pid = part.strip()
        if not pid or not re.fullmatch(r"[0-9a-fA-F-]{10,}", pid):
            continue
        safe_ids.append(f"'{pid.replace(chr(39), '')}'")
    if not safe_ids:
        return ""
    return " AND person_id NOT IN (" + ", ".join(safe_ids) + ")"

POSTHOG_EXECUTIVE_METRIC_BUNDLE_ID = "posthog_executive_pragmatic_live_hogql_v1"

# Stable IDs for executive JSON fields under posthog.* (HogQL + derived).
POSTHOG_EXECUTIVE_METRIC_FIELD_IDS: Dict[str, str] = {
    "distinct_persons_application_installed": (
        "posthog_hogql_distinct_persons_event_application_installed"
    ),
    "distinct_persons_first_open": "posthog_hogql_distinct_persons_event_first_open",
    "timer_started_events": "posthog_hogql_count_events_timer_started",
    "timer_completed_events": "posthog_hogql_count_events_timer_completed",
    "distinct_persons_timer_started": "posthog_hogql_distinct_persons_event_timer_started",
    "distinct_persons_timer_completed": "posthog_hogql_distinct_persons_event_timer_completed",
    "distinct_persons_timer_started_and_completed": (
        "posthog_hogql_distinct_persons_completed_also_started_same_window"
    ),
    "wqtu_distinct_persons": "posthog_hogql_wqtu_timer_completed_ge3_trailing_window_days",
    "wqtu_7d_distinct_persons": "posthog_hogql_wqtu_timer_completed_ge3_trailing_7d_fixed",
    "timer_abandon_rate_event_level_pct": (
        "posthog_derived_event_level_started_minus_completed_over_started_pct"
    ),
    "distinct_persons_paywall_purchase_success": (
        "posthog_hogql_distinct_persons_event_paywall_purchase_success"
    ),
    "events_paywall_purchase_success": "posthog_hogql_count_events_paywall_purchase_success",
    "distinct_persons_paywall_purchase_success_ios": (
        "posthog_hogql_distinct_persons_event_paywall_purchase_success_ios"
    ),
    "distinct_persons_paywall_purchase_success_android": (
        "posthog_hogql_distinct_persons_event_paywall_purchase_success_android"
    ),
    "events_paywall_purchase_success_ios": (
        "posthog_hogql_count_events_paywall_purchase_success_ios"
    ),
    "events_paywall_purchase_success_android": (
        "posthog_hogql_count_events_paywall_purchase_success_android"
    ),
    "in_app_review_prompt_events": "posthog_hogql_count_events_review_prompt_requested",
    "in_app_review_prompt_distinct_persons": (
        "posthog_hogql_distinct_persons_event_review_prompt_requested"
    ),
    "top_screens_by_distinct_persons": (
        "posthog_hogql_top_screens_by_distinct_persons_limit_12_order_desc"
    ),
    "posthog_exception_events": "posthog_hogql_count_events_dollar_exception",
    "paywall_revenue_sum_event_properties": (
        "posthog_hogql_sum_coalesce_revenue_price_paywall_purchase_success"
    ),
    "paywall_viewed_distinct_persons": "posthog_hogql_distinct_persons_paywall_viewed",
    "paywall_purchaser_conversion_from_viewed_pct": (
        "posthog_derived_distinct_purchasers_over_distinct_paywall_viewers_pct"
    ),
    "distinct_persons_pageview_utm_cpc_ppc_paid": (
        "posthog_hogql_distinct_persons_pageview_utm_medium_cpc_ppc_paid"
    ),
}


def _posthog_credentials() -> tuple[str, str]:
    key = (
        os.environ.get("POSTHOG_PERSONAL_API_KEY", "").strip()
        or os.environ.get("POSTHOG_API_KEY", "").strip()
        or os.environ.get("posthog_api_key", "").strip()
    )
    project_id = os.environ.get("POSTHOG_PROJECT_ID", "").strip()
    return key, project_id


def _posthog_section(project_id: str, api_key: str, days: int) -> Dict[str, Any]:
    from store_downloads_snapshot import posthog_query

    errors: List[str] = []
    win = f"{days} day"
    person_excl = _posthog_person_id_exclusion_sql()
    f = PRAGMATIC_LIVE + person_excl
    audience_sql_json = _redact_audience_sql_for_json(f.strip()) if person_excl else f.strip()
    out: Dict[str, Any] = {
        "status": "ok" if api_key and project_id else "skipped",
        "host": "https://us.posthog.com",
        "project_id": project_id or None,
        "audience": "pragmatic_live",
        "audience_sql": audience_sql_json,
        "audience_note": (
            "Excludes debug/sim/emulator, is_internal, non–App Store/TestFlight/Firebase-style "
            "distribution_channel values, and optional POSTHOG_EXECUTIVE_EXCLUDE_PERSON_IDS. "
            "Legacy events without distribution_channel use coalesce 'legacy' (still included). "
            "Not a guarantee of human/non-team users—set person exclusions for known IDs."
        ),
        "exclude_person_ids_configured": bool(person_excl),
        "window_days": days,
        "errors": errors,
    }
    if not api_key or not project_id:
        out["reason"] = "missing POSTHOG_PERSONAL_API_KEY or POSTHOG_PROJECT_ID"
        return out

    def scalar(sql: str) -> Optional[int]:
        data = posthog_query(sql, api_key, project_id, errors)
        if not data or not data.get("results"):
            return None
        row = data["results"][0]
        if not row:
            return None
        try:
            return int(row[0] or 0)
        except (TypeError, ValueError):
            return None

    def scalar_float(sql: str) -> Optional[float]:
        data = posthog_query(sql, api_key, project_id, errors)
        if not data or not data.get("results"):
            return None
        row = data["results"][0]
        if not row:
            return None
        try:
            return float(row[0] or 0.0)
        except (TypeError, ValueError):
            return None

    out["distinct_persons_application_installed"] = scalar(
        f"SELECT count(DISTINCT person_id) FROM events WHERE event = 'Application Installed' "
        f"AND timestamp > now() - interval {win} AND {f}"
    )
    out["distinct_persons_first_open"] = scalar(
        f"SELECT count(DISTINCT person_id) FROM events WHERE event = 'first_open' "
        f"AND timestamp > now() - interval {win} AND {f}"
    )
    started = scalar(
        f"SELECT count() FROM events WHERE event = 'timer_started' "
        f"AND timestamp > now() - interval {win} AND {f}"
    )
    completed = scalar(
        f"SELECT count() FROM events WHERE event = 'timer_completed' "
        f"AND timestamp > now() - interval {win} AND {f}"
    )
    out["timer_started_events"] = started
    out["timer_completed_events"] = completed
    out["distinct_persons_timer_started"] = scalar(
        f"SELECT count(DISTINCT person_id) FROM events WHERE event = 'timer_started' "
        f"AND timestamp > now() - interval {win} AND {f}"
    )
    out["distinct_persons_timer_completed"] = scalar(
        f"SELECT count(DISTINCT person_id) FROM events WHERE event = 'timer_completed' "
        f"AND timestamp > now() - interval {win} AND {f}"
    )
    out["distinct_persons_timer_started_and_completed"] = scalar(
        f"SELECT count(DISTINCT person_id) FROM events WHERE event = 'timer_completed' "
        f"AND timestamp > now() - interval {win} AND {f} "
        f"AND person_id IN ("
        f"SELECT person_id FROM events WHERE event = 'timer_started' "
        f"AND timestamp > now() - interval {win} AND {f}"
        f")"
    )
    out["wqtu_distinct_persons"] = scalar(
        f"SELECT count() FROM ("
        f"SELECT person_id FROM events WHERE event = 'timer_completed' "
        f"AND timestamp > now() - interval {win} AND {f} "
        f"GROUP BY person_id HAVING count() >= 3"
        f")"
    )
    out["wqtu_7d_distinct_persons"] = scalar(
        f"SELECT count() FROM ("
        f"SELECT person_id FROM events WHERE event = 'timer_completed' "
        f"AND timestamp > now() - interval 7 day AND {f} "
        f"GROUP BY person_id HAVING count() >= 3"
        f")"
    )
    if started and started > 0 and completed is not None:
        out["timer_abandon_rate_event_level_pct"] = round(
            (started - completed) / started * 100, 2
        )
    pf_ios = "AND coalesce(toString(properties.platform), '') = 'ios'"
    pf_android = "AND coalesce(toString(properties.platform), '') = 'android'"
    out["distinct_persons_paywall_purchase_success"] = scalar(
        f"SELECT count(DISTINCT person_id) FROM events WHERE event = 'paywall_purchase_success' "
        f"AND timestamp > now() - interval {win} AND {f}"
    )
    out["events_paywall_purchase_success"] = scalar(
        f"SELECT count() FROM events WHERE event = 'paywall_purchase_success' "
        f"AND timestamp > now() - interval {win} AND {f}"
    )
    out["distinct_persons_paywall_purchase_success_ios"] = scalar(
        f"SELECT count(DISTINCT person_id) FROM events WHERE event = 'paywall_purchase_success' "
        f"AND timestamp > now() - interval {win} AND {f} {pf_ios}"
    )
    out["distinct_persons_paywall_purchase_success_android"] = scalar(
        f"SELECT count(DISTINCT person_id) FROM events WHERE event = 'paywall_purchase_success' "
        f"AND timestamp > now() - interval {win} AND {f} {pf_android}"
    )
    out["events_paywall_purchase_success_ios"] = scalar(
        f"SELECT count() FROM events WHERE event = 'paywall_purchase_success' "
        f"AND timestamp > now() - interval {win} AND {f} {pf_ios}"
    )
    out["events_paywall_purchase_success_android"] = scalar(
        f"SELECT count() FROM events WHERE event = 'paywall_purchase_success' "
        f"AND timestamp > now() - interval {win} AND {f} {pf_android}"
    )
    out["paywall_revenue_sum_event_properties"] = scalar_float(
        f"SELECT sum(toFloatOrZero(coalesce(toString(properties.revenue), toString(properties.price), '0'))) "
        f"FROM events WHERE event = 'paywall_purchase_success' "
        f"AND timestamp > now() - interval {win} AND {f}"
    )
    viewed_d = scalar(
        f"SELECT count(DISTINCT person_id) FROM events WHERE event = 'paywall_viewed' "
        f"AND timestamp > now() - interval {win} AND {f}"
    )
    out["paywall_viewed_distinct_persons"] = viewed_d
    purchasers_d = out.get("distinct_persons_paywall_purchase_success")
    if viewed_d and viewed_d > 0 and purchasers_d is not None:
        out["paywall_purchaser_conversion_from_viewed_pct"] = round(
            purchasers_d / viewed_d * 100, 2
        )
    out["distinct_persons_pageview_utm_cpc_ppc_paid"] = scalar(
        f"SELECT count(DISTINCT person_id) FROM events WHERE event = '$pageview' "
        f"AND timestamp > now() - interval {win} AND {f} AND "
        f"lower(coalesce(toString(properties.utm_medium), '')) IN ('cpc', 'ppc', 'paid')"
    )
    q_reviews = posthog_query(
        f"SELECT count(), count(DISTINCT person_id) FROM events WHERE event = 'review_prompt_requested' "
        f"AND timestamp > now() - interval {win} AND {f}",
        api_key,
        project_id,
        errors,
    )
    if q_reviews and q_reviews.get("results"):
        r0 = q_reviews["results"][0]
        if r0 and len(r0) >= 2:
            out["in_app_review_prompt_events"] = int(r0[0] or 0)
            out["in_app_review_prompt_distinct_persons"] = int(r0[1] or 0)

    q_screen = posthog_query(
        f"""
        SELECT coalesce(toString(properties.`$screen_name`), toString(properties.screen_name), '(unnamed)'),
               count(DISTINCT person_id), count()
        FROM events WHERE event = '$screen' AND timestamp > now() - interval {win} AND {f}
        GROUP BY 1 ORDER BY 2 DESC LIMIT 12
        """,
        api_key,
        project_id,
        errors,
    )
    out["top_screens_by_distinct_persons"] = (q_screen or {}).get("results") or []

    q_exc = scalar(
        f"SELECT count() FROM events WHERE event = '$exception' "
        f"AND timestamp > now() - interval {win} AND {f}"
    )
    out["posthog_exception_events"] = q_exc
    out["metric_bundle_id"] = POSTHOG_EXECUTIVE_METRIC_BUNDLE_ID
    out["metric_field_ids"] = dict(POSTHOG_EXECUTIVE_METRIC_FIELD_IDS)
    if errors:
        out["query_errors"] = errors[:20]
    return out


def run(
    repo_root: Path,
    days: int = 30,
    crashlytics_hours: int = 168,
    load_dotenv: bool = True,
) -> Dict[str, Any]:
    if load_dotenv:
        load_repo_dotenv(repo_root)

    generated_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()

    ph_key, ph_proj = _posthog_credentials()
    posthog = _posthog_section(ph_proj, ph_key, days)

    try:
        from real_store_downloads import _get_android_data, _get_ios_data
    except Exception as exc:
        android = {"status": "error", "reason": f"import real_store_downloads: {exc}"}
        ios = {"status": "error", "reason": f"import real_store_downloads: {exc}"}
    else:
        try:
            android = _get_android_data(days)
        except Exception as exc:
            android = {"status": "error", "reason": str(exc)}
        try:
            ios = _get_ios_data(days)
        except Exception as exc:
            ios = {"status": "error", "reason": str(exc)}

    try:
        from check_crashlytics import collect_crashlytics_snapshot

        crashlytics = collect_crashlytics_snapshot(hours=crashlytics_hours)
    except Exception as exc:
        crashlytics = {"status": "error", "reason": str(exc), "source": "crashlytics"}

    try:
        from store_sales_ledger import fetch_ios_sales_daily_summary

        ios_ledger = fetch_ios_sales_daily_summary(days)
    except Exception as exc:
        ios_ledger = {"status": "error", "reason": str(exc), "metric_bundle_id": "asc_sales_daily_summary_tsv_v1"}

    ledger_revenue: Dict[str, Any] = {
        "ios_sales_reports_daily": ios_ledger,
        "android_play_billing": {
            "status": "skipped",
            "reason": "Play Console earnings not wired in executive snapshot (use Play financial exports).",
        },
    }

    payload: Dict[str, Any] = {
        "generated_at": generated_at,
        "source": "executive_metrics_snapshot",
        "reliability_contract_doc": "docs/OPERATIONAL_RELIABILITY.md",
        "definitions": {
            "install_proxy_posthog": "Distinct persons with event Application Installed (not store units).",
            "reviews_store": (
                "Play: reviews.list is comment-bearing reviews touched in the last 7 days only "
                "(per Google); star-only ratings omitted; can read 0 while the public listing shows "
                "reviews; pagination max 100/page. App Store: customerReviews first page only "
                "(limit 50, newest first), not lifetime total. Use review_count_metric_id under "
                "store_apis.android / store_apis.ios when present."
            ),
            "reviews_in_app": "PostHog review_prompt_requested / write_review_tapped (not published star count).",
            "paid_posthog": (
                "In-app telemetry: paywall_purchase_success / paywall_purchase_result (not Play/App Store "
                "revenue). Compare posthog.events_paywall_purchase_success_ios vs _android "
                "(properties.platform). Ledger: App Store Connect + Google Play billing."
            ),
            "paywall_revenue_event_properties": (
                "Sum of coalesce(properties.revenue, properties.price) on paywall_purchase_success "
                "within pragmatic_live + window_days. Semantics depend on client instrumentation "
                "(currency, tax); not store ledger."
            ),
            "ledger_revenue_ios_sales_reports": (
                "App Store Connect GET /v1/salesReports (SALES, DAILY, SUMMARY, 1_0) aggregated TSV "
                "columns when APPSTORE_VENDOR_NUMBER is set. Filtered to Apple Identifier "
                "6758355312 when the report includes that column."
            ),
            "marketing_utm_signal": (
                "Distinct persons with $pageview and utm_medium in (cpc, ppc, paid) — coarse paid-traffic "
                "proxy; not ad network attribution."
            ),
            "posthog_executive": (
                "HogQL scalars use audience_sql (PRAGMATIC_LIVE) and window_days except "
                "wqtu_7d_distinct_persons (fixed 7d). Filters exclude non–store-production "
                "distribution_channel (testflight, non_play_install, dev, emulator, etc.), "
                "is_internal, debug/sim events; legacy events without distribution_channel stay "
                "included as 'legacy'. Optional POSTHOG_EXECUTIVE_EXCLUDE_PERSON_IDS env. "
                "See posthog.metric_field_ids and posthog.audience_note."
            ),
            "crashes": (
                "Crashlytics BigQuery streaming export; posthog_exception_events is separate. "
                "crashlytics_bigquery.fatal_events_in_window is COUNT(*) of fatal rows in the "
                "lookback hours. fatal_events sums crash_count only within parsed top_fatal_issues "
                "(up to 10 rows displayed from top 20 SQL groups) — see metric_field_ids."
            ),
            "uninstalls": "Not available on iOS; Android uninstall metrics require Play reporting APIs (not in this script yet).",
            "wqtu": "Distinct persons with >=3 timer_completed events in the same window as window_days (supplementary).",
            "wqtu_7d": "North Star WQTU: distinct persons with >=3 timer_completed in trailing 7 days (canonical).",
            "started_and_completed_persons": "Distinct persons with at least one timer_completed in-window who also have at least one timer_started in-window.",
        },
        "posthog": posthog,
        "store_apis": {"android": android, "ios": ios},
        "ledger_revenue": ledger_revenue,
        "crashlytics_bigquery": crashlytics,
    }

    out_path = repo_root / "marketing" / "data" / "executive_metrics.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Executive metrics snapshot (PostHog + stores + Crashlytics)")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--days", type=int, default=30, help="PostHog window days")
    parser.add_argument(
        "--crashlytics-hours",
        type=int,
        default=168,
        help="Crashlytics BigQuery lookback (default 7d)",
    )
    parser.add_argument("--no-dotenv", action="store_true", help="Skip loading .env from repo root")
    parser.add_argument("--json-stdout", action="store_true", help="Print full JSON to stdout")
    args = parser.parse_args()

    payload = run(
        args.repo_root.resolve(),
        days=args.days,
        crashlytics_hours=args.crashlytics_hours,
        load_dotenv=not args.no_dotenv,
    )
    out_path = args.repo_root.resolve() / "marketing" / "data" / "executive_metrics.json"
    print("=" * 60)
    print("  EXECUTIVE METRICS SNAPSHOT")
    print("=" * 60)
    print(f"  Written: {out_path}")
    ph = payload.get("posthog") or {}
    print(f"  PostHog: {ph.get('status')}  installs(persons)={ph.get('distinct_persons_application_installed')}")
    if ph.get("status") == "ok":
        print(
            f"    timer: started(events)={ph.get('timer_started_events')} "
            f"completed(events)={ph.get('timer_completed_events')} "
            f"distinct_started={ph.get('distinct_persons_timer_started')} "
            f"distinct_completed={ph.get('distinct_persons_timer_completed')} "
            f"starters_who_completed={ph.get('distinct_persons_timer_started_and_completed')} "
            f"wqtu_{ph.get('window_days')}d={ph.get('wqtu_distinct_persons')} "
            f"wqtu_7d={ph.get('wqtu_7d_distinct_persons')}"
        )
        print(
            f"    revenue(proxy): sum_event_props={ph.get('paywall_revenue_sum_event_properties')} "
            f"paywall_viewers={ph.get('paywall_viewed_distinct_persons')} "
            f"conversion_vs_viewed_pct={ph.get('paywall_purchaser_conversion_from_viewed_pct')} "
            f"utm_paid_viewers={ph.get('distinct_persons_pageview_utm_cpc_ppc_paid')}"
        )
    lr = payload.get("ledger_revenue") or {}
    ios_l = (lr.get("ios_sales_reports_daily") or {}).get("status")
    print(f"  Ledger iOS sales API: {ios_l}")
    st = payload.get("store_apis") or {}
    print(f"  Android API: {(st.get('android') or {}).get('status')}")
    print(f"  iOS API: {(st.get('ios') or {}).get('status')}")
    cr = payload.get("crashlytics_bigquery") or {}
    print(
        f"  Crashlytics BQ: {cr.get('status')} "
        f"fatal_in_window={cr.get('fatal_events_in_window')} "
        f"fatal_top_groups_sum={cr.get('fatal_events')}"
    )
    print("=" * 60)
    if args.json_stdout:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
