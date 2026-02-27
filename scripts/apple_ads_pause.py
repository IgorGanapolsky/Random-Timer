#!/usr/bin/env python3
"""Pause Apple Search Ads campaign via API v5."""

from __future__ import annotations
import os
import sys
import json
from pathlib import Path
import jwt
import requests
import time

BASE_URL = "https://api.searchads.apple.com/api/v5"
CAMPAIGN_ID = 2143440089

def load_env():
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"): continue
            if "=" in line:
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip().strip("'\""))

def _read_private_key() -> str:
    inline = os.getenv("APPLE_ADS_PRIVATE_KEY", "").strip()
    if inline: return inline.replace("\\n", "\n")
    key_path = os.getenv("APPLE_ADS_PRIVATE_KEY_PATH", "private-key.pem")
    p = Path(key_path) if os.path.isabs(key_path) else Path(__file__).resolve().parent.parent / key_path
    return p.read_text()

def generate_jwt_token() -> str:
    key_id = os.environ["APPLE_ADS_KEY_ID"]
    client_id = os.environ["APPLE_ADS_CLIENT_ID"]
    team_id = os.environ["APPLE_ADS_TEAM_ID"]
    private_key = _read_private_key()
    now = int(time.time())
    payload = {"sub": client_id, "aud": "https://appleid.apple.com", "iat": now, "exp": now + 3600, "iss": team_id}
    headers = {"alg": "ES256", "kid": key_id}
    return jwt.encode(payload, private_key, algorithm="ES256", headers=headers)

def get_access_token(client_secret: str) -> str:
    client_id = os.environ["APPLE_ADS_CLIENT_ID"]
    resp = requests.post("https://appleid.apple.com/auth/oauth2/token",
                         data={"grant_type": "client_credentials", "client_id": client_id, "client_secret": client_secret, "scope": "searchadsorg"},
                         headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=30)
    resp.raise_for_status()
    return resp.json()["access_token"]

def main():
    load_env()
    required = ["APPLE_ADS_CLIENT_ID", "APPLE_ADS_TEAM_ID", "APPLE_ADS_KEY_ID", "APPLE_ADS_ORG_ID"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        print(f"ERROR: Missing env vars: {missing}")
        sys.exit(1)

    print(f"Pausing Apple Search Ads campaign {CAMPAIGN_ID}...")
    client_secret = generate_jwt_token()
    access_token = get_access_token(client_secret)
    org_id = os.environ["APPLE_ADS_ORG_ID"]
    headers = {"Authorization": f"Bearer {access_token}", "X-AP-Context": f"orgId={org_id}", "Content-Type": "application/json"}
    
    # Payload to pause serving
    payload = {"servingStatus": "USER_PAUSED"}
    url = f"{BASE_URL}/campaigns/{CAMPAIGN_ID}"
    resp = requests.put(url, headers=headers, json=payload, timeout=30)
    
    if resp.status_code == 200:
        print(f"SUCCESS: Campaign {CAMPAIGN_ID} paused.")
        config_path = Path(__file__).resolve().parent.parent / "marketing" / "data" / "paid_campaigns.json"
        if config_path.exists():
            config = json.loads(config_path.read_text())
            for c in config.get("campaigns", []):
                if c.get("campaign_id") == CAMPAIGN_ID:
                    c["status"] = "paused"
            config["history"].append({"timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "action": "apple_search_ads_paused", "campaign_id": CAMPAIGN_ID})
            config_path.write_text(json.dumps(config, indent=2) + "\n")
    else:
        print(f"FAILED: {resp.status_code} {resp.text}")
        sys.exit(1)

if __name__ == "__main__":
    main()
