#!/usr/bin/env python3
"""Delete GitHub Actions artifacts older than a retention window.

Uses ``gh api`` (requires ``gh auth login`` with ``actions:write`` or repo admin).

Default is dry-run; pass ``--execute`` to delete. Default retention is 7 days.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone

MAX_RETRIES = 6
INITIAL_BACKOFF_SEC = 30
MAX_BACKOFF_SEC = 300


def _run_gh(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
        check=False,
    )


def _is_rate_limited(result: subprocess.CompletedProcess[str]) -> bool:
    text = f"{result.stderr}\n{result.stdout}".lower()
    return result.returncode != 0 and (
        "403" in text or "rate limit" in text or "secondary rate limit" in text
    )


def _retry_after_seconds(result: subprocess.CompletedProcess[str], attempt: int) -> float:
    text = f"{result.stderr}\n{result.stdout}"
    match = re.search(r"retry.after[:\s]+(\d+)", text, re.IGNORECASE)
    if match:
        return float(match.group(1))
    return min(INITIAL_BACKOFF_SEC * (2**attempt), MAX_BACKOFF_SEC)


def _run_gh_with_retry(args: list[str], *, label: str) -> subprocess.CompletedProcess[str]:
    last: subprocess.CompletedProcess[str] | None = None
    for attempt in range(MAX_RETRIES):
        last = _run_gh(args)
        if last.returncode == 0:
            return last
        if _is_rate_limited(last) and attempt < MAX_RETRIES - 1:
            wait = _retry_after_seconds(last, attempt)
            print(
                f"Rate limited on {label}; sleeping {wait:.0f}s (attempt {attempt + 1}/{MAX_RETRIES})",
                file=sys.stderr,
            )
            time.sleep(wait)
            continue
        return last
    assert last is not None
    return last


def gh_api_json(path: str, *, paginate: bool = False, start_page: int = 1) -> tuple[list[dict], int | None, bool]:
    """Return (artifacts, total_count, pagination_complete)."""
    if paginate:
        return _paginate_artifacts(path, start_page=start_page)

    result = _run_gh_with_retry(["api", path], label=path)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"gh api failed: {path}")

    payload = json.loads(result.stdout or "{}")
    total_count = payload.get("total_count") if isinstance(payload, dict) else None
    if isinstance(payload, dict) and "artifacts" in payload:
        return payload["artifacts"], total_count, True
    if isinstance(payload, list):
        return payload, total_count, True
    return [payload], total_count, True


def _paginate_artifacts(path: str, *, start_page: int = 1) -> tuple[list[dict], int | None, bool]:
    """Page through Actions artifacts; resume from ``start_page`` after rate limits."""
    items: list[dict] = []
    total_count: int | None = None
    page = start_page
    while True:
        sep = "&" if "?" in path else "?"
        page_path = f"{path}{sep}per_page=100&page={page}"
        result = _run_gh_with_retry(["api", page_path], label=f"page {page}")
        if result.returncode != 0:
            if _is_rate_limited(result):
                print(
                    f"Pagination stopped at page {page} after retries; "
                    f"resume with --start-page {page}",
                    file=sys.stderr,
                )
                return items, total_count, False
            raise RuntimeError(result.stderr.strip() or f"gh api failed: {page_path}")
        payload = json.loads(result.stdout or "{}")
        if total_count is None and isinstance(payload, dict):
            total_count = payload.get("total_count")
        batch = payload.get("artifacts", [])
        items.extend(batch)
        if len(batch) < 100:
            return items, total_count, True
        page += 1
    return items, total_count, True


def parse_github_ts(value: str) -> datetime:
    # e.g. 2026-06-01T12:34:56Z
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value).astimezone(timezone.utc)


def delete_artifact(repo: str, artifact_id: int) -> None:
    path = f"repos/{repo}/actions/artifacts/{artifact_id}"
    result = _run_gh_with_retry(["api", "-X", "DELETE", path], label=f"delete {artifact_id}")
    if result.returncode != 0:
        if _is_rate_limited(result):
            raise RuntimeError(f"rate limited deleting artifact {artifact_id}")
        raise RuntimeError(
            f"delete artifact {artifact_id} failed: {result.stderr.strip() or result.stdout.strip()}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo",
        default=None,
        help="owner/repo (default: gh repo view --json nameWithOwner)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Delete artifacts older than this many days (default: 7)",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually delete artifacts (default: dry-run)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Max deletions per run (0 = no limit)",
    )
    parser.add_argument(
        "--start-page",
        type=int,
        default=1,
        help="Resume artifact list pagination from this page (default: 1)",
    )
    args = parser.parse_args()

    repo = args.repo
    if not repo:
        view = _run_gh(["repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"])
        if view.returncode != 0:
            print(f"Could not resolve repo: {view.stderr.strip()}", file=sys.stderr)
            return 1
        repo = view.stdout.strip()

    auth = _run_gh(["auth", "status"])
    if auth.returncode != 0:
        print(auth.stderr.strip() or "gh not authenticated", file=sys.stderr)
        return 1

    cutoff = datetime.now(timezone.utc) - timedelta(days=args.days)
    mode = "EXECUTE" if args.execute else "DRY-RUN"
    print(f"{mode}: repo={repo} cutoff={cutoff.isoformat()} (>{args.days}d old)")

    try:
        artifacts, total_count, pagination_complete = gh_api_json(
            f"repos/{repo}/actions/artifacts",
            paginate=True,
            start_page=args.start_page,
        )
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    stale = []
    for artifact in artifacts:
        created_raw = artifact.get("created_at")
        if not created_raw:
            continue
        created = parse_github_ts(created_raw)
        if created < cutoff:
            stale.append(artifact)

    total_bytes = sum(int(a.get("size_in_bytes") or 0) for a in stale)
    total_label = total_count if total_count is not None else "?"
    print(
        f"Listed {len(artifacts)} artifacts (total_count={total_label}); "
        f"{len(stale)} older than {args.days}d (~{total_bytes / (1024**3):.2f} GiB)"
    )
    if not pagination_complete:
        print("Pagination incomplete — stale count may be understated.", file=sys.stderr)

    deleted = 0
    rate_limited = False
    for artifact in stale:
        if args.limit and deleted >= args.limit:
            print(f"Stopped at --limit {args.limit}")
            break

        aid = artifact["id"]
        name = artifact.get("name", "?")
        created = artifact.get("created_at", "?")
        size_mb = int(artifact.get("size_in_bytes") or 0) / (1024 * 1024)

        if args.execute:
            try:
                delete_artifact(repo, aid)
            except RuntimeError as exc:
                msg = str(exc)
                print(f"  FAIL id={aid} name={name}: {msg}", file=sys.stderr)
                if "rate limited" in msg.lower():
                    rate_limited = True
                    break
                continue
            deleted += 1
            if deleted % 100 == 0:
                print(f"  deleted {deleted}...")
        else:
            deleted += 1
            if deleted <= 10:
                print(f"  would delete id={aid} name={name} created={created} size={size_mb:.1f}MB")
            elif deleted == 11:
                print("  ...")

    action = "Deleted" if args.execute else "Would delete"
    print(f"{action} {deleted} artifact(s)")
    if rate_limited:
        print("Stopped: delete rate limit hit.", file=sys.stderr)
        return 2
    if not pagination_complete:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
