#!/usr/bin/env python3
"""Daily Conversion Dashboard — the ONE morning report the CEO looks at.

Funnel: first_open → timer_started → timer_completed →
        paywall_viewed → paywall_purchase_attempt → paywall_purchase_success

Outputs:
  - Console: colour-coded table with biggest-drop highlight
  - marketing/data/daily_dashboard.json (committed by CI)

Usage:
    python scripts/daily_conversion_dashboard.py
    python scripts/daily_conversion_dashboard.py --days 14 --output path/to/out.json
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SCRIPTS = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

from repo_dotenv import load_repo_dotenv

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

POSTHOG_HOST = "https://us.posthog.com"
POSTHOG_PROJECT_ID_DEFAULT = "299775"

FUNNEL_STEPS: List[Tuple[str, str]] = [
    ("first_open",                 "First Open"),
    ("timer_started",              "Timer Started"),
    ("timer_completed",            "Timer Completed"),
    ("paywall_viewed",             "Paywall Viewed"),
    ("paywall_purchase_attempt",   "Purchase Attempt"),
    ("paywall_purchase_success",   "Purchase Success"),
]

# Real-device live-user audience filter (no bots / simulators / internal)
LIVE_FILTER = """(
  lower(coalesce(properties.build_type, 'release')) != 'debug'
  AND lower(coalesce(properties.runtime_target, 'device')) NOT IN ('simulator', 'emulator')
  AND coalesce(toString(properties.is_internal), 'false') != 'true'
  AND coalesce(toString(properties.distribution_channel), 'legacy') NOT IN (
    'testflight', 'non_play_install', 'dev', 'emulator', 'simulator', 'ui_test'
  )
)"""

# ANSI colours (disabled when not a TTY)
_IS_TTY = sys.stdout.isatty()


def _c(code: str, text: str) -> str:
    if not _IS_TTY:
        return text
    return f"\033[{code}m{text}\033[0m"


RED    = lambda s: _c("31;1", s)
YELLOW = lambda s: _c("33;1", s)
GREEN  = lambda s: _c("32;1", s)
CYAN   = lambda s: _c("36;1", s)
BOLD   = lambda s: _c("1", s)
DIM    = lambda s: _c("2", s)

# ---------------------------------------------------------------------------
# PostHog helpers (self-contained — no dependency on other scripts)
# ---------------------------------------------------------------------------


def _get_creds() -> Tuple[str, str]:
    key = (
        os.environ.get("POSTHOG_PERSONAL_API_KEY", "").strip()
        or os.environ.get("POSTHOG_API_KEY", "").strip()
    )
    project_id = (
        os.environ.get("POSTHOG_PROJECT_ID", "").strip()
        or POSTHOG_PROJECT_ID_DEFAULT
    )
    return key, project_id


def _query(sql: str, api_key: str, project_id: str, errors: List[str]) -> Optional[Dict[str, Any]]:
    try:
        import requests
    except ImportError:
        errors.append("missing_dependency: requests  (pip install requests)")
        return None

    try:
        resp = requests.post(
            f"{POSTHOG_HOST}/api/projects/{project_id}/query/",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={"query": {"kind": "HogQLQuery", "query": sql}},
            timeout=30,
        )
    except Exception as exc:
        errors.append(f"request_error: {exc}")
        return None

    if resp.status_code >= 300:
        errors.append(f"http_{resp.status_code}: {resp.text[:300]}")
        return None
    try:
        return resp.json()
    except Exception as exc:
        errors.append(f"json_parse_error: {exc}")
        return None


def _scalar_int(sql: str, api_key: str, project_id: str, errors: List[str]) -> Optional[int]:
    data = _query(sql, api_key, project_id, errors)
    if not data or not data.get("results"):
        return None
    try:
        return int(data["results"][0][0] or 0)
    except (TypeError, ValueError, IndexError):
        return None


def _scalar_float(sql: str, api_key: str, project_id: str, errors: List[str]) -> Optional[float]:
    data = _query(sql, api_key, project_id, errors)
    if not data or not data.get("results"):
        return None
    try:
        return round(float(data["results"][0][0] or 0), 2)
    except (TypeError, ValueError, IndexError):
        return None


def _rows(sql: str, api_key: str, project_id: str, errors: List[str]) -> List[List[Any]]:
    data = _query(sql, api_key, project_id, errors)
    if not data or not data.get("results"):
        return []
    return data["results"]


# ---------------------------------------------------------------------------
# Funnel section
# ---------------------------------------------------------------------------


def _funnel_7d(api_key: str, project_id: str, errors: List[str]) -> List[Dict[str, Any]]:
    """Return funnel steps with distinct users + step/overall conversion rates."""
    steps: List[Dict[str, Any]] = []
    prev_count: Optional[int] = None
    first_count: Optional[int] = None

    for event, label in FUNNEL_STEPS:
        count = _scalar_int(
            f"SELECT count(DISTINCT person_id) FROM events "
            f"WHERE event = '{event}' "
            f"AND timestamp > now() - interval 7 day "
            f"AND {LIVE_FILTER}",
            api_key, project_id, errors,
        )
        step: Dict[str, Any] = {
            "event": event,
            "label": label,
            "distinct_users": count,
            "step_conversion_pct": None,
            "overall_conversion_pct": None,
        }
        if first_count is not None and first_count > 0 and count is not None:
            step["overall_conversion_pct"] = round(count / first_count * 100, 1)
        if prev_count is not None and prev_count > 0 and count is not None:
            step["step_conversion_pct"] = round(count / prev_count * 100, 1)
        elif prev_count is not None and prev_count == 0:
            step["step_conversion_pct"] = 0.0

        steps.append(step)
        if first_count is None:
            first_count = count
        prev_count = count

    return steps


def _biggest_drop(steps: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Return the step with the lowest step_conversion_pct (i.e. biggest drop)."""
    candidates = [
        s for s in steps[1:]  # skip first step (no previous)
        if s.get("step_conversion_pct") is not None
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda s: s["step_conversion_pct"])  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Daily trend section
# ---------------------------------------------------------------------------


def _daily_trend_7d(api_key: str, project_id: str, errors: List[str]) -> List[Dict[str, Any]]:
    """Daily unique users per funnel step for the last 7 days.

    Returns list of {date, step_counts: {event: count}} sorted ascending.
    """
    rows = _rows(
        f"SELECT toDate(timestamp) AS day, event, count(DISTINCT person_id) AS users "
        f"FROM events "
        f"WHERE event IN ({', '.join(repr(e) for e, _ in FUNNEL_STEPS)}) "
        f"AND timestamp > now() - interval 7 day "
        f"AND {LIVE_FILTER} "
        f"GROUP BY day, event "
        f"ORDER BY day",
        api_key, project_id, errors,
    )

    # Aggregate by date
    by_date: Dict[str, Dict[str, int]] = {}
    for row in rows:
        date_str = str(row[0])
        event = str(row[1])
        users = int(row[2] or 0)
        if date_str not in by_date:
            by_date[date_str] = {}
        by_date[date_str][event] = users

    result = []
    for date_str in sorted(by_date):
        counts = by_date[date_str]
        entry: Dict[str, Any] = {"date": date_str, "step_counts": counts}

        # Compute top-of-funnel → bottom-of-funnel conversion for each day
        top = counts.get("first_open", 0)
        bottom = counts.get("paywall_purchase_success", 0)
        entry["full_funnel_pct"] = round(bottom / top * 100, 2) if top > 0 else 0.0
        result.append(entry)

    return result


def _trend_direction(trend: List[Dict[str, Any]]) -> str:
    """'improving', 'declining', 'flat', or 'insufficient_data'."""
    if len(trend) < 3:
        return "insufficient_data"
    rates = [d["full_funnel_pct"] for d in trend]
    # Compare average of last 3 days vs average of first 3 days
    early_avg = sum(rates[:3]) / 3
    late_avg  = sum(rates[-3:]) / 3
    delta = late_avg - early_avg
    if delta > 0.05:
        return "improving"
    if delta < -0.05:
        return "declining"
    return "flat"


# ---------------------------------------------------------------------------
# Revenue section
# ---------------------------------------------------------------------------


def _revenue_7d(api_key: str, project_id: str, errors: List[str]) -> Dict[str, Any]:
    purchase_events = _scalar_int(
        f"SELECT count() FROM events "
        f"WHERE event = 'paywall_purchase_success' "
        f"AND timestamp > now() - interval 7 day "
        f"AND {LIVE_FILTER}",
        api_key, project_id, errors,
    )
    purchase_users = _scalar_int(
        f"SELECT count(DISTINCT person_id) FROM events "
        f"WHERE event = 'paywall_purchase_success' "
        f"AND timestamp > now() - interval 7 day "
        f"AND {LIVE_FILTER}",
        api_key, project_id, errors,
    )
    revenue_sum = _scalar_float(
        f"SELECT sum(toFloat64OrZero(toString(coalesce("
        f"  properties.revenue, properties.price, '0'"
        f")))) FROM events "
        f"WHERE event = 'paywall_purchase_success' "
        f"AND timestamp > now() - interval 7 day "
        f"AND {LIVE_FILTER}",
        api_key, project_id, errors,
    )
    # Daily revenue breakdown
    daily_rev_rows = _rows(
        f"SELECT toDate(timestamp) AS day, "
        f"  count() AS purchases, "
        f"  sum(toFloat64OrZero(toString(coalesce(properties.revenue, properties.price, '0')))) AS rev "
        f"FROM events "
        f"WHERE event = 'paywall_purchase_success' "
        f"AND timestamp > now() - interval 7 day "
        f"AND {LIVE_FILTER} "
        f"GROUP BY day ORDER BY day",
        api_key, project_id, errors,
    )
    target_daily = 100.0  # CEO north star: $100/day
    avg_daily_rev = round((revenue_sum or 0) / 7, 2)
    pct_to_target = round(avg_daily_rev / target_daily * 100, 1) if target_daily > 0 else 0.0

    return {
        "purchase_events_7d": purchase_events,
        "purchase_users_7d": purchase_users,
        "revenue_sum_7d": revenue_sum,
        "avg_daily_revenue": avg_daily_rev,
        "target_daily_revenue": target_daily,
        "pct_to_daily_target": pct_to_target,
        "daily_breakdown": [
            {
                "date": str(r[0]),
                "purchases": int(r[1] or 0),
                "revenue": round(float(r[2] or 0), 2),
            }
            for r in daily_rev_rows
        ],
    }


# ---------------------------------------------------------------------------
# WQTU section
# ---------------------------------------------------------------------------


def _wqtu_7d(api_key: str, project_id: str, errors: List[str]) -> Dict[str, Any]:
    wqtu = _scalar_int(
        f"SELECT count() FROM ("
        f"  SELECT person_id, count() AS c FROM events "
        f"  WHERE event = 'timer_completed' "
        f"  AND timestamp > now() - interval 7 day "
        f"  AND {LIVE_FILTER} "
        f"  GROUP BY person_id HAVING c >= 3"
        f")",
        api_key, project_id, errors,
    )
    # Weekly trend: WQTU for each of the last 4 weeks
    weekly_rows = _rows(
        f"SELECT week, count() AS wqtu "
        f"FROM ("
        f"  SELECT toStartOfWeek(timestamp) AS week, person_id, count() AS c "
        f"  FROM events "
        f"  WHERE event = 'timer_completed' "
        f"  AND timestamp > now() - interval 28 day "
        f"  AND {LIVE_FILTER} "
        f"  GROUP BY week, person_id HAVING c >= 3"
        f") GROUP BY week ORDER BY week",
        api_key, project_id, errors,
    )
    return {
        "wqtu": wqtu,
        "definition": "Users with >= 3 timer_completed in trailing 7 days",
        "weekly_trend": [
            {"week_start": str(r[0]), "wqtu": int(r[1] or 0)}
            for r in weekly_rows
        ],
    }


# ---------------------------------------------------------------------------
# Dashboard builder
# ---------------------------------------------------------------------------


def build_dashboard(days: int = 7, load_dotenv: bool = True) -> Dict[str, Any]:
    if load_dotenv:
        load_repo_dotenv(REPO_ROOT)

    api_key, project_id = _get_creds()
    generated_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    errors: List[str] = []

    if not api_key:
        return {
            "generated_at": generated_at,
            "status": "skipped",
            "reason": "POSTHOG_PERSONAL_API_KEY not set",
        }

    funnel_steps = _funnel_7d(api_key, project_id, errors)
    drop_step = _biggest_drop(funnel_steps)
    trend = _daily_trend_7d(api_key, project_id, errors)
    revenue = _revenue_7d(api_key, project_id, errors)
    wqtu = _wqtu_7d(api_key, project_id, errors)

    dashboard: Dict[str, Any] = {
        "generated_at": generated_at,
        "status": "ok" if not errors else "degraded",
        "source": "daily_conversion_dashboard",
        "host": POSTHOG_HOST,
        "project_id": project_id,
        "audience": "live_real_device",
        "window_days": 7,
        "funnel_7d": {
            "steps": funnel_steps,
            "biggest_drop": drop_step,
            "priority_action": (
                f"Fix drop at '{drop_step['label']}' step "
                f"({drop_step['step_conversion_pct']}% step conversion)"
                if drop_step else None
            ),
        },
        "daily_trend": {
            "days": trend,
            "direction": _trend_direction(trend),
        },
        "revenue": revenue,
        "wqtu": wqtu,
    }

    if errors:
        dashboard["query_errors"] = errors[:30]
        dashboard["status"] = "degraded"

    return dashboard


# ---------------------------------------------------------------------------
# Console rendering
# ---------------------------------------------------------------------------


def _fmt_pct(val: Optional[float]) -> str:
    if val is None:
        return DIM("   n/a")
    colour = GREEN if val >= 50 else (YELLOW if val >= 20 else RED)
    return colour(f"{val:6.1f}%")


def _fmt_users(val: Optional[int]) -> str:
    if val is None:
        return DIM("      -")
    return f"{val:7,}"


def print_dashboard(dash: Dict[str, Any]) -> None:
    w = 72
    print()
    print(BOLD("=" * w))
    print(BOLD("  DAILY CONVERSION DASHBOARD  —  Random Timer"))
    print(BOLD("=" * w))
    print(f"  Generated : {dash.get('generated_at')}")
    print(f"  Status    : {dash.get('status')}")
    print(f"  Window    : last 7 days  |  Audience: live real-device users")
    print()

    # ── Funnel ──────────────────────────────────────────────────────────────
    print(BOLD("  CONVERSION FUNNEL (7d)"))
    print(f"  {'Step':<28} {'Users':>8}  {'Step Conv':>10}  {'Overall':>8}")
    print(f"  {'-'*28}  {'-'*8}  {'-'*10}  {'-'*8}")

    funnel = dash.get("funnel_7d", {})
    steps = funnel.get("steps", [])
    drop_event = (funnel.get("biggest_drop") or {}).get("event", "")

    for i, step in enumerate(steps):
        label = step["label"]
        marker = " ◄ #1 FIX" if step["event"] == drop_event and i > 0 else ""
        step_pct = _fmt_pct(step.get("step_conversion_pct"))
        overall_pct = _fmt_pct(step.get("overall_conversion_pct"))
        users = _fmt_users(step.get("distinct_users"))
        line = f"  {label:<28} {users}  {step_pct}  {overall_pct}"
        if marker:
            line += RED(marker)
        print(line)

    print()
    drop = funnel.get("biggest_drop")
    if drop:
        print(RED(f"  >> #1 PRIORITY: {drop['label']} step — only {drop['step_conversion_pct']}% pass through"))
        action = funnel.get("priority_action")
        if action:
            print(RED(f"     {action}"))
    print()

    # ── Trend ───────────────────────────────────────────────────────────────
    trend_data = dash.get("daily_trend", {})
    direction = trend_data.get("direction", "unknown")
    dir_str = {
        "improving":        GREEN("↑ IMPROVING"),
        "declining":        RED("↓ DECLINING"),
        "flat":             YELLOW("→ FLAT"),
        "insufficient_data": DIM("~ INSUFFICIENT DATA"),
    }.get(direction, direction)

    print(BOLD("  DAILY TREND (7d full-funnel conversion %)"))
    print(f"  Direction: {dir_str}")
    days_list = trend_data.get("days", [])
    if days_list:
        print(f"  {'Date':<12}  {'Full Funnel%':>14}  {'first_open':>11}  {'purchase_ok':>12}")
        print(f"  {'-'*12}  {'-'*14}  {'-'*11}  {'-'*12}")
        for d in days_list[-7:]:
            counts = d.get("step_counts", {})
            fo = counts.get("first_open", 0)
            ps = counts.get("paywall_purchase_success", 0)
            ffp = d.get("full_funnel_pct", 0)
            print(f"  {d['date']:<12}  {_fmt_pct(ffp):>14}  {fo:>11,}  {ps:>12,}")
    print()

    # ── Revenue ─────────────────────────────────────────────────────────────
    rev = dash.get("revenue", {})
    target = rev.get("target_daily_revenue", 100)
    avg = rev.get("avg_daily_revenue", 0)
    pct = rev.get("pct_to_daily_target", 0)
    rev_colour = GREEN if pct >= 100 else (YELLOW if pct >= 50 else RED)

    print(BOLD("  REVENUE (7d)"))
    print(f"  Purchases (events) : {rev.get('purchase_events_7d')}")
    print(f"  Buying users       : {rev.get('purchase_users_7d')}")
    print(f"  Revenue sum 7d     : ${rev.get('revenue_sum_7d', 0):,.2f}")
    print(f"  Avg daily revenue  : {rev_colour(f'${avg:,.2f}')}")
    print(f"  Daily target       : ${target:,.2f}  |  {rev_colour(f'{pct:.1f}% to target')}")
    print()

    # ── WQTU ────────────────────────────────────────────────────────────────
    wqtu_data = dash.get("wqtu", {})
    wqtu_val = wqtu_data.get("wqtu")
    wqtu_colour = GREEN if (wqtu_val or 0) > 0 else RED
    print(BOLD("  WQTU — North Star Metric (7d)"))
    print(f"  Definition: {wqtu_data.get('definition')}")
    print(f"  WQTU (7d) : {wqtu_colour(str(wqtu_val))}")
    trend_rows = wqtu_data.get("weekly_trend", [])
    if trend_rows:
        print(f"  Weekly trend:")
        for row in trend_rows:
            print(f"    {row['week_start']}  WQTU={row['wqtu']}")
    print()

    # ── Errors ──────────────────────────────────────────────────────────────
    errs = dash.get("query_errors", [])
    if errs:
        print(YELLOW(f"  QUERY WARNINGS ({len(errs)}):"))
        for e in errs[:5]:
            print(YELLOW(f"    - {e}"))
        print()

    print(BOLD("=" * w))
    print()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="CEO daily conversion dashboard from PostHog"
    )
    parser.add_argument(
        "--days", type=int, default=7,
        help="Lookback window in days (default: 7)",
    )
    parser.add_argument(
        "--output", type=str,
        default=None,
        help="JSON output path (default: marketing/data/daily_dashboard.json)",
    )
    parser.add_argument(
        "--no-dotenv", action="store_true",
        help="Skip loading .env from repo root",
    )
    parser.add_argument(
        "--json-only", action="store_true",
        help="Print JSON to stdout only (no console table)",
    )
    args = parser.parse_args()

    dashboard = build_dashboard(
        days=args.days,
        load_dotenv=not args.no_dotenv,
    )

    # Determine output path
    out_path_str = args.output or str(REPO_ROOT / "marketing" / "data" / "daily_dashboard.json")
    out_path = Path(out_path_str)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(dashboard, indent=2) + "\n", encoding="utf-8")

    if args.json_only or os.environ.get("CI", "").lower() in ("true", "1"):
        # In CI: print JSON to stdout so it appears in the Actions log
        print(json.dumps(dashboard, indent=2))
    else:
        print_dashboard(dashboard)
        print(f"  Saved to: {out_path}", file=sys.stderr)

    status = dashboard.get("status", "ok")
    return 0 if status in ("ok", "degraded") else 1


if __name__ == "__main__":
    raise SystemExit(main())
