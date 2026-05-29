#!/usr/bin/env bash
# One-time AdMob API auth for local CLI (ADC + admob.readonly scope).
set -euo pipefail
gcloud auth application-default login \
  --scopes="https://www.googleapis.com/auth/admob.readonly,https://www.googleapis.com/auth/cloud-platform"
echo "OK. Run: python3 scripts/admob_token_probe.py"
