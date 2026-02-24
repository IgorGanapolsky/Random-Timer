#!/usr/bin/env python3
"""Launch Apple Search Ads campaign via API v5.

Reads campaign config from marketing/data/paid_campaigns.json,
authenticates via JWT, creates campaign + ad groups + keywords,
and enables the campaign.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import jwt
    import requests
except ImportError:
    print("ERROR: pip install PyJWT cryptography requests")
    sys.exit(1)


BASE_URL = "https://api.searchads.apple.com/api/v5"
ADAM_ID = 6758355312  # iOS App Store ID


def load_env():
    """Load .env file into os.environ."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, val = line.partition("=")
                val = val.strip().strip("'\"")
                os.environ.setdefault(key.strip(), val)


def generate_jwt_token() -> str:
    """Generate ES256 JWT for Apple Search Ads API v4."""
    key_id = os.environ["APPLE_ADS_KEY_ID"]
    client_id = os.environ["APPLE_ADS_CLIENT_ID"]
    team_id = os.environ["APPLE_ADS_TEAM_ID"]

    key_path = os.environ.get("APPLE_ADS_PRIVATE_KEY_PATH", "private-key.pem")
    if not os.path.isabs(key_path):
        key_path = str(Path(__file__).resolve().parent.parent / key_path)

    private_key = Path(key_path).read_text()

    now = int(time.time())
    payload = {
        "sub": client_id,
        "aud": "https://appleid.apple.com",
        "iat": now,
        "exp": now + 3600,
        "iss": team_id,
    }
    headers = {
        "alg": "ES256",
        "kid": key_id,
    }
    return jwt.encode(payload, private_key, algorithm="ES256", headers=headers)


def get_access_token(client_secret: str) -> str:
    """Exchange JWT for OAuth access token."""
    client_id = os.environ["APPLE_ADS_CLIENT_ID"]
    resp = requests.post(
        "https://appleid.apple.com/auth/oauth2/token",
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "searchadsorg",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def api_headers(access_token: str, org_id: int) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "X-AP-Context": f"orgId={org_id}",
        "Content-Type": "application/json",
    }


def api_get(path: str, headers: Dict[str, str]) -> Dict[str, Any]:
    url = f"{BASE_URL}{path}"
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def api_post(path: str, headers: Dict[str, str], payload: Any) -> Dict[str, Any]:
    url = f"{BASE_URL}{path}"
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    if resp.status_code >= 400:
        print(f"ERROR {resp.status_code}: {resp.text}")
        resp.raise_for_status()
    return resp.json()


def api_put(path: str, headers: Dict[str, str], payload: Any) -> Dict[str, Any]:
    url = f"{BASE_URL}{path}"
    resp = requests.put(url, headers=headers, json=payload, timeout=30)
    if resp.status_code >= 400:
        print(f"ERROR {resp.status_code}: {resp.text}")
        resp.raise_for_status()
    return resp.json()


def create_campaign(headers: Dict[str, str], budget: float) -> int:
    """Create a paused campaign. Returns campaign ID."""
    payload = {
        "orgId": int(os.environ.get("APPLE_ADS_ORG_ID", "20617940")),
        "name": "Random Tactical Timer - Search v1",
        "budgetAmount": {"amount": str(budget), "currency": "USD"},
        "dailyBudgetAmount": {"amount": str(budget), "currency": "USD"},
        "adamId": ADAM_ID,
        "countriesOrRegions": ["US"],
        "status": "ENABLED",
        "adChannelType": "SEARCH",
        "billingEvent": "TAPS",
        "supplySources": ["APPSTORE_SEARCH_RESULTS"],
    }
    print(f"Creating campaign with ${budget}/day budget...")
    result = api_post("/campaigns", headers, payload)
    campaign_id = result["data"]["id"]
    print(f"  Campaign created: ID={campaign_id}")
    return campaign_id


def create_ad_group(
    headers: Dict[str, str],
    campaign_id: int,
    name: str,
    default_bid: float,
    auto_keywords: bool = False,
) -> int:
    """Create an ad group. Returns ad group ID."""
    import datetime as dt
    start = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000")
    payload = {
        "campaignId": campaign_id,
        "name": name,
        "defaultBidAmount": {"amount": str(default_bid), "currency": "USD"},
        "automatedKeywordsOptIn": auto_keywords,
        "pricingModel": "CPC",
        "status": "ENABLED",
        "startTime": start,
    }
    print(f"  Creating ad group: {name} (bid=${default_bid})...")
    result = api_post(f"/campaigns/{campaign_id}/adgroups", headers, payload)
    ag_id = result["data"]["id"]
    print(f"    Ad group created: ID={ag_id}")
    return ag_id


def add_keywords(
    headers: Dict[str, str],
    campaign_id: int,
    ad_group_id: int,
    keywords: List[Dict[str, Any]],
    match_type: str,
    bid: float,
) -> int:
    """Add keywords to an ad group. Returns count added."""
    apple_match = "EXACT" if match_type == "exact" else "BROAD"
    kw_payload = []
    for kw in keywords:
        kw_payload.append({
            "text": kw["text"],
            "matchType": apple_match,
            "bidAmount": {"amount": str(bid), "currency": "USD"},
            "status": "ACTIVE",
        })

    result = api_post(
        f"/campaigns/{campaign_id}/adgroups/{ad_group_id}/targetingkeywords/bulk",
        headers,
        kw_payload,
    )
    created = len(result.get("data", []))
    errors = result.get("errors", [])
    print(f"    Added {created} keywords ({apple_match}), {len(errors)} errors")
    if errors:
        for e in errors[:3]:
            print(f"      Error: {e}")
    return created


def add_negative_keywords(
    headers: Dict[str, str],
    campaign_id: int,
    negatives: List[str],
) -> int:
    """Add campaign-level negative keywords."""
    payload = [{"text": kw, "matchType": "EXACT"} for kw in negatives]
    result = api_post(
        f"/campaigns/{campaign_id}/negativekeywords/bulk",
        headers,
        payload,
    )
    created = len(result.get("data", []))
    print(f"  Added {created} negative keywords")
    return created


def enable_campaign(headers: Dict[str, str], campaign_id: int) -> str:
    """Verify campaign is enabled (created with ENABLED status)."""
    result = api_get(f"/campaigns/{campaign_id}", headers)
    data = result.get("data", {})
    status = data.get("status", "UNKNOWN")
    serving = data.get("servingStatus", "UNKNOWN")
    print(f"  Campaign status: {status}, serving: {serving}")
    return status


def verify_campaign(headers: Dict[str, str], campaign_id: int) -> Dict[str, Any]:
    """Read back campaign to verify it's live."""
    result = api_get(f"/campaigns/{campaign_id}", headers)
    data = result.get("data", {})
    return {
        "id": data.get("id"),
        "name": data.get("name"),
        "status": data.get("status"),
        "servingStatus": data.get("servingStatus"),
        "dailyBudget": data.get("dailyBudgetAmount"),
    }


def main() -> int:
    load_env()

    required = ["APPLE_ADS_CLIENT_ID", "APPLE_ADS_TEAM_ID", "APPLE_ADS_KEY_ID"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        print(f"ERROR: Missing env vars: {missing}")
        return 1

    # Load campaign config
    config_path = Path(__file__).resolve().parent.parent / "marketing" / "data" / "paid_campaigns.json"
    config = json.loads(config_path.read_text())
    apple_campaign = None
    for c in config.get("campaigns", []):
        if c.get("platform") == "apple_search_ads":
            apple_campaign = c
            break

    if not apple_campaign:
        print("ERROR: No apple_search_ads campaign in paid_campaigns.json")
        return 1

    # Authenticate
    print("Authenticating with Apple Search Ads API v4...")
    client_secret = generate_jwt_token()
    access_token = get_access_token(client_secret)
    org_id = int(os.environ.get("APPLE_ADS_ORG_ID", "20617940"))
    hdrs = api_headers(access_token, org_id)
    print(f"  Authenticated (org={org_id})")

    # Check existing campaigns
    print("Checking existing campaigns...")
    existing = api_get("/campaigns", hdrs)
    existing_campaigns = existing.get("data", [])
    print(f"  Found {len(existing_campaigns)} existing campaigns")

    # Reuse existing campaign or create new one
    budget = apple_campaign.get("daily_budget_usd", 10.0)
    campaign_id = None
    for ec in existing_campaigns:
        if "Random Tactical Timer" in ec.get("name", ""):
            campaign_id = ec["id"]
            print(f"  Reusing existing campaign: ID={campaign_id} ({ec['name']})")
            break
    if campaign_id is None:
        campaign_id = create_campaign(hdrs, budget)

    # Create ad groups and keywords
    total_keywords = 0
    for ag in apple_campaign.get("ad_groups", []):
        ag_name = ag["name"]
        match_type = ag.get("match_type", "exact")
        bid = ag.get("max_cpt_usd", 1.50)
        is_search = match_type == "search"

        ag_id = create_ad_group(hdrs, campaign_id, ag_name, bid, auto_keywords=is_search)
        keywords = ag.get("keywords", [])
        if keywords:
            count = add_keywords(hdrs, campaign_id, ag_id, keywords, match_type, bid)
            total_keywords += count

    # Add negative keywords
    negatives = apple_campaign.get("negative_keywords", [])
    if negatives:
        add_negative_keywords(hdrs, campaign_id, negatives)

    # Enable campaign
    print("Enabling campaign...")
    status = enable_campaign(hdrs, campaign_id)

    # Verify
    print("Verifying campaign...")
    verification = verify_campaign(hdrs, campaign_id)
    print(f"  Verification: {json.dumps(verification, indent=2)}")

    # Update config status
    apple_campaign["status"] = "active"
    apple_campaign["campaign_id"] = campaign_id
    apple_campaign["launched_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    config["history"].append({
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "action": "apple_search_ads_launched",
        "campaign_id": campaign_id,
        "keywords": total_keywords,
        "daily_budget_usd": budget,
    })
    config_path.write_text(json.dumps(config, indent=2) + "\n")
    print(f"Updated paid_campaigns.json: status=active, campaign_id={campaign_id}")

    print(f"\nDONE: Campaign {campaign_id} is {status} with {total_keywords} keywords at ${budget}/day")
    return 0


if __name__ == "__main__":
    sys.exit(main())
