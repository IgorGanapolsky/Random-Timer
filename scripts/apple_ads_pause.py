#!/usr/bin/env python3
"""Pause active Apple Search Ads campaign and update local campaign state."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any

from apple_ads_launch import (
    api_get,
    api_headers,
    api_put,
    generate_jwt_token,
    get_access_token,
    load_env,
)


def _ensure_private_key_path() -> None:
    inline = os.getenv("APPLE_ADS_PRIVATE_KEY", "").strip()
    if not inline or os.getenv("APPLE_ADS_PRIVATE_KEY_PATH", "").strip():
        return
    fd, path = tempfile.mkstemp(prefix="apple-ads-key-", suffix=".pem")
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(inline)
        if not inline.endswith("\n"):
            handle.write("\n")
    os.environ["APPLE_ADS_PRIVATE_KEY_PATH"] = path


def _pause_campaign(headers: dict[str, str], campaign_id: int, org_id: int) -> dict[str, Any]:
    before = api_get(f"/campaigns/{campaign_id}", headers).get("data", {})
    before_status = str(before.get("status", "UNKNOWN"))

    if before_status.upper() == "PAUSED":
        return {
            "campaign_id": campaign_id,
            "status_before": before_status,
            "status_after": before_status,
            "serving_after": str(before.get("servingStatus", "UNKNOWN")),
            "changed": False,
        }

    attempts = [
        {"status": "PAUSED"},
        {"id": campaign_id, "status": "PAUSED"},
        {"orgId": org_id, "id": campaign_id, "status": "PAUSED"},
    ]
    last_error: str | None = None
    for payload in attempts:
        try:
            api_put(f"/campaigns/{campaign_id}", headers, payload)
            after = api_get(f"/campaigns/{campaign_id}", headers).get("data", {})
            return {
                "campaign_id": campaign_id,
                "status_before": before_status,
                "status_after": str(after.get("status", "UNKNOWN")),
                "serving_after": str(after.get("servingStatus", "UNKNOWN")),
                "changed": True,
            }
        except Exception as exc:  # noqa: BLE001
            last_error = str(exc)
    raise RuntimeError(f"Unable to pause campaign {campaign_id}: {last_error}")


def _update_paid_campaigns_json(
    repo_root: Path,
    *,
    campaign_id: int,
    reason: str,
    status_after: str,
    dry_run: bool,
) -> bool:
    path = repo_root / "marketing" / "data" / "paid_campaigns.json"
    if not path.exists():
        return False

    payload = json.loads(path.read_text(encoding="utf-8"))
    changed = False
    for campaign in payload.get("campaigns", []):
        if campaign.get("platform") == "apple_search_ads":
            if int(campaign.get("campaign_id") or 0) == campaign_id:
                if campaign.get("status") != status_after.lower():
                    campaign["status"] = status_after.lower()
                    changed = True
                campaign["paused_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                changed = True

    history = payload.setdefault("history", [])
    history.append(
        {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "action": "apple_search_ads_paused",
            "campaign_id": campaign_id,
            "reason": reason,
            "status": status_after,
        }
    )
    changed = True

    if changed and not dry_run:
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description="Pause Apple Search Ads campaign and update local campaign state")
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parent.parent))
    parser.add_argument("--campaign-id", type=int, default=0)
    parser.add_argument("--reason", default="no_scale_lock_active")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    load_env()
    _ensure_private_key_path()

    required = ["APPLE_ADS_CLIENT_ID", "APPLE_ADS_TEAM_ID", "APPLE_ADS_KEY_ID"]
    missing = [name for name in required if not os.getenv(name, "").strip()]
    if missing:
        raise SystemExit(f"Missing required env vars: {missing}")

    campaign_id = args.campaign_id
    if campaign_id <= 0:
        paid_path = repo_root / "marketing" / "data" / "paid_campaigns.json"
        payload = json.loads(paid_path.read_text(encoding="utf-8"))
        for campaign in payload.get("campaigns", []):
            if campaign.get("platform") == "apple_search_ads":
                campaign_id = int(campaign.get("campaign_id") or 0)
                break
    if campaign_id <= 0:
        raise SystemExit("No Apple Search Ads campaign_id found")

    client_secret = generate_jwt_token()
    access_token = get_access_token(client_secret)
    org_id = int(os.getenv("APPLE_ADS_ORG_ID", "20617940"))
    headers = api_headers(access_token, org_id)

    pause_result = _pause_campaign(headers, campaign_id, org_id)
    status_after = str(pause_result["status_after"]).upper()
    if status_after != "PAUSED":
        raise SystemExit(f"Pause request completed but campaign status is {status_after}")

    changed = _update_paid_campaigns_json(
        repo_root,
        campaign_id=campaign_id,
        reason=args.reason,
        status_after=status_after,
        dry_run=args.dry_run,
    )

    print(
        json.dumps(
            {
                "campaign_id": campaign_id,
                "status_before": pause_result["status_before"],
                "status_after": pause_result["status_after"],
                "serving_after": pause_result["serving_after"],
                "updated_paid_campaigns_json": changed and not args.dry_run,
                "dry_run": args.dry_run,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
