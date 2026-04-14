#!/usr/bin/env python3
"""Comprehensive PostHog analytics dashboard.

Queries PostHog HogQL API to build a full-funnel dashboard covering:
- Install funnel with conversion rates (7d and 30d)
- Engagement metrics (WQTU, DAU, avg completions)
- Feature popularity breakdowns
- Revenue metrics
- Retention (daily timer_completed, new vs returning)

Outputs JSON to stdout. Designed for CI (env vars for auth) or local (.env).

Usage:
    python scripts/posthog_dashboard.py --days 30
    python scripts/posthog_dashboard.py --days 7 --json-stdout
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

SCRIPTS = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

from repo_dotenv import load_repo_dotenv

POSTHOG_HOST = "https://us.posthog.com"

# Audience filter: non-debug, real device, not internal
PRAGMATIC_LIVE = """(
  lower(coalesce(properties.build_type, 'release')) != 'debug'
  AND lower(coalesce(properties.runtime_target, 'device')) NOT IN ('simulator', 'emulator')
  AND coalesce(toString(properties.is_internal), 'false') != 'true'
  AND coalesce(toString(properties.distribution_channel), 'legacy') NOT IN (
    'testflight', 'non_play_install', 'dev', 'emulator', 'simulator', 'ui_test'
  )
)"""


def _posthog_credentials() -> tuple[str, str]:
    key = (
        os.environ.get("POSTHOG_PERSONAL_API_KEY", "").strip()
        or os.environ.get("POSTHOG_API_KEY", "").strip()
        or os.environ.get("posthog_api_key", "").strip()
    )
    project_id = os.environ.get("POSTHOG_PROJECT_ID", "").strip()
    return key, project_id


def _requests_module():
    try:
        import requests
        return requests
    except ImportError:
        return None


def posthog_query(
    sql: str, api_key: str, project_id: str, errors: List[str]
) -> Optional[Dict[str, Any]]:
    """Execute a HogQL query and return JSON payload."""
    requests = _requests_module()
    if requests is None:
        errors.append("missing_dependency: requests")
        return None

    try:
        response = requests.post(
            f"{POSTHOG_HOST}/api/projects/{project_id}/query/",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={"query": {"kind": "HogQLQuery", "query": sql}},
            timeout=30,
        )
    except requests.RequestException as exc:
        errors.append(f"request_error: {exc}")
        return None

    if response.status_code >= 300:
        errors.append(f"http_{response.status_code}: {response.text[:200]}")
        return None
    try:
        return response.json()
    except Exception as exc:
        errors.append(f"json_parse_error: {exc}")
        return None


def _scalar(
    sql: str, api_key: str, project_id: str, errors: List[str]
) -> Optional[int]:
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


def _scalar_float(
    sql: str, api_key: str, project_id: str, errors: List[str]
) -> Optional[float]:
    data = posthog_query(sql, api_key, project_id, errors)
    if not data or not data.get("results"):
        return None
    row = data["results"][0]
    if not row:
        return None
    try:
        return round(float(row[0] or 0), 2)
    except (TypeError, ValueError):
        return None


def _rows(
    sql: str, api_key: str, project_id: str, errors: List[str]
) -> List[List[Any]]:
    data = posthog_query(sql, api_key, project_id, errors)
    if not data or not data.get("results"):
        return []
    return data["results"]


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

def _funnel_section(
    api_key: str, project_id: str, errors: List[str]
) -> Dict[str, Any]:
    """Install funnel with conversion rates for 7d and 30d windows."""
    f = PRAGMATIC_LIVE
    funnel_events = [
        ("Application Installed", "application_installed"),
        ("first_open", "first_open"),
        ("first_timer_configured", "first_timer_configured"),
        ("timer_completed", "timer_completed"),
        ("paywall_viewed", "paywall_viewed"),
        ("paywall_purchase_success", "paywall_purchase_success"),
    ]

    result: Dict[str, Any] = {}
    for window_label, window_days in [("7d", 7), ("30d", 30)]:
        win = f"{window_days} day"
        steps = []
        prev_count: Optional[int] = None
        first_count: Optional[int] = None
        for event_name, key in funnel_events:
            count = _scalar(
                f"SELECT count(DISTINCT person_id) FROM events "
                f"WHERE event = '{event_name}' "
                f"AND timestamp > now() - interval {win} AND {f}",
                api_key, project_id, errors,
            )
            step: Dict[str, Any] = {
                "event": event_name,
                "distinct_users": count,
            }
            if first_count is not None and first_count > 0 and count is not None:
                step["overall_conversion_pct"] = round(count / first_count * 100, 2)
            if prev_count is not None and prev_count > 0 and count is not None:
                step["step_conversion_pct"] = round(count / prev_count * 100, 2)
            steps.append(step)
            if first_count is None:
                first_count = count
            prev_count = count
        result[window_label] = {"window_days": window_days, "steps": steps}

    return result


def _engagement_section(
    api_key: str, project_id: str, days: int, errors: List[str]
) -> Dict[str, Any]:
    """WQTU, DAU, avg timer_completed per user per week."""
    f = PRAGMATIC_LIVE

    # WQTU: distinct users with >=3 timer_completed in trailing 7 days
    wqtu = _scalar(
        f"SELECT count() FROM ("
        f"  SELECT person_id, count() AS c FROM events "
        f"  WHERE event = 'timer_completed' "
        f"  AND timestamp > now() - interval 7 day AND {f} "
        f"  GROUP BY person_id HAVING c >= 3"
        f")",
        api_key, project_id, errors,
    )

    # DAU: distinct users with any event today
    dau = _scalar(
        f"SELECT count(DISTINCT person_id) FROM events "
        f"WHERE timestamp > now() - interval 1 day AND {f}",
        api_key, project_id, errors,
    )

    # Average timer_completed per user per week (over the window)
    avg_completions_per_user_week = _scalar_float(
        f"SELECT avg(c) FROM ("
        f"  SELECT person_id, count() AS c FROM events "
        f"  WHERE event = 'timer_completed' "
        f"  AND timestamp > now() - interval 7 day AND {f} "
        f"  GROUP BY person_id"
        f")",
        api_key, project_id, errors,
    )

    # Weekly active users (any event in trailing 7d)
    wau = _scalar(
        f"SELECT count(DISTINCT person_id) FROM events "
        f"WHERE timestamp > now() - interval 7 day AND {f}",
        api_key, project_id, errors,
    )

    return {
        "wqtu_7d": wqtu,
        "dau": dau,
        "wau_7d": wau,
        "avg_timer_completed_per_user_7d": avg_completions_per_user_week,
        "window_days": days,
    }


def _feature_popularity_section(
    api_key: str, project_id: str, days: int, errors: List[str]
) -> Dict[str, Any]:
    """Feature popularity breakdowns."""
    f = PRAGMATIC_LIVE
    win = f"{days} day"

    # voice_gender_selected breakdown
    voice_gender = _rows(
        f"SELECT coalesce(toString(properties.gender), '(unknown)'), "
        f"count(), count(DISTINCT person_id) FROM events "
        f"WHERE event = 'voice_gender_selected' "
        f"AND timestamp > now() - interval {win} AND {f} "
        f"GROUP BY 1 ORDER BY 2 DESC LIMIT 10",
        api_key, project_id, errors,
    )

    # feature_gate_hit breakdown
    feature_gates = _rows(
        f"SELECT coalesce(toString(properties.feature), toString(properties.`$feature_flag`), '(unknown)'), "
        f"count(), count(DISTINCT person_id) FROM events "
        f"WHERE event = 'feature_gate_hit' "
        f"AND timestamp > now() - interval {win} AND {f} "
        f"GROUP BY 1 ORDER BY 2 DESC LIMIT 20",
        api_key, project_id, errors,
    )

    # settings_changed breakdown
    settings_changed = _rows(
        f"SELECT coalesce(toString(properties.setting), toString(properties.changed_property), '(unknown)'), "
        f"count(), count(DISTINCT person_id) FROM events "
        f"WHERE event = 'settings_changed' "
        f"AND timestamp > now() - interval {win} AND {f} "
        f"GROUP BY 1 ORDER BY 2 DESC LIMIT 20",
        api_key, project_id, errors,
    )

    # Most common timer range (min/max)
    timer_ranges = _rows(
        f"SELECT "
        f"  coalesce(toString(properties.min_seconds), '?'), "
        f"  coalesce(toString(properties.max_seconds), '?'), "
        f"  count(), count(DISTINCT person_id) "
        f"FROM events "
        f"WHERE event IN ('timer_started', 'first_timer_configured') "
        f"AND timestamp > now() - interval {win} AND {f} "
        f"GROUP BY 1, 2 ORDER BY 3 DESC LIMIT 10",
        api_key, project_id, errors,
    )

    return {
        "voice_gender_selected": [
            {"gender": r[0], "events": r[1], "distinct_users": r[2]}
            for r in voice_gender
        ],
        "feature_gate_hit": [
            {"feature": r[0], "events": r[1], "distinct_users": r[2]}
            for r in feature_gates
        ],
        "settings_changed": [
            {"setting": r[0], "events": r[1], "distinct_users": r[2]}
            for r in settings_changed
        ],
        "top_timer_ranges": [
            {"min_seconds": r[0], "max_seconds": r[1], "events": r[2], "distinct_users": r[3]}
            for r in timer_ranges
        ],
    }


def _revenue_section(
    api_key: str, project_id: str, days: int, errors: List[str]
) -> Dict[str, Any]:
    """Revenue: paywall_purchase_success count/sum, conversion from viewed."""
    f = PRAGMATIC_LIVE
    win = f"{days} day"

    purchase_count = _scalar(
        f"SELECT count() FROM events "
        f"WHERE event = 'paywall_purchase_success' "
        f"AND timestamp > now() - interval {win} AND {f}",
        api_key, project_id, errors,
    )

    purchase_distinct = _scalar(
        f"SELECT count(DISTINCT person_id) FROM events "
        f"WHERE event = 'paywall_purchase_success' "
        f"AND timestamp > now() - interval {win} AND {f}",
        api_key, project_id, errors,
    )

    purchase_revenue = _scalar_float(
        f"SELECT sum(toFloat64OrZero(toString(coalesce(properties.revenue, properties.price, '0')))) "
        f"FROM events "
        f"WHERE event = 'paywall_purchase_success' "
        f"AND timestamp > now() - interval {win} AND {f}",
        api_key, project_id, errors,
    )

    paywall_viewed = _scalar(
        f"SELECT count(DISTINCT person_id) FROM events "
        f"WHERE event = 'paywall_viewed' "
        f"AND timestamp > now() - interval {win} AND {f}",
        api_key, project_id, errors,
    )

    conversion_rate = None
    if paywall_viewed and paywall_viewed > 0 and purchase_distinct is not None:
        conversion_rate = round(purchase_distinct / paywall_viewed * 100, 2)

    return {
        "paywall_purchase_success_events": purchase_count,
        "paywall_purchase_success_distinct_users": purchase_distinct,
        "paywall_revenue_sum": purchase_revenue,
        "paywall_viewed_distinct_users": paywall_viewed,
        "paywall_conversion_rate_pct": conversion_rate,
        "window_days": days,
    }


def _retention_section(
    api_key: str, project_id: str, errors: List[str]
) -> Dict[str, Any]:
    """Daily timer_completed over last 30 days + new vs returning users."""
    f = PRAGMATIC_LIVE

    # Daily timer_completed for last 30 days
    daily_completions = _rows(
        f"SELECT toDate(timestamp) AS day, count(), count(DISTINCT person_id) "
        f"FROM events "
        f"WHERE event = 'timer_completed' "
        f"AND timestamp > now() - interval 30 day AND {f} "
        f"GROUP BY day ORDER BY day",
        api_key, project_id, errors,
    )

    # New users (first seen in last 7d) vs returning (first seen before last 7d)
    # who had any event in last 7d
    new_users_7d = _scalar(
        f"SELECT count(DISTINCT e.person_id) FROM events e "
        f"INNER JOIN ("
        f"  SELECT person_id, min(timestamp) AS first_seen FROM events "
        f"  WHERE {f} GROUP BY person_id"
        f") f ON e.person_id = f.person_id "
        f"WHERE e.timestamp > now() - interval 7 day AND {f} "
        f"AND f.first_seen > now() - interval 7 day",
        api_key, project_id, errors,
    )

    returning_users_7d = _scalar(
        f"SELECT count(DISTINCT e.person_id) FROM events e "
        f"INNER JOIN ("
        f"  SELECT person_id, min(timestamp) AS first_seen FROM events "
        f"  WHERE {f} GROUP BY person_id"
        f") f ON e.person_id = f.person_id "
        f"WHERE e.timestamp > now() - interval 7 day AND {f} "
        f"AND f.first_seen <= now() - interval 7 day",
        api_key, project_id, errors,
    )

    return {
        "daily_timer_completed_30d": [
            {"date": str(r[0]), "events": r[1], "distinct_users": r[2]}
            for r in daily_completions
        ],
        "new_users_7d": new_users_7d,
        "returning_users_7d": returning_users_7d,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build_dashboard(
    days: int = 30,
    load_dotenv: bool = True,
) -> Dict[str, Any]:
    if load_dotenv:
        load_repo_dotenv(REPO_ROOT)

    api_key, project_id = _posthog_credentials()
    errors: List[str] = []
    generated_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()

    if not api_key or not project_id:
        return {
            "generated_at": generated_at,
            "status": "skipped",
            "reason": "missing POSTHOG_PERSONAL_API_KEY or POSTHOG_PROJECT_ID",
        }

    dashboard: Dict[str, Any] = {
        "generated_at": generated_at,
        "status": "ok",
        "source": "posthog_dashboard",
        "host": POSTHOG_HOST,
        "project_id": project_id,
        "audience": "pragmatic_live",
        "window_days": days,
        "funnel": _funnel_section(api_key, project_id, errors),
        "engagement": _engagement_section(api_key, project_id, days, errors),
        "feature_popularity": _feature_popularity_section(api_key, project_id, days, errors),
        "revenue": _revenue_section(api_key, project_id, days, errors),
        "retention": _retention_section(api_key, project_id, errors),
    }

    if errors:
        dashboard["query_errors"] = errors[:30]

    return dashboard


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Comprehensive PostHog analytics dashboard"
    )
    parser.add_argument(
        "--days", type=int, default=30,
        help="Lookback window in days (default: 30)",
    )
    parser.add_argument(
        "--no-dotenv", action="store_true",
        help="Skip loading .env from repo root",
    )
    parser.add_argument(
        "--json-stdout", action="store_true",
        help="Print full JSON to stdout (always enabled in CI)",
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Write JSON to this file path (in addition to stdout)",
    )
    args = parser.parse_args()

    # In CI, always output JSON to stdout
    is_ci = os.environ.get("CI", "").lower() in ("true", "1")
    json_stdout = args.json_stdout or is_ci

    dashboard = build_dashboard(
        days=args.days,
        load_dotenv=not args.no_dotenv,
    )

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(dashboard, indent=2) + "\n", encoding="utf-8")
        print(f"Dashboard written to {out_path}", file=sys.stderr)

    if json_stdout:
        print(json.dumps(dashboard, indent=2))
    else:
        # Human-readable summary
        print("=" * 60)
        print("  POSTHOG ANALYTICS DASHBOARD")
        print("=" * 60)
        print(f"  Status: {dashboard.get('status')}")
        print(f"  Window: {dashboard.get('window_days')} days")
        print(f"  Generated: {dashboard.get('generated_at')}")
        print()

        eng = dashboard.get("engagement") or {}
        print(f"  WQTU (7d):  {eng.get('wqtu_7d')}")
        print(f"  DAU:        {eng.get('dau')}")
        print(f"  WAU (7d):   {eng.get('wau_7d')}")
        print(f"  Avg completions/user/week: {eng.get('avg_timer_completed_per_user_7d')}")
        print()

        rev = dashboard.get("revenue") or {}
        print(f"  Purchases:       {rev.get('paywall_purchase_success_events')}")
        print(f"  Revenue sum:     {rev.get('paywall_revenue_sum')}")
        print(f"  Paywall conv %:  {rev.get('paywall_conversion_rate_pct')}")
        print()

        funnel_30 = (dashboard.get("funnel") or {}).get("30d", {})
        steps = funnel_30.get("steps") or []
        if steps:
            print("  FUNNEL (30d):")
            for s in steps:
                conv = s.get("step_conversion_pct", "-")
                print(f"    {s['event']:40s} users={s.get('distinct_users')}  step_conv={conv}%")
        print()

        ret = dashboard.get("retention") or {}
        print(f"  New users (7d):       {ret.get('new_users_7d')}")
        print(f"  Returning users (7d): {ret.get('returning_users_7d')}")

        errs = dashboard.get("query_errors") or []
        if errs:
            print(f"\n  Errors ({len(errs)}):")
            for e in errs[:5]:
                print(f"    - {e}")
        print("=" * 60)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
