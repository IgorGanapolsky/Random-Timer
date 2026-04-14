#!/usr/bin/env python3
"""Zernio.com API orchestration for social fan-out (complements growth_content_pipeline).

Docs: https://docs.zernio.com/ — Base URL https://zernio.com/api/v1, Bearer API key.

Environment (local `.env` or GitHub Actions secrets):
  ZERNIO_API_KEY or ZERNIO_TOKEN — API key (`sk_...`)
  ZERNIO_PUBLISH_ACCOUNTS — JSON array, e.g.
    [{"platform":"twitter","accountId":"acc_xxx"},{"platform":"linkedin","accountId":"acc_yyy"}]
  ZERNIO_AUTO_PUBLISH — if not "1", `sync-latest` only records a dry-run (default for safety)
  ZERNIO_TIMEZONE — IANA tz for scheduled posts (default UTC via scheduledFor without tz in API - use timezone field)

Cron-friendly: `sync-latest` skips if this slug was successfully published to Zernio in the last 36 hours.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

SCRIPTS = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

from repo_dotenv import load_repo_dotenv  # noqa: E402

ZERNIO_BASE = "https://zernio.com/api/v1"


def zernio_api_key() -> str:
    return (
        os.environ.get("ZERNIO_API_KEY", "").strip()
        or os.environ.get("ZERNIO_TOKEN", "").strip()
    )


def zernio_headers(api_key: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def zernio_list_accounts(api_key: str, timeout: int = 45) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
    try:
        r = requests.get(
            f"{ZERNIO_BASE}/accounts",
            headers=zernio_headers(api_key),
            timeout=timeout,
        )
    except requests.RequestException as exc:
        return None, f"request_error:{exc}"
    if r.status_code >= 300:
        return None, f"http_{r.status_code}:{r.text[:300]}"
    try:
        data = r.json()
    except Exception:
        return None, "non_json_response"
    accounts = data.get("accounts")
    if isinstance(accounts, list):
        return accounts, None
    return None, "unexpected_payload"


def zernio_create_post(
    api_key: str,
    content: str,
    platforms: List[Dict[str, str]],
    *,
    publish_now: bool = True,
    scheduled_for: Optional[str] = None,
    timezone: str = "UTC",
    timeout: int = 60,
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    body: Dict[str, Any] = {
        "content": content,
        "platforms": platforms,
    }
    if publish_now:
        body["publishNow"] = True
    elif scheduled_for:
        body["scheduledFor"] = scheduled_for
        body["timezone"] = timezone
    try:
        r = requests.post(
            f"{ZERNIO_BASE}/posts",
            headers=zernio_headers(api_key),
            json=body,
            timeout=timeout,
        )
    except requests.RequestException as exc:
        return None, f"request_error:{exc}"
    if r.status_code >= 300:
        return None, f"http_{r.status_code}:{r.text[:500]}"
    try:
        return r.json(), None
    except Exception:
        return None, f"non_json_response:{r.text[:200]}"


def _parse_publish_accounts(raw: str) -> Tuple[Optional[List[Dict[str, str]]], Optional[str]]:
    raw = raw.strip()
    if not raw:
        return None, "missing ZERNIO_PUBLISH_ACCOUNTS"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, f"invalid_json:{exc}"
    if not isinstance(data, list) or not data:
        return None, "ZERNIO_PUBLISH_ACCOUNTS must be a non-empty JSON array"
    out: List[Dict[str, str]] = []
    for item in data:
        if not isinstance(item, dict):
            return None, "each platform entry must be an object"
        pid = str(item.get("platform") or item.get("platformId") or "").strip()
        aid = str(item.get("accountId") or item.get("account_id") or "").strip()
        if not pid or not aid:
            return None, "each entry needs platform and accountId"
        if "replace_me" in aid.lower() or aid.strip() in ("", "...", "xxx", "TODO"):
            return None, "replace placeholder accountId values in ZERNIO_PUBLISH_ACCOUNTS"
        out.append({"platform": pid, "accountId": aid})
    return out, None


def _recent_zernio_publish_for_slug(log_path: Path, slug: str, hours: int = 36) -> bool:
    if not log_path.is_file():
        return False
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=hours)
    try:
        lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return False
    for line in lines[-400:]:
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("slug") != slug:
            continue
        if row.get("channel") != "zernio":
            continue
        if row.get("status") not in ("published", "dry_run"):
            continue
        ts_raw = str(row.get("timestamp") or "")
        try:
            ts = dt.datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=dt.timezone.utc)
        except ValueError:
            continue
        if ts >= cutoff:
            return True
    return False


def _append_jsonl(path: Path, row: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def cmd_health(_args: argparse.Namespace) -> int:
    key = zernio_api_key()
    if not key:
        print(json.dumps({"status": "skipped", "reason": "missing ZERNIO_API_KEY or ZERNIO_TOKEN"}))
        return 0
    accounts, err = zernio_list_accounts(key)
    if err:
        print(json.dumps({"status": "error", "reason": err}))
        return 1
    # Do not print account IDs in CI logs at info level — only counts + platforms
    platforms: Dict[str, int] = {}
    for acc in accounts or []:
        if not isinstance(acc, dict):
            continue
        p = str(acc.get("platform") or "unknown")
        platforms[p] = platforms.get(p, 0) + 1
    print(
        json.dumps(
            {
                "status": "ok",
                "account_count": len(accounts or []),
                "platforms": platforms,
            },
            indent=2,
        )
    )
    return 0


def cmd_sync_latest(args: argparse.Namespace) -> int:
    load_repo_dotenv(Path(args.repo_root).resolve())
    output_root = Path(args.output_root).resolve()
    log_path = output_root / "data" / "zernio_orchestration.jsonl"

    key = zernio_api_key()
    if not key:
        print(json.dumps({"status": "skipped", "reason": "missing ZERNIO_API_KEY or ZERNIO_TOKEN"}))
        return 0

    from growth_content_pipeline import (
        add_utm,
        campaign_from_slug,
        compose_social_post_text,
        latest_post_asset,
        resolve_blog_base_url,
    )

    try:
        post = latest_post_asset(output_root)
    except SystemExit:
        print(json.dumps({"status": "skipped", "reason": "no_marketing_posts"}))
        return 0
    if _recent_zernio_publish_for_slug(log_path, post.slug):
        print(
            json.dumps(
                {
                    "status": "skipped",
                    "reason": "recent_zernio_sync_for_slug",
                    "slug": post.slug,
                }
            )
        )
        return 0

    base_url = resolve_blog_base_url(output_root)
    canonical_url = f"{base_url}/posts/{post.slug}.html"
    campaign = campaign_from_slug(post.slug)
    tracked_url = add_utm(canonical_url, "zernio", campaign, medium="social", content=post.slug)
    text = f"{compose_social_post_text(post.title)}\n\n{tracked_url}"

    platforms, perr = _parse_publish_accounts(os.environ.get("ZERNIO_PUBLISH_ACCOUNTS", ""))
    if perr:
        _append_jsonl(
            log_path,
            {
                "timestamp": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
                "slug": post.slug,
                "channel": "zernio",
                "status": "skipped",
                "reason": perr,
            },
        )
        print(json.dumps({"status": "skipped", "reason": perr, "slug": post.slug}))
        return 0

    auto = os.environ.get("ZERNIO_AUTO_PUBLISH", "").strip() == "1"
    dry = args.dry_run or not auto

    if dry:
        _append_jsonl(
            log_path,
            {
                "timestamp": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
                "slug": post.slug,
                "channel": "zernio",
                "status": "dry_run",
                "preview_chars": len(text),
                "platform_count": len(platforms or []),
            },
        )
        print(
            json.dumps(
                {
                    "status": "dry_run",
                    "slug": post.slug,
                    "ZERNIO_AUTO_PUBLISH": "set to 1 to live-publish",
                    "platform_count": len(platforms or []),
                },
                indent=2,
            )
        )
        return 0

    payload, err = zernio_create_post(
        key,
        text,
        platforms,
        publish_now=True,
    )
    row = {
        "timestamp": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "slug": post.slug,
        "channel": "zernio",
        "status": "published" if not err else "error",
        "reason": err,
        "response": payload,
    }
    _append_jsonl(log_path, row)
    print(json.dumps(row, indent=2, default=str))
    return 0 if not err else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Zernio growth orchestration")
    sub = p.add_subparsers(dest="command", required=True)
    p_health = sub.add_parser("health", help="Verify API key and list account counts (no secrets printed)")
    p_health.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    p_sync = sub.add_parser("sync-latest", help="Fan-out latest growth post via Zernio (idempotent)")
    p_sync.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    p_sync.add_argument("--output-root", type=Path, default=REPO_ROOT / "marketing")
    p_sync.add_argument("--dry-run", action="store_true", help="Never POST; log dry_run only")
    return p


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "health":
        load_repo_dotenv(Path(args.repo_root).resolve())
        return cmd_health(args)
    if args.command == "sync-latest":
        return cmd_sync_latest(args)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
