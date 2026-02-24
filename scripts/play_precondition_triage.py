#!/usr/bin/env python3
"""Upsert a single GitHub triage issue for Play FAILED_PRECONDITION blockers."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

DEFAULT_ISSUE_TITLE = "Android production publish blocked by Play FAILED_PRECONDITION"


def load_json(path: str) -> dict[str, Any] | None:
    if not path:
        return None
    p = Path(path)
    if not p.is_file():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def is_failed_precondition_payload(payload: dict[str, Any] | None) -> bool:
    if not payload:
        return False
    text = f"{payload.get('error', '')}\n{payload.get('response', '')}".lower()
    return "failed_precondition" in text or "precondition check failed" in text


def should_close_issue(result_payload: dict[str, Any] | None) -> bool:
    if not result_payload:
        return False
    requested = str(result_payload.get("requested_track", "")).lower()
    effective = str(result_payload.get("effective_track", "")).lower()
    fallback_used = bool(result_payload.get("fallback_used"))
    precondition_blocked = bool(result_payload.get("precondition_blocked"))
    return (
        requested == "production"
        and effective == "production"
        and not fallback_used
        and not precondition_blocked
    )


def _run_gh(args: list[str], *, capture_output: bool = True) -> subprocess.CompletedProcess[str]:
    cmd = ["gh", *args]
    return subprocess.run(
        cmd,
        check=False,
        capture_output=capture_output,
        text=True,
    )


def _find_issue_number(repo: str, title: str, state: str) -> int | None:
    proc = _run_gh(
        [
            "issue",
            "list",
            "--repo",
            repo,
            "--state",
            state,
            "--search",
            f'"{title}" in:title',
            "--json",
            "number,title,state",
            "--limit",
            "20",
        ]
    )
    if proc.returncode != 0:
        raise RuntimeError(f"gh issue list failed: {proc.stderr.strip()}")

    issues = json.loads(proc.stdout or "[]")
    for issue in issues:
        if issue.get("title") == title:
            return int(issue["number"])
    return None


def _write_body_file(content: str) -> str:
    fd, path = tempfile.mkstemp(prefix="play-precondition-", suffix=".md")
    with open(fd, "w", encoding="utf-8", closefd=True) as f:
        f.write(content)
    return path


def build_issue_body(
    *,
    run_url: str,
    error_payload: dict[str, Any],
    result_payload: dict[str, Any] | None,
) -> str:
    details = {
        "http_status": error_payload.get("http_status"),
        "requested_track": error_payload.get("requested_track"),
        "failed_track": error_payload.get("track"),
        "release_status": error_payload.get("release_status"),
        "attempt": error_payload.get("attempt"),
        "effective_track": (result_payload or {}).get("effective_track"),
        "fallback_used": (result_payload or {}).get("fallback_used"),
        "version_code": (result_payload or {}).get("version_code"),
    }
    details_json = json.dumps(details, indent=2, ensure_ascii=True)
    response_excerpt = str(error_payload.get("response", "")).strip()
    if len(response_excerpt) > 2000:
        response_excerpt = response_excerpt[:2000] + "\n... (truncated)"

    body = [
        "## Play Production Blocker",
        "",
        "Automated triage detected a Google Play production publish blocker (`FAILED_PRECONDITION`).",
        "",
        f"- Run: {run_url}",
        "",
        "### Structured details",
        "```json",
        details_json,
        "```",
        "",
        "### Play response excerpt",
        "```text",
        response_excerpt or "(empty response)",
        "```",
        "",
        "### Action",
        "- Keep daily production retry enabled.",
        "- Continue alpha fallback for continuity until production preconditions clear.",
    ]
    return "\n".join(body)


def _comment_and_close(repo: str, issue_number: int, run_url: str, result_payload: dict[str, Any]) -> None:
    message = (
        "Production publish is now succeeding again. Closing blocker automatically.\n\n"
        f"- Run: {run_url}\n"
        f"- Effective track: {result_payload.get('effective_track')}\n"
        f"- Version code: {result_payload.get('version_code')}"
    )
    comment = _run_gh(
        [
            "issue",
            "comment",
            str(issue_number),
            "--repo",
            repo,
            "--body",
            message,
        ]
    )
    if comment.returncode != 0:
        raise RuntimeError(f"gh issue comment failed: {comment.stderr.strip()}")

    close = _run_gh(["issue", "close", str(issue_number), "--repo", repo])
    if close.returncode != 0:
        raise RuntimeError(f"gh issue close failed: {close.stderr.strip()}")


def _upsert_open_issue(
    repo: str,
    title: str,
    body: str,
) -> int:
    open_issue = _find_issue_number(repo, title, "open")
    body_file = _write_body_file(body)
    try:
        if open_issue is not None:
            edit = _run_gh(
                [
                    "issue",
                    "edit",
                    str(open_issue),
                    "--repo",
                    repo,
                    "--title",
                    title,
                    "--body-file",
                    body_file,
                ]
            )
            if edit.returncode != 0:
                raise RuntimeError(f"gh issue edit failed: {edit.stderr.strip()}")
            return open_issue

        closed_issue = _find_issue_number(repo, title, "closed")
        if closed_issue is not None:
            reopen = _run_gh(["issue", "reopen", str(closed_issue), "--repo", repo])
            if reopen.returncode != 0:
                raise RuntimeError(f"gh issue reopen failed: {reopen.stderr.strip()}")
            edit = _run_gh(
                [
                    "issue",
                    "edit",
                    str(closed_issue),
                    "--repo",
                    repo,
                    "--title",
                    title,
                    "--body-file",
                    body_file,
                ]
            )
            if edit.returncode != 0:
                raise RuntimeError(f"gh issue edit failed: {edit.stderr.strip()}")
            return closed_issue

        create = _run_gh(
            [
                "issue",
                "create",
                "--repo",
                repo,
                "--title",
                title,
                "--body-file",
                body_file,
            ]
        )
        if create.returncode != 0:
            raise RuntimeError(f"gh issue create failed: {create.stderr.strip()}")
        issue_url = (create.stdout or "").strip()
        try:
            return int(issue_url.rstrip("/").split("/")[-1])
        except Exception:
            return 0
    finally:
        Path(body_file).unlink(missing_ok=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Upsert Play precondition triage issue.")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--run-url", required=True)
    parser.add_argument("--error-json", default="")
    parser.add_argument("--result-json", default="")
    parser.add_argument("--title", default=DEFAULT_ISSUE_TITLE)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    error_payload = load_json(args.error_json)
    result_payload = load_json(args.result_json)

    precondition_blocked = is_failed_precondition_payload(error_payload)
    if precondition_blocked:
        body = build_issue_body(
            run_url=args.run_url,
            error_payload=error_payload or {},
            result_payload=result_payload,
        )
        issue_number = _upsert_open_issue(args.repo, args.title, body)
        print(
            f"updated_issue={issue_number}\n"
            f"action=upsert\n"
            f"precondition_blocked=true"
        )
        return 0

    open_issue = _find_issue_number(args.repo, args.title, "open")
    if open_issue is None:
        print("action=noop\nprecondition_blocked=false")
        return 0

    if should_close_issue(result_payload):
        _comment_and_close(args.repo, open_issue, args.run_url, result_payload or {})
        print(f"closed_issue={open_issue}\naction=close\nprecondition_blocked=false")
        return 0

    print(
        f"open_issue={open_issue}\naction=noop_open_issue_retained\nprecondition_blocked=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
