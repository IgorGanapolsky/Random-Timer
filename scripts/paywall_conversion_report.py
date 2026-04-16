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

from store_downloads_snapshot import LIVE_EVENTS_PREDICATE, posthog_query


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
        "entry_points": [],
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
    entry_points = _entry_point_funnel(api_key, project_id, days, errors)

    payload["funnel"] = {
        **counts,
        "view_to_select_rate": _rate(counts["offer_selects"], counts["views"]),
        "select_to_attempt_rate": _rate(counts["purchase_attempts"], counts["offer_selects"]),
        "attempt_to_success_rate": _rate(counts["purchase_successes"], counts["purchase_attempts"]),
    }
    payload["top_failure_reasons"] = failures
    payload["entry_points"] = entry_points
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
