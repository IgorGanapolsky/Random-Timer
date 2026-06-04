#!/usr/bin/env python3
"""Delete GitHub Actions artifacts older than a retention window.

Uses ``gh api`` (requires ``gh auth login`` with ``actions:write`` or repo admin).

Default is dry-run; pass ``--execute`` to delete. Default retention is 7 days.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone


def _run_gh(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
        check=False,
    )


def gh_api_json(path: str, *, paginate: bool = False) -> list[dict]:
    if paginate:
        return _paginate_artifacts(path)

    result = _run_gh(["api", path])
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"gh api failed: {path}")

    payload = json.loads(result.stdout or "{}")
    if isinstance(payload, dict) and "artifacts" in payload:
        return payload["artifacts"]
    if isinstance(payload, list):
        return payload
    return [payload]


def _paginate_artifacts(path: str) -> list[dict]:
    """Page through Actions artifacts; ``gh api --paginate`` concatenates JSON blobs."""
    items: list[dict] = []
    page = 1
    while True:
        sep = "&" if "?" in path else "?"
        page_path = f"{path}{sep}per_page=100&page={page}"
        result = _run_gh(["api", page_path])
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or f"gh api failed: {page_path}")
        payload = json.loads(result.stdout or "{}")
        batch = payload.get("artifacts", [])
        items.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return items


def parse_github_ts(value: str) -> datetime:
    # e.g. 2026-06-01T12:34:56Z
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value).astimezone(timezone.utc)


def delete_artifact(repo: str, artifact_id: int) -> None:
    result = _run_gh(["api", "-X", "DELETE", f"repos/{repo}/actions/artifacts/{artifact_id}"])
    if result.returncode != 0:
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
        artifacts = gh_api_json(f"repos/{repo}/actions/artifacts", paginate=True)
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
    print(f"Listed {len(artifacts)} artifacts; {len(stale)} older than {args.days}d (~{total_bytes / (1024**3):.2f} GiB)")

    deleted = 0
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
                print(f"  FAIL id={aid} name={name}: {exc}", file=sys.stderr)
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
