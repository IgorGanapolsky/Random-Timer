#!/usr/bin/env python3
"""Weekly paywall conversion and non-conversion diagnostics.

``paywall_purchase_attempt`` means native purchase flow start (see
``docs/POSTHOG_ANALYTICS.md`` § Paywall funnel semantics), not arbitrary CTA taps.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from repo_dotenv import load_repo_dotenv
from store_downloads_snapshot import LIVE_EVENTS_PREDICATE, posthog_query

PLAY_STORE_CATALOG_FILTER = (
    "AND coalesce(toString(properties.distribution_channel), 'legacy') IN ('play_store', 'legacy') "
    "AND coalesce(toString(properties.billing_ready), 'true') = 'true'"
)


def _safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(float(numerator) / float(denominator), 4)


def _scalar(query: str, api_key: str, project_id: str, errors: List[str]) -> int:
    result = posthog_query(query, api_key, project_id, errors)
    if not result or not result.get("results"):
        return 0
    row = result["results"][0]
    if not row:
        return 0
    return _safe_int(row[0])


def _table(
    query: str,
    api_key: str,
    project_id: str,
    errors: List[str],
) -> list[list[Any]]:
    result = posthog_query(query, api_key, project_id, errors)
    rows = (result or {}).get("results")
    if not isinstance(rows, list):
        return []
    return rows


def _funnel_counts(api_key: str, project_id: str, days: int, errors: List[str]) -> Dict[str, int]:
    win = f"{days} day"
    views = _scalar(
        f"""
        SELECT count()
        FROM events
        WHERE event IN ('paywall_view', 'paywall_viewed')
          AND timestamp > now() - interval {win}
          AND {LIVE_EVENTS_PREDICATE}
        """,
        api_key,
        project_id,
        errors,
    )
    offer_selects = _scalar(
        f"""
        SELECT count()
        FROM events
        WHERE event = 'paywall_offer_select'
          AND timestamp > now() - interval {win}
          AND {LIVE_EVENTS_PREDICATE}
        """,
        api_key,
        project_id,
        errors,
    )
    purchase_attempts = _scalar(
        f"""
        SELECT count()
        FROM events
        WHERE event = 'paywall_purchase_attempt'
          AND timestamp > now() - interval {win}
          AND {LIVE_EVENTS_PREDICATE}
        """,
        api_key,
        project_id,
        errors,
    )
    purchase_successes = _scalar(
        f"""
        SELECT count()
        FROM events
        WHERE event = 'paywall_purchase_success'
          AND timestamp > now() - interval {win}
          AND {LIVE_EVENTS_PREDICATE}
        """,
        api_key,
        project_id,
        errors,
    )
    return {
        "views": views,
        "offer_selects": offer_selects,
        "purchase_attempts": purchase_attempts,
        "purchase_successes": purchase_successes,
    }


def _failure_reasons(api_key: str, project_id: str, days: int, errors: List[str]) -> list[dict[str, Any]]:
    win = f"{days} day"
    rows = _table(
        f"""
        SELECT
          coalesce(
            toString(coalesce(properties.reason, properties.result, 'unknown')),
            'unknown'
          ) AS reason,
          count() AS failures
        FROM events
        WHERE event IN ('paywall_purchase_fail_reason', 'purchase_failed')
          AND timestamp > now() - interval {win}
          AND {LIVE_EVENTS_PREDICATE}
        GROUP BY reason
        ORDER BY failures DESC
        LIMIT 12
        /* top_failure_reasons */
        """,
        api_key,
        project_id,
        errors,
    )
    return [{"reason": str(row[0] or "unknown"), "count": _safe_int(row[1])} for row in rows]


def _failure_breakdown(api_key: str, project_id: str, days: int, errors: List[str]) -> list[dict[str, Any]]:
    win = f"{days} day"
    rows = _table(
        f"""
        SELECT
          coalesce(toString(properties.platform), 'unknown') AS platform,
          coalesce(toString(properties.product_id), 'unknown') AS product_id,
          coalesce(toString(coalesce(properties.reason, properties.result, 'unknown')), 'unknown') AS reason,
          count() AS failures,
          count(DISTINCT person_id) AS users
        FROM events
        WHERE event IN ('paywall_purchase_fail_reason', 'purchase_failed')
          AND timestamp > now() - interval {win}
          AND {LIVE_EVENTS_PREDICATE}
        GROUP BY platform, product_id, reason
        ORDER BY failures DESC
        LIMIT 25
        /* failure_breakdown */
        """,
        api_key,
        project_id,
        errors,
    )
    return [
        {
            "platform": str(row[0] or "unknown"),
            "product_id": str(row[1] or "unknown"),
            "reason": str(row[2] or "unknown"),
            "failures": _safe_int(row[3]),
            "users": _safe_int(row[4]),
        }
        for row in rows
    ]


def _product_funnel(api_key: str, project_id: str, days: int, errors: List[str]) -> list[dict[str, Any]]:
    win = f"{days} day"
    rows = _table(
        f"""
        SELECT
          coalesce(toString(properties.platform), 'unknown') AS platform,
          coalesce(toString(properties.product_id), 'unknown') AS product_id,
          countIf(event = 'paywall_offer_select') AS offer_selects,
          countIf(event = 'paywall_purchase_attempt') AS attempts,
          countIf(event = 'paywall_purchase_success') AS successes
        FROM events
        WHERE event IN ('paywall_offer_select', 'paywall_purchase_attempt', 'paywall_purchase_success')
          AND timestamp > now() - interval {win}
          AND {LIVE_EVENTS_PREDICATE}
        GROUP BY platform, product_id
        ORDER BY attempts DESC, offer_selects DESC
        LIMIT 25
        /* product_funnel */
        """,
        api_key,
        project_id,
        errors,
    )
    out: list[dict[str, Any]] = []
    for row in rows:
        offer_selects = _safe_int(row[2])
        attempts = _safe_int(row[3])
        successes = _safe_int(row[4])
        out.append(
            {
                "platform": str(row[0] or "unknown"),
                "product_id": str(row[1] or "unknown"),
                "offer_selects": offer_selects,
                "attempts": attempts,
                "successes": successes,
                "select_to_attempt_rate": _rate(attempts, offer_selects),
                "attempt_to_success_rate": _rate(successes, attempts),
            }
        )
    return out


def _product_catalog_failures(
    api_key: str,
    project_id: str,
    days: int,
    errors: List[str],
    *,
    play_store_only: bool = False,
) -> list[dict[str, Any]]:
    win = f"{days} day"
    channel_filter = PLAY_STORE_CATALOG_FILTER if play_store_only else ""
    query_tag = "product_catalog_failures_play_store" if play_store_only else "product_catalog_failures"
    rows = _table(
        f"""
        SELECT
          coalesce(toString(properties.platform), 'unknown') AS platform,
          coalesce(toString(properties.product_id), 'unknown') AS product_id,
          count() AS failures,
          count(DISTINCT person_id) AS users
        FROM events
        WHERE event = 'billing_product_not_found'
          AND timestamp > now() - interval {win}
          AND {LIVE_EVENTS_PREDICATE}
          {channel_filter}
        GROUP BY platform, product_id
        ORDER BY failures DESC
        LIMIT 25
        /* {query_tag} */
        """,
        api_key,
        project_id,
        errors,
    )
    return [
        {
            "platform": str(row[0] or "unknown"),
            "product_id": str(row[1] or "unknown"),
            "failures": _safe_int(row[2]),
            "users": _safe_int(row[3]),
        }
        for row in rows
    ]


def _entry_point_funnel(api_key: str, project_id: str, days: int, errors: List[str]) -> list[dict[str, Any]]:
    win = f"{days} day"
    rows = _table(
        f"""
        SELECT
          coalesce(toString(properties.entry_point), 'unknown') AS entry_point,
          countIf(event IN ('paywall_view', 'paywall_viewed')) AS views,
          countIf(event = 'paywall_purchase_attempt') AS attempts,
          countIf(event = 'paywall_purchase_success') AS successes
        FROM events
        WHERE event IN ('paywall_view', 'paywall_viewed', 'paywall_purchase_attempt', 'paywall_purchase_success')
          AND timestamp > now() - interval {win}
          AND {LIVE_EVENTS_PREDICATE}
        GROUP BY entry_point
        ORDER BY views DESC
        LIMIT 15
        /* entry_point_funnel */
        """,
        api_key,
        project_id,
        errors,
    )
    out: list[dict[str, Any]] = []
    for row in rows:
        views = _safe_int(row[1])
        attempts = _safe_int(row[2])
        successes = _safe_int(row[3])
        out.append(
            {
                "entry_point": str(row[0] or "unknown"),
                "views": views,
                "attempts": attempts,
                "successes": successes,
                "view_to_attempt_rate": _rate(attempts, views),
                "attempt_to_success_rate": _rate(successes, attempts),
            }
        )
    return out


def _settings_hotspots(api_key: str, project_id: str, days: int, errors: List[str]) -> list[dict[str, Any]]:
    win = f"{days} day"
    rows = _table(
        f"""
        SELECT
          coalesce(toString(properties.setting_name), 'unknown') AS setting_name,
          count() AS changes,
          count(DISTINCT person_id) AS users
        FROM events
        WHERE event = 'settings_changed'
          AND timestamp > now() - interval {win}
          AND {LIVE_EVENTS_PREDICATE}
        GROUP BY setting_name
        ORDER BY changes DESC
        LIMIT 15
        /* settings_hotspots */
        """,
        api_key,
        project_id,
        errors,
    )
    return [
        {
            "setting_name": str(row[0] or "unknown"),
            "changes": _safe_int(row[1]),
            "users": _safe_int(row[2]),
        }
        for row in rows
    ]


def _leaky_entry_points(entry_points: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in entry_points
        if _safe_int(row.get("views")) >= 20 and _safe_int(row.get("attempts")) == 0
    ]


def _data_quality_warnings(
    counts: dict[str, int],
    entry_points: list[dict[str, Any]],
    settings_hotspots: list[dict[str, Any]],
    failure_reasons: list[dict[str, Any]],
    product_catalog_failures: list[dict[str, Any]],
) -> list[str]:
    warnings: list[str] = []
    offer_selects = _safe_int(counts.get("offer_selects"))
    attempts = _safe_int(counts.get("purchase_attempts"))
    views = _safe_int(counts.get("views"))

    if attempts > offer_selects and offer_selects > 0:
        warnings.append(
            "purchase_attempts exceed offer_selects; paywall funnel events are inconsistent and need instrumentation review"
        )
    if attempts > views and views > 0:
        warnings.append(
            "purchase_attempts exceed paywall views; entry or purchase attempt events are being emitted without matching impressions"
        )
    if any(str(row.get("entry_point")) == "unknown" and _safe_int(row.get("views")) >= 20 for row in entry_points):
        warnings.append("unknown paywall entry_point is still receiving meaningful traffic")
    if settings_hotspots:
        top = settings_hotspots[0]
        if str(top.get("setting_name")) == "unknown" and _safe_int(top.get("changes")) >= 100:
            warnings.append("settings_changed is still dominated by unknown setting_name rows in live data")
    failure_total = sum(_safe_int(row.get("count")) for row in failure_reasons)
    user_cancelled = sum(
        _safe_int(row.get("count"))
        for row in failure_reasons
        if str(row.get("reason")) == "user_cancelled"
    )
    if failure_total > 0 and _rate(user_cancelled, failure_total) >= 0.75:
        warnings.append(
            "purchase failures are dominated by user_cancelled; prioritize pricing, plan default, and purchase-sheet value proof before assuming a store outage"
        )
    catalog_failure_total = sum(_safe_int(row.get("failures")) for row in product_catalog_failures)
    if catalog_failure_total > 0:
        warnings.append(
            "product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status"
        )
    return warnings


def build_markdown(payload: Dict[str, Any]) -> str:
    funnel = payload.get("funnel", {})
    lines = [
        "# Paywall Conversion Report",
        "",
        f"Generated: {payload.get('generated_at', '')}",
        f"Window (days): {payload.get('window_days', 30)}",
        "",
        "## Funnel",
        f"- Views: **{funnel.get('views', 0)}**",
        f"- Offer Selects: **{funnel.get('offer_selects', 0)}**",
        f"- Purchase Attempts: **{funnel.get('purchase_attempts', 0)}**",
        f"- Purchase Successes: **{funnel.get('purchase_successes', 0)}**",
        f"- View -> Offer Select: **{funnel.get('view_to_select_rate', 0):.1%}**",
        f"- Select -> Purchase Attempt: **{funnel.get('select_to_attempt_rate', 0):.1%}**",
        f"- Attempt -> Purchase Success: **{funnel.get('attempt_to_success_rate', 0):.1%}**",
        "",
        "## Top Failure Reasons",
        "| Reason | Count |",
        "|--------|-------|",
    ]
    for row in payload.get("top_failure_reasons", []):
        lines.append(f"| {row.get('reason', 'unknown')} | {row.get('count', 0)} |")
    if not payload.get("top_failure_reasons"):
        lines.append("| (none) | 0 |")

    lines.extend(
        [
            "",
            "## Failure Breakdown",
            "| Platform | Product ID | Reason | Failures | Users |",
            "|----------|------------|--------|----------|-------|",
        ]
    )
    for row in payload.get("failure_breakdown", []):
        lines.append(
            f"| {row.get('platform', 'unknown')} | {row.get('product_id', 'unknown')} | "
            f"{row.get('reason', 'unknown')} | {row.get('failures', 0)} | {row.get('users', 0)} |"
        )
    if not payload.get("failure_breakdown"):
        lines.append("| (none) | (none) | (none) | 0 | 0 |")

    lines.extend(
        [
            "",
            "## Product Funnel",
            "| Platform | Product ID | Selects | Attempts | Successes | Select->Attempt | Attempt->Success |",
            "|----------|------------|---------|----------|-----------|-----------------|------------------|",
        ]
    )
    for row in payload.get("product_funnel", []):
        lines.append(
            f"| {row.get('platform', 'unknown')} | {row.get('product_id', 'unknown')} | "
            f"{row.get('offer_selects', 0)} | {row.get('attempts', 0)} | {row.get('successes', 0)} | "
            f"{row.get('select_to_attempt_rate', 0):.1%} | {row.get('attempt_to_success_rate', 0):.1%} |"
        )
    if not payload.get("product_funnel"):
        lines.append("| (none) | (none) | 0 | 0 | 0 | 0.0% | 0.0% |")

    lines.extend(
        [
            "",
            "## Product Catalog Failures",
            "| Platform | Product ID | Failures | Users |",
            "|----------|------------|----------|-------|",
        ]
    )
    for row in payload.get("product_catalog_failures", []):
        lines.append(
            f"| {row.get('platform', 'unknown')} | {row.get('product_id', 'unknown')} | "
            f"{row.get('failures', 0)} | {row.get('users', 0)} |"
        )
    if not payload.get("product_catalog_failures"):
        lines.append("| (none) | (none) | 0 | 0 |")

    lines.extend(
        [
            "",
            "## Entry Point Funnel",
            "| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |",
            "|-------------|-------|----------|-----------|---------------|------------------|",
        ]
    )
    for row in payload.get("entry_points", []):
        lines.append(
            f"| {row.get('entry_point', 'unknown')} | {row.get('views', 0)} | "
            f"{row.get('attempts', 0)} | {row.get('successes', 0)} | "
            f"{row.get('view_to_attempt_rate', 0):.1%} | {row.get('attempt_to_success_rate', 0):.1%} |"
        )
    if not payload.get("entry_points"):
        lines.append("| (none) | 0 | 0 | 0 | 0.0% | 0.0% |")

    lines.extend(
        [
            "",
            "## Leaky Entry Points",
        ]
    )
    for row in payload.get("leaky_entry_points", []):
        lines.append(
            f"- `{row.get('entry_point', 'unknown')}` had **{row.get('views', 0)}** views and "
            f"**0** purchase attempts."
        )
    if not payload.get("leaky_entry_points"):
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Settings Hotspots",
            "| Setting | Changes | Users |",
            "|---------|---------|-------|",
        ]
    )
    for row in payload.get("settings_hotspots", []):
        lines.append(
            f"| {row.get('setting_name', 'unknown')} | {row.get('changes', 0)} | {row.get('users', 0)} |"
        )
    if not payload.get("settings_hotspots"):
        lines.append("| (none) | 0 | 0 |")

    lines.extend(
        [
            "",
            "## Data Quality Warnings",
        ]
    )
    for warning in payload.get("data_quality_warnings", []):
        lines.append(f"- {warning}")
    if not payload.get("data_quality_warnings"):
        lines.append("- None")

    if payload.get("query_errors"):
        lines.extend(
            [
                "",
                "## Query Diagnostics",
                f"- Query errors: **{len(payload.get('query_errors', []))}**",
                f"- Last error: `{payload['query_errors'][-1]}`",
            ]
        )
    return "\n".join(lines) + "\n"


def run(repo_root: Path, days: int = 30) -> Dict[str, Any]:
    load_repo_dotenv(repo_root)
    output_dir = repo_root / "marketing" / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "paywall_conversion_report.json"
    md_path = output_dir / "paywall_conversion_report.md"
    generated_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()

    api_key = (
        os.getenv("POSTHOG_PERSONAL_API_KEY", "").strip()
        or os.getenv("POSTHOG_API_KEY", "").strip()
        or os.getenv("posthog_api_key", "").strip()
    )
    project_id = os.getenv("POSTHOG_PROJECT_ID", "").strip()
    errors: list[str] = []

    payload: Dict[str, Any] = {
        "generated_at": generated_at,
        "window_days": int(days),
        "status": "ok",
        "reason": "",
        "funnel": {
            "views": 0,
            "offer_selects": 0,
            "purchase_attempts": 0,
            "purchase_successes": 0,
            "view_to_select_rate": 0.0,
            "select_to_attempt_rate": 0.0,
            "attempt_to_success_rate": 0.0,
        },
        "top_failure_reasons": [],
        "failure_breakdown": [],
        "product_funnel": [],
        "product_catalog_failures": [],
        "product_catalog_failures_play_store": [],
        "entry_points": [],
        "leaky_entry_points": [],
        "settings_hotspots": [],
        "data_quality_warnings": [],
        "query_errors": [],
    }

    if not api_key or not project_id:
        payload["status"] = "skipped"
        payload["reason"] = "missing POSTHOG_PERSONAL_API_KEY/POSTHOG_API_KEY or POSTHOG_PROJECT_ID"
        md = build_markdown(payload)
        json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        md_path.write_text(md, encoding="utf-8")
        return payload

    counts = _funnel_counts(api_key, project_id, days, errors)
    failures = _failure_reasons(api_key, project_id, days, errors)
    failure_breakdown = _failure_breakdown(api_key, project_id, days, errors)
    product_funnel = _product_funnel(api_key, project_id, days, errors)
    product_catalog_failures = _product_catalog_failures(api_key, project_id, days, errors)
    product_catalog_failures_play_store = _product_catalog_failures(
        api_key, project_id, days, errors, play_store_only=True
    )
    entry_points = _entry_point_funnel(api_key, project_id, days, errors)
    settings_hotspots = _settings_hotspots(api_key, project_id, days, errors)

    payload["funnel"] = {
        **counts,
        "view_to_select_rate": _rate(counts["offer_selects"], counts["views"]),
        "select_to_attempt_rate": _rate(counts["purchase_attempts"], counts["offer_selects"]),
        "attempt_to_success_rate": _rate(counts["purchase_successes"], counts["purchase_attempts"]),
    }
    payload["top_failure_reasons"] = failures
    payload["failure_breakdown"] = failure_breakdown
    payload["product_funnel"] = product_funnel
    payload["product_catalog_failures"] = product_catalog_failures
    payload["product_catalog_failures_play_store"] = product_catalog_failures_play_store
    payload["entry_points"] = entry_points
    payload["leaky_entry_points"] = _leaky_entry_points(entry_points)
    payload["settings_hotspots"] = settings_hotspots
    payload["data_quality_warnings"] = _data_quality_warnings(
        payload["funnel"],
        entry_points,
        settings_hotspots,
        failures,
        product_catalog_failures_play_store or product_catalog_failures,
    )
    payload["query_errors"] = errors
    if errors:
        payload["status"] = "degraded"
        payload["reason"] = "one or more PostHog queries failed"

    md = build_markdown(payload)
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(md, encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate paywall conversion report")
    parser.add_argument("--repo-root", default=".", help="Repository root")
    parser.add_argument("--days", type=int, default=30, help="Lookback window")
    args = parser.parse_args()
    result = run(Path(args.repo_root).resolve(), days=args.days)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
