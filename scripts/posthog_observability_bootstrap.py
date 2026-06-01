#!/usr/bin/env python3
"""Verify and optionally apply PostHog observability assets (saved HogQL + log alerts).

Reads marketing/data/posthog_observability.json, runs each saved HogQL query against the
live project (when POSTHOG_API_KEY + POSTHOG_PROJECT_ID are set), and writes
marketing/data/posthog_observability_status.json with evidence.

Log alerts (--apply-log-alerts) require POSTHOG_PERSONAL_API_KEY with logs scope.
Native apps emit billing_* events today; PostHog Logs OTLP is optional for CI/scripts.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path
from typing import Any

_SCRIPTS = Path(__file__).resolve().parent
REPO_ROOT = _SCRIPTS.parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from repo_dotenv import load_repo_dotenv
from store_downloads_snapshot import posthog_query

CONFIG_PATH = REPO_ROOT / "marketing" / "data" / "posthog_observability.json"
STATUS_PATH = REPO_ROOT / "marketing" / "data" / "posthog_observability_status.json"


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_config() -> dict[str, Any]:
    raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("posthog_observability.json must be a JSON object")
    return raw


def _posthog_credentials() -> tuple[str, str] | tuple[None, None]:
    api_key = os.environ.get("POSTHOG_API_KEY", "").strip()
    project_id = os.environ.get("POSTHOG_PROJECT_ID", "").strip()
    if api_key and project_id:
        return api_key, project_id
    return None, None


def verify_saved_queries(config: dict[str, Any]) -> list[dict[str, Any]]:
    queries = config.get("saved_queries") or []
    if not isinstance(queries, list):
        raise ValueError("saved_queries must be a list")

    api_key, project_id = _posthog_credentials()
    errors: list[str] = []
    results: list[dict[str, Any]] = []

    for item in queries:
        if not isinstance(item, dict):
            continue
        query_id = str(item.get("id") or "")
        hogql = str(item.get("hogql") or "").strip()
        entry: dict[str, Any] = {
            "id": query_id,
            "title": item.get("title"),
            "verified": False,
        }
        if not query_id or not hogql:
            entry["error"] = "missing id or hogql"
            results.append(entry)
            continue
        if not api_key or not project_id:
            entry["skipped"] = "POSTHOG_API_KEY or POSTHOG_PROJECT_ID unset"
            results.append(entry)
            continue

        payload = posthog_query(hogql, api_key, project_id, errors)
        if payload is None:
            entry["error"] = errors[-1] if errors else "query_failed"
        else:
            entry["verified"] = True
            entry["row_count"] = len((payload.get("results") or []))
            entry["results_preview"] = (payload.get("results") or [])[:5]
        results.append(entry)

    return results


def _requests_module():
    try:
        import requests

        return requests
    except ImportError:
        return None


def apply_log_alerts(config: dict[str, Any], *, dry_run: bool) -> list[dict[str, Any]]:
    templates = config.get("log_alert_templates") or []
    personal_key = os.environ.get("POSTHOG_PERSONAL_API_KEY", "").strip()
    project_id = os.environ.get("POSTHOG_PROJECT_ID", "").strip()
    host = str(config.get("posthog_host") or "https://us.i.posthog.com").rstrip("/")
    api_host = host.replace("i.posthog.com", "posthog.com")

    outcomes: list[dict[str, Any]] = []
    requests = _requests_module()

    for template in templates:
        if not isinstance(template, dict):
            continue
        alert_id = str(template.get("id") or "")
        enabled = bool(template.get("enabled", True))
        outcome: dict[str, Any] = {"id": alert_id, "applied": False}
        if not enabled:
            outcome["skipped"] = "template disabled in JSON"
            outcomes.append(outcome)
            continue
        if dry_run:
            outcome["skipped"] = "dry_run"
            outcomes.append(outcome)
            continue
        if not personal_key or not project_id:
            outcome["skipped"] = "POSTHOG_PERSONAL_API_KEY or POSTHOG_PROJECT_ID unset"
            outcomes.append(outcome)
            continue
        if requests is None:
            outcome["error"] = "requests not installed"
            outcomes.append(outcome)
            continue

        body = {
            "name": template.get("name") or alert_id,
            "enabled": True,
            "filters": template.get("filters") or {},
            "window_minutes": int(template.get("window_minutes") or 5),
            "threshold_count": int(template.get("threshold_count") or 1),
            "threshold_operator": template.get("threshold_operator") or "above",
        }
        url = f"{api_host}/api/projects/{project_id}/logs/alerts/"
        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {personal_key}",
                "Content-Type": "application/json",
            },
            json=body,
            timeout=60,
        )
        if response.status_code >= 300:
            outcome["error"] = f"http_{response.status_code}"
        else:
            try:
                outcome["applied"] = True
                outcome["remote_id"] = response.json().get("id")
            except Exception:
                outcome["applied"] = True
        outcomes.append(outcome)

    return outcomes


def write_status(
    config: dict[str, Any],
    query_results: list[dict[str, Any]],
    alert_results: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    status = {
        "generated_at": _utc_now(),
        "config_schema_version": config.get("schema_version"),
        "saved_queries": query_results,
        "log_alerts": alert_results or [],
        "all_queries_verified": all(r.get("verified") for r in query_results if "skipped" not in r),
    }
    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATUS_PATH.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    return status


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply-log-alerts",
        action="store_true",
        help="Create log alerts from log_alert_templates (requires personal API key).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="With --apply-log-alerts, print intent without POSTing.",
    )
    args = parser.parse_args()

    load_repo_dotenv(REPO_ROOT)
    config = load_config()
    query_results = verify_saved_queries(config)
    alert_results = (
        apply_log_alerts(config, dry_run=args.dry_run or not args.apply_log_alerts)
        if args.apply_log_alerts or args.dry_run
        else None
    )
    status = write_status(config, query_results, alert_results)

    verified = sum(1 for r in query_results if r.get("verified"))
    skipped = sum(1 for r in query_results if "skipped" in r)
    print(
        json.dumps(
            {
                "status_path": str(STATUS_PATH.relative_to(REPO_ROOT)),
                "queries_verified": verified,
                "queries_skipped": skipped,
                "all_queries_verified": status["all_queries_verified"],
            }
        )
    )

    if any(r.get("error") for r in query_results if "skipped" not in r):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
