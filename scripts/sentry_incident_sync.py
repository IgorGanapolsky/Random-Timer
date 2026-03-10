#!/usr/bin/env python3
"""Sync high-signal Sentry issues into GitHub incident issues."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SENTRY_API_BASE = "https://sentry.io/api/0"
GITHUB_API_BASE = "https://api.github.com"
DEFAULT_LOOKBACK_DAYS = 7
DEFAULT_MIN_EVENTS = 5
DEFAULT_MIN_USERS = 2
DEFAULT_MAX_ISSUES = 20
INCIDENT_LABELS = {
    "incident": {"color": "d73a4a", "description": "Operational incident requiring intervention"},
    "sentry": {"color": "5319e7", "description": "Incident synced from Sentry"},
}
IGNORE_PATTERNS = (
    "qa menu",
    "test sentry",
    "sentry client crash",
    "crashtestingscreen",
    "devtools",
)
MONETIZATION_KEYWORDS = ("purchase", "billing", "subscription", "paywall", "pro")
ALARM_KEYWORDS = ("alarm", "notification", "timer", "audio", "voice", "callout", "countdown", "drill")
STABILITY_KEYWORDS = ("crash", "fatal", "exception", "panic")


@dataclass
class Config:
    sentry_org: str
    sentry_project: str
    sentry_auth_token: str
    github_repo: str
    github_token: str
    lookback_days: int
    min_events: int
    min_users: int
    max_issues: int
    dry_run: bool
    issues_json: Path | None
    json_out: Path | None


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return default


def _issue_text(issue: dict[str, Any]) -> str:
    parts = [
        str(issue.get("title") or ""),
        str(issue.get("culprit") or ""),
        str(issue.get("level") or ""),
        str((issue.get("metadata") or {}).get("type") or ""),
        str((issue.get("metadata") or {}).get("value") or ""),
    ]
    return " ".join(parts).lower()


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)


def _issue_marker(config: Config, issue: dict[str, Any]) -> str:
    short_id = issue.get("shortId") or issue.get("id") or "unknown"
    return (
        "<!-- sentry-incident-sync:"
        f"org={config.sentry_org};project={config.sentry_project or 'all'};issue={short_id}"
        " -->"
    )


def _request_json(
    url: str,
    headers: dict[str, str],
    *,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
) -> Any:
    data = None
    request_headers = dict(headers)
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        request_headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, headers=request_headers, method=method, data=data)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} for {url}: {body[:400]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Request failed for {url}: {exc.reason}") from exc


def fetch_sentry_issues(config: Config) -> list[dict[str, Any]]:
    if config.issues_json is not None:
        payload = json.loads(config.issues_json.read_text(encoding="utf-8"))
        return payload if isinstance(payload, list) else []

    query_parts = [f"is:unresolved lastSeen:-{config.lookback_days}d"]
    if config.sentry_project:
        query_parts.append(f"project:{config.sentry_project}")
    query = " ".join(query_parts)
    params = urllib.parse.urlencode({"query": query, "limit": str(config.max_issues), "sort": "user"})
    url = f"{SENTRY_API_BASE}/organizations/{config.sentry_org}/issues/?{params}"
    headers = {
        "Authorization": f"Bearer {config.sentry_auth_token}",
        "Accept": "application/json",
    }
    payload = _request_json(url, headers)
    return payload if isinstance(payload, list) else []


def classify_issue(issue: dict[str, Any], config: Config) -> dict[str, Any]:
    text = _issue_text(issue)
    count = _to_int(issue.get("count"))
    users = _to_int(issue.get("userCount"))
    level = str(issue.get("level") or "").lower()
    ignored = [pattern for pattern in IGNORE_PATTERNS if pattern in text]
    monetization = _contains_any(text, MONETIZATION_KEYWORDS)
    alarm = _contains_any(text, ALARM_KEYWORDS)
    stability = _contains_any(text, STABILITY_KEYWORDS) or level == "fatal"

    reasons: list[str] = []
    if ignored:
        reasons.append(f"ignored:{ignored[0]}")
    if monetization:
        reasons.append("keyword:monetization")
    if alarm:
        reasons.append("keyword:alarm")
    if stability:
        reasons.append("keyword:stability")
    if count >= config.min_events:
        reasons.append(f"event_threshold:{count}")
    if users >= config.min_users:
        reasons.append(f"user_threshold:{users}")

    eligible = False
    if not ignored:
        if monetization or alarm:
            eligible = count >= 1 or users >= 1
        elif stability:
            eligible = count >= 1
        else:
            eligible = count >= config.min_events and users >= config.min_users

    priority = "low"
    if monetization or alarm or stability or count >= 20 or users >= 5:
        priority = "high"
    elif count >= config.min_events or users >= config.min_users:
        priority = "medium"

    area = "generic"
    if monetization:
        area = "monetization"
    elif alarm:
        area = "alarm_lifecycle"
    elif stability:
        area = "stability"

    return {
        "eligible": eligible,
        "priority": priority,
        "area": area,
        "reasons": reasons,
        "count": count,
        "users": users,
    }


def format_issue_body(config: Config, issue: dict[str, Any], classification: dict[str, Any]) -> str:
    short_id = issue.get("shortId") or issue.get("id") or "unknown"
    permalink = issue.get("permalink") or "unavailable"
    assignee = issue.get("assignedTo")
    assignee_text = "unassigned"
    if isinstance(assignee, dict):
        assignee_text = str(assignee.get("name") or assignee.get("email") or assignee.get("id") or "unassigned")

    culprit = issue.get("culprit") or "unknown"
    level = issue.get("level") or "unknown"
    reasons = classification["reasons"] or ["none"]
    return "\n".join(
        [
            _issue_marker(config, issue),
            f"## Sentry incident candidate {short_id}",
            "",
            f"- Synced at (UTC): {_now()}",
            f"- Sentry Org: `{config.sentry_org}`",
            f"- Sentry Project: `{config.sentry_project or 'all'}`",
            f"- Sentry Issue: [{short_id}]({permalink})",
            f"- Title: {issue.get('title') or 'unknown'}",
            f"- Priority: `{classification['priority']}`",
            f"- Area: `{classification['area']}`",
            f"- Level: `{level}`",
            f"- Events: `{classification['count']}`",
            f"- Users: `{classification['users']}`",
            f"- First Seen: `{issue.get('firstSeen') or 'unknown'}`",
            f"- Last Seen: `{issue.get('lastSeen') or 'unknown'}`",
            f"- Culprit: `{culprit}`",
            f"- Assignee: `{assignee_text}`",
            "",
            "### Sync Evidence",
            *(f"- {reason}" for reason in reasons),
        ]
    )


def format_issue_title(issue: dict[str, Any], classification: dict[str, Any]) -> str:
    short_id = issue.get("shortId") or issue.get("id") or "unknown"
    title = str(issue.get("title") or "Untitled issue").strip()
    trimmed = title if len(title) <= 80 else f"{title[:77]}..."
    return f"Sentry Incident: [{classification['priority'].upper()}] {short_id} {trimmed}"


def github_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "random-timer-sentry-incident-sync",
    }


def ensure_labels(repo: str, token: str) -> None:
    owner, name = repo.split("/", 1)
    headers = github_headers(token)
    labels = _request_json(f"{GITHUB_API_BASE}/repos/{owner}/{name}/labels?per_page=100", headers)
    existing = {label.get("name") for label in labels if isinstance(label, dict)}
    for label_name, spec in INCIDENT_LABELS.items():
        if label_name in existing:
            continue
        _request_json(
            f"{GITHUB_API_BASE}/repos/{owner}/{name}/labels",
            headers,
            method="POST",
            payload={"name": label_name, **spec},
        )


def list_open_synced_issues(repo: str, token: str) -> list[dict[str, Any]]:
    owner, name = repo.split("/", 1)
    headers = github_headers(token)
    url = f"{GITHUB_API_BASE}/repos/{owner}/{name}/issues?state=open&labels=incident,sentry&per_page=100"
    payload = _request_json(url, headers)
    return [issue for issue in payload if isinstance(issue, dict) and "pull_request" not in issue]


def find_existing_issue(open_issues: list[dict[str, Any]], marker: str) -> dict[str, Any] | None:
    for issue in open_issues:
        if marker in str(issue.get("body") or ""):
            return issue
    return None


def create_issue(repo: str, token: str, title: str, body: str) -> int:
    owner, name = repo.split("/", 1)
    headers = github_headers(token)
    payload = _request_json(
        f"{GITHUB_API_BASE}/repos/{owner}/{name}/issues",
        headers,
        method="POST",
        payload={"title": title, "body": body, "labels": list(INCIDENT_LABELS)},
    )
    return _to_int(payload.get("number"))


def update_issue(repo: str, token: str, number: int, title: str, body: str) -> None:
    owner, name = repo.split("/", 1)
    headers = github_headers(token)
    _request_json(
        f"{GITHUB_API_BASE}/repos/{owner}/{name}/issues/{number}",
        headers,
        method="PATCH",
        payload={"title": title, "body": body},
    )


def comment_issue(repo: str, token: str, number: int, body: str) -> None:
    owner, name = repo.split("/", 1)
    headers = github_headers(token)
    _request_json(
        f"{GITHUB_API_BASE}/repos/{owner}/{name}/issues/{number}/comments",
        headers,
        method="POST",
        payload={"body": body},
    )


def close_issue(repo: str, token: str, number: int, comment: str) -> None:
    owner, name = repo.split("/", 1)
    headers = github_headers(token)
    if comment:
        comment_issue(repo, token, number, comment)
    _request_json(
        f"{GITHUB_API_BASE}/repos/{owner}/{name}/issues/{number}",
        headers,
        method="PATCH",
        payload={"state": "closed", "state_reason": "completed"},
    )


def build_config(args: argparse.Namespace) -> Config:
    return Config(
        sentry_org=(args.sentry_org or os.getenv("SENTRY_ORG", "")).strip(),
        sentry_project=(args.sentry_project or os.getenv("SENTRY_PROJECT", "")).strip(),
        sentry_auth_token=(args.sentry_auth_token or os.getenv("SENTRY_AUTH_TOKEN", "")).strip(),
        github_repo=(args.github_repo or os.getenv("GITHUB_REPOSITORY", "")).strip(),
        github_token=(
            args.github_token
            or os.getenv("GITHUB_TOKEN", "")
            or os.getenv("GH_TOKEN", "")
            or os.getenv("ADMIN_TOKEN", "")
        ).strip(),
        lookback_days=int(args.lookback_days),
        min_events=int(args.min_events),
        min_users=int(args.min_users),
        max_issues=int(args.max_issues),
        dry_run=bool(args.dry_run),
        issues_json=Path(args.issues_json).resolve() if args.issues_json else None,
        json_out=Path(args.json_out).resolve() if args.json_out else None,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync high-signal Sentry issues into GitHub incidents.")
    parser.add_argument("--sentry-org", default="", help="Sentry organization slug")
    parser.add_argument("--sentry-project", default="", help="Sentry project slug")
    parser.add_argument("--sentry-auth-token", default="", help="Sentry auth token")
    parser.add_argument("--github-repo", default="", help="GitHub repo in owner/name form")
    parser.add_argument("--github-token", default="", help="GitHub token with issues:write")
    parser.add_argument("--lookback-days", type=int, default=int(os.getenv("SENTRY_INCIDENT_LOOKBACK_DAYS", DEFAULT_LOOKBACK_DAYS)))
    parser.add_argument("--min-events", type=int, default=int(os.getenv("SENTRY_INCIDENT_MIN_EVENTS", DEFAULT_MIN_EVENTS)))
    parser.add_argument("--min-users", type=int, default=int(os.getenv("SENTRY_INCIDENT_MIN_USERS", DEFAULT_MIN_USERS)))
    parser.add_argument("--max-issues", type=int, default=int(os.getenv("SENTRY_INCIDENT_MAX_ISSUES", DEFAULT_MAX_ISSUES)))
    parser.add_argument("--dry-run", action="store_true", help="Evaluate and report actions without writing GitHub issues")
    parser.add_argument("--issues-json", default="", help="Load Sentry issues from a local JSON file instead of the API")
    parser.add_argument("--json-out", default="", help="Write a machine-readable report to this path")
    return parser.parse_args()


def run(config: Config) -> dict[str, Any]:
    result: dict[str, Any] = {
        "generated_at": _now(),
        "status": "ok",
        "mode": "dry_run" if config.dry_run else "write",
        "config": {
            "sentry_org": config.sentry_org,
            "sentry_project": config.sentry_project,
            "github_repo": config.github_repo,
            "lookback_days": config.lookback_days,
            "min_events": config.min_events,
            "min_users": config.min_users,
            "max_issues": config.max_issues,
            "issues_json": config.issues_json,
        },
        "summary": {
            "fetched": 0,
            "eligible": 0,
            "created": 0,
            "updated": 0,
            "closed": 0,
            "ignored": 0,
            "unchanged": 0,
        },
        "actions": [],
        "warnings": [],
    }

    missing: list[str] = []
    if not config.sentry_org:
        missing.append("SENTRY_ORG")
    if not config.github_repo:
        missing.append("GITHUB_REPOSITORY")
    if config.issues_json is None and not config.sentry_auth_token:
        missing.append("SENTRY_AUTH_TOKEN")
    if not config.dry_run and not config.github_token:
        missing.append("GITHUB_TOKEN")
    if missing:
        result["status"] = "skipped_missing_config"
        result["warnings"].append(f"Missing required configuration: {', '.join(missing)}")
        return result

    sentry_issues = fetch_sentry_issues(config)
    result["summary"]["fetched"] = len(sentry_issues)
    existing_open: list[dict[str, Any]] = []
    if config.github_token:
        if not config.dry_run:
            ensure_labels(config.github_repo, config.github_token)
        existing_open = list_open_synced_issues(config.github_repo, config.github_token)

    seen_markers: set[str] = set()
    for issue in sentry_issues:
        classification = classify_issue(issue, config)
        marker = _issue_marker(config, issue)
        seen_markers.add(marker)
        action: dict[str, Any] = {
            "short_id": issue.get("shortId") or issue.get("id"),
            "title": issue.get("title"),
            "eligible": classification["eligible"],
            "priority": classification["priority"],
            "area": classification["area"],
            "reasons": classification["reasons"],
            "count": classification["count"],
            "users": classification["users"],
            "existing_issue_number": None,
            "action": "ignored",
        }
        existing = find_existing_issue(existing_open, marker) if existing_open else None
        if existing:
            action["existing_issue_number"] = existing.get("number")

        if not classification["eligible"]:
            result["summary"]["ignored"] += 1
            result["actions"].append(action)
            continue

        result["summary"]["eligible"] += 1
        title = format_issue_title(issue, classification)
        body = format_issue_body(config, issue, classification)
        if existing is None:
            if config.dry_run or not config.github_token:
                action["action"] = "would_create"
            else:
                number = create_issue(config.github_repo, config.github_token, title, body)
                action["action"] = "created"
                action["github_issue_number"] = number
                result["summary"]["created"] += 1
            result["actions"].append(action)
            continue

        action["github_issue_number"] = existing.get("number")
        if str(existing.get("title") or "") == title and str(existing.get("body") or "") == body:
            action["action"] = "unchanged"
            result["summary"]["unchanged"] += 1
        elif config.dry_run or not config.github_token:
            action["action"] = "would_update"
        else:
            update_issue(config.github_repo, config.github_token, _to_int(existing.get("number")), title, body)
            action["action"] = "updated"
            result["summary"]["updated"] += 1
        result["actions"].append(action)

    for existing in existing_open:
        body = str(existing.get("body") or "")
        marker_lines = [line for line in body.splitlines() if line.startswith("<!-- sentry-incident-sync:")]
        if not marker_lines:
            continue
        marker = marker_lines[0]
        if marker in seen_markers:
            continue
        action = {
            "github_issue_number": existing.get("number"),
            "title": existing.get("title"),
            "action": "would_close" if config.dry_run or not config.github_token else "closed",
        }
        if not config.dry_run and config.github_token:
            close_issue(
                config.github_repo,
                config.github_token,
                _to_int(existing.get("number")),
                f"Sentry incident recovered or no longer matches the sync criteria.\n\n- Synced at (UTC): {_now()}",
            )
            result["summary"]["closed"] += 1
        result["actions"].append(action)

    return result


def main() -> None:
    args = parse_args()
    config = build_config(args)
    result = run(config)
    if config.json_out is not None:
        config.json_out.parent.mkdir(parents=True, exist_ok=True)
        config.json_out.write_text(json.dumps(result, indent=2, default=_json_default) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, default=_json_default))
    if result["status"] not in {"ok", "skipped_missing_config"}:
        sys.exit(1)


if __name__ == "__main__":
    main()
