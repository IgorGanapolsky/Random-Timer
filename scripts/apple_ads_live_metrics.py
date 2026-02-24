#!/usr/bin/env python3
"""Fetch live Apple Search Ads metrics and persist a local snapshot.

Outputs: marketing/data/apple_ads_live_metrics.json
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import jwt
    import requests
except ImportError:
    print("ERROR: install dependencies: PyJWT cryptography requests")
    raise SystemExit(1)


APPLE_AUTH_URL = "https://appleid.apple.com/auth/oauth2/token"
APPLE_AUD = "https://appleid.apple.com"
APPLE_SCOPE = "searchadsorg"
APPLE_API_BASE = "https://api.searchads.apple.com/api/v5"
DEFAULT_ADAM_ID = 6758355312


def load_env(repo_root: Path) -> None:
    env_path = repo_root / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, raw = line.partition("=")
        key = key.strip()
        value = raw.strip().strip("'\"")
        os.environ.setdefault(key, value)


def _read_private_key(repo_root: Path) -> Optional[str]:
    inline = os.getenv("APPLE_ADS_PRIVATE_KEY", "").strip()
    if inline:
        return inline.replace("\\n", "\n")

    key_path = os.getenv("APPLE_ADS_PRIVATE_KEY_PATH", "").strip()
    if not key_path:
        return None
    p = Path(key_path)
    if not p.is_absolute():
        p = repo_root / key_path
    if not p.exists():
        return None
    return p.read_text(encoding="utf-8")


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _amount(value: Any) -> float:
    if isinstance(value, dict):
        return _to_float(value.get("amount"))
    return _to_float(value)


def _oauth_access_token() -> tuple[str, str]:
    required = ["APPLE_ADS_CLIENT_ID", "APPLE_ADS_TEAM_ID", "APPLE_ADS_KEY_ID"]
    missing = [k for k in required if not os.getenv(k, "").strip()]
    if missing:
        return "", f"missing env vars: {', '.join(missing)}"

    repo_root = Path(__file__).resolve().parent.parent
    private_key = _read_private_key(repo_root)
    if not private_key:
        return "", "missing APPLE_ADS_PRIVATE_KEY or APPLE_ADS_PRIVATE_KEY_PATH"

    now = int(time.time())
    client_id = os.environ["APPLE_ADS_CLIENT_ID"].strip()
    key_id = os.environ["APPLE_ADS_KEY_ID"].strip()
    team_id = os.environ["APPLE_ADS_TEAM_ID"].strip()
    payload = {
        "sub": client_id,
        "aud": APPLE_AUD,
        "iat": now,
        "exp": now + 3600,
        "iss": team_id,
    }
    headers = {"alg": "ES256", "kid": key_id}
    client_secret = jwt.encode(payload, private_key, algorithm="ES256", headers=headers)

    resp = requests.post(
        APPLE_AUTH_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": APPLE_SCOPE,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    if resp.status_code >= 400:
        return "", f"oauth failed: HTTP {resp.status_code}"
    data = resp.json()
    token = data.get("access_token", "")
    if not token:
        return "", "oauth failed: access token missing"
    return token, ""


def _ads_headers(access_token: str) -> tuple[Dict[str, str], str]:
    org_id = os.getenv("APPLE_ADS_ORG_ID", "").strip()
    if not org_id:
        return {}, "missing APPLE_ADS_ORG_ID"
    return {
        "Authorization": f"Bearer {access_token}",
        "X-AP-Context": f"orgId={org_id}",
        "Content-Type": "application/json",
    }, ""


def _api_get(path: str, headers: Dict[str, str]) -> requests.Response:
    return requests.get(f"{APPLE_API_BASE}{path}", headers=headers, timeout=30)


def _api_post(path: str, headers: Dict[str, str], payload: Dict[str, Any]) -> requests.Response:
    return requests.post(f"{APPLE_API_BASE}{path}", headers=headers, json=payload, timeout=30)


def _report_payload(window_days: int, adam_id: int) -> Dict[str, Any]:
    end = dt.date.today()
    start = end - dt.timedelta(days=max(1, window_days))
    return {
        "startTime": start.isoformat(),
        "endTime": end.isoformat(),
        "selector": {
            "conditions": [
                {"field": "adamId", "operator": "EQUALS", "values": [str(adam_id)]},
            ],
            "pagination": {"offset": 0, "limit": 100},
            "orderBy": [{"field": "localSpend", "sortOrder": "DESCENDING"}],
        },
        "returnRecordsWithNoMetrics": True,
        "returnRowTotals": True,
    }


def _status_active(status: str, serving_status: str) -> bool:
    s = (status or "").upper()
    serving = (serving_status or "").upper()
    return s in {"ENABLED", "ACTIVE"} and serving in {"RUNNING", "ELIGIBLE", "SERVING", ""}


def run(repo_root: Path, window_days: int = 30, adam_id: int = DEFAULT_ADAM_ID) -> Dict[str, Any]:
    output_path = repo_root / "marketing" / "data" / "apple_ads_live_metrics.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()

    load_env(repo_root)
    token, err = _oauth_access_token()
    if not token:
        payload = {
            "generated_at": now,
            "source": "apple_ads_api",
            "status": "skipped",
            "status_reason": err,
            "window_days": window_days,
            "adam_id": adam_id,
            "campaign_count": 0,
            "active_campaign_count": 0,
            "campaigns": [],
            "metrics_30d": {
                "impressions": 0,
                "taps": 0,
                "spend_usd": 0.0,
                "installs": 0,
                "avg_cpt_usd": 0.0,
                "tap_install_cpi_usd": 0.0,
                "ttr": 0.0,
                "tap_install_rate": 0.0,
            },
            "finding": f"Apple Ads live check skipped: {err}",
            "snapshots": [],
        }
        output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return {
            "status": payload["status"],
            "output": str(output_path),
            "reason": payload["status_reason"],
            "campaign_count": 0,
            "active_campaign_count": 0,
        }

    headers, hdr_err = _ads_headers(token)
    if hdr_err:
        payload = {
            "generated_at": now,
            "source": "apple_ads_api",
            "status": "skipped",
            "status_reason": hdr_err,
            "window_days": window_days,
            "adam_id": adam_id,
            "campaign_count": 0,
            "active_campaign_count": 0,
            "campaigns": [],
            "metrics_30d": {
                "impressions": 0,
                "taps": 0,
                "spend_usd": 0.0,
                "installs": 0,
                "avg_cpt_usd": 0.0,
                "tap_install_cpi_usd": 0.0,
                "ttr": 0.0,
                "tap_install_rate": 0.0,
            },
            "finding": f"Apple Ads live check skipped: {hdr_err}",
            "snapshots": [],
        }
        output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return {
            "status": payload["status"],
            "output": str(output_path),
            "reason": payload["status_reason"],
            "campaign_count": 0,
            "active_campaign_count": 0,
        }

    campaigns_resp = _api_get("/campaigns", headers)
    if campaigns_resp.status_code >= 400:
        payload = {
            "generated_at": now,
            "source": "apple_ads_api",
            "status": "degraded",
            "status_reason": f"campaign list failed: HTTP {campaigns_resp.status_code}",
            "window_days": window_days,
            "adam_id": adam_id,
            "campaign_count": 0,
            "active_campaign_count": 0,
            "campaigns": [],
            "metrics_30d": {
                "impressions": 0,
                "taps": 0,
                "spend_usd": 0.0,
                "installs": 0,
                "avg_cpt_usd": 0.0,
                "tap_install_cpi_usd": 0.0,
                "ttr": 0.0,
                "tap_install_rate": 0.0,
            },
            "finding": f"Apple Ads campaign API error: HTTP {campaigns_resp.status_code}",
            "snapshots": [],
        }
        output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return {
            "status": payload["status"],
            "output": str(output_path),
            "reason": payload["status_reason"],
            "campaign_count": 0,
            "active_campaign_count": 0,
        }
    all_campaigns = campaigns_resp.json().get("data", [])
    campaigns_by_id = {
        int(c.get("id")): c for c in all_campaigns if c.get("id") is not None
    }

    report_resp = _api_post("/reports/campaigns", headers, _report_payload(window_days, adam_id))
    if report_resp.status_code >= 400:
        payload = {
            "generated_at": now,
            "source": "apple_ads_api",
            "status": "degraded",
            "status_reason": f"report failed: HTTP {report_resp.status_code}",
            "window_days": window_days,
            "adam_id": adam_id,
            "campaign_count": 0,
            "active_campaign_count": 0,
            "campaigns": [],
            "metrics_30d": {
                "impressions": 0,
                "taps": 0,
                "spend_usd": 0.0,
                "installs": 0,
                "avg_cpt_usd": 0.0,
                "tap_install_cpi_usd": 0.0,
                "ttr": 0.0,
                "tap_install_rate": 0.0,
            },
            "finding": f"Apple Ads reporting API error: HTTP {report_resp.status_code}",
            "snapshots": [],
        }
        output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return {
            "status": payload["status"],
            "output": str(output_path),
            "reason": payload["status_reason"],
            "campaign_count": 0,
            "active_campaign_count": 0,
        }

    report = report_resp.json().get("data", {}).get("reportingDataResponse", {})
    rows = report.get("row", [])

    campaign_rows: List[Dict[str, Any]] = []
    totals = {
        "impressions": 0,
        "taps": 0,
        "spend_usd": 0.0,
        "installs": 0,
        "tap_installs": 0,
    }
    for row in rows:
        md = row.get("metadata", {})
        total = row.get("total", {})

        campaign_id = int(md.get("campaignId", 0) or 0)
        from_list = campaigns_by_id.get(campaign_id, {})
        status = str(md.get("campaignStatus") or from_list.get("status") or "")
        serving = str(md.get("servingStatus") or from_list.get("servingStatus") or "")
        daily_budget = _amount(from_list.get("dailyBudgetAmount"))

        impressions = int(total.get("impressions", 0) or 0)
        taps = int(total.get("taps", 0) or 0)
        spend = _amount(total.get("localSpend"))
        installs = int(total.get("totalInstalls", 0) or 0)
        tap_installs = int(total.get("tapInstalls", 0) or 0)

        totals["impressions"] += impressions
        totals["taps"] += taps
        totals["spend_usd"] += spend
        totals["installs"] += installs
        totals["tap_installs"] += tap_installs

        campaign_rows.append(
            {
                "id": campaign_id,
                "name": md.get("campaignName") or from_list.get("name") or "",
                "status": status,
                "serving_status": serving,
                "daily_budget_usd": daily_budget,
                "impressions": impressions,
                "taps": taps,
                "spend_usd": round(spend, 2),
                "installs": installs,
                "tap_installs": tap_installs,
            }
        )

    active_count = sum(
        1 for c in campaign_rows if _status_active(c.get("status", ""), c.get("serving_status", ""))
    )
    avg_cpt = totals["spend_usd"] / totals["taps"] if totals["taps"] > 0 else 0.0
    tap_install_cpi = (
        totals["spend_usd"] / totals["tap_installs"] if totals["tap_installs"] > 0 else 0.0
    )
    ttr = (totals["taps"] / totals["impressions"]) if totals["impressions"] > 0 else 0.0
    tap_install_rate = (totals["tap_installs"] / totals["taps"]) if totals["taps"] > 0 else 0.0

    if len(campaign_rows) == 0:
        finding = f"API reports 0 campaign(s) for adamId {adam_id}."
    else:
        finding = (
            f"API reports {len(campaign_rows)} campaign(s), {active_count} active; "
            f"30d taps {totals['taps']}, spend ${totals['spend_usd']:.2f}, installs {totals['installs']}."
        )

    payload = {
        "generated_at": now,
        "source": "apple_ads_api",
        "status": "ok",
        "status_reason": "",
        "window_days": window_days,
        "adam_id": adam_id,
        "campaign_count": len(campaign_rows),
        "active_campaign_count": active_count,
        "campaigns": campaign_rows,
        "metrics_30d": {
            "impressions": totals["impressions"],
            "taps": totals["taps"],
            "spend_usd": round(totals["spend_usd"], 2),
            "installs": totals["installs"],
            "avg_cpt_usd": round(avg_cpt, 4),
            "tap_install_cpi_usd": round(tap_install_cpi, 4),
            "ttr": round(ttr, 6),
            "tap_install_rate": round(tap_install_rate, 6),
        },
        "finding": finding,
        "snapshots": [],
    }

    if output_path.exists():
        try:
            existing = json.loads(output_path.read_text(encoding="utf-8"))
            snapshots = existing.get("snapshots", [])
            if isinstance(snapshots, list):
                payload["snapshots"] = snapshots
        except (json.JSONDecodeError, OSError):
            payload["snapshots"] = []

    payload["snapshots"].append(
        {
            "timestamp": now,
            "campaign_count": payload["campaign_count"],
            "active_campaign_count": payload["active_campaign_count"],
            "impressions": payload["metrics_30d"]["impressions"],
            "taps": payload["metrics_30d"]["taps"],
            "spend_usd": payload["metrics_30d"]["spend_usd"],
            "installs": payload["metrics_30d"]["installs"],
        }
    )
    payload["snapshots"] = payload["snapshots"][-120:]

    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return {
        "status": payload["status"],
        "output": str(output_path),
        "campaign_count": payload["campaign_count"],
        "active_campaign_count": payload["active_campaign_count"],
        "taps_30d": payload["metrics_30d"]["taps"],
        "spend_usd_30d": payload["metrics_30d"]["spend_usd"],
        "installs_30d": payload["metrics_30d"]["installs"],
        "finding": payload["finding"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Apple Ads live metrics snapshot")
    parser.add_argument("--repo-root", default=".", help="Repository root")
    parser.add_argument("--window-days", type=int, default=30, help="Rolling reporting window")
    parser.add_argument(
        "--adam-id",
        type=int,
        default=DEFAULT_ADAM_ID,
        help="App Store app ID (adamId)",
    )
    args = parser.parse_args()
    result = run(Path(args.repo_root).resolve(), window_days=args.window_days, adam_id=args.adam_id)
    print(json.dumps(result, indent=2))
    return 0 if result.get("status") in {"ok", "skipped"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
