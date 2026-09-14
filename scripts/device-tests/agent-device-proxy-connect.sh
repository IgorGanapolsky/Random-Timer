#!/usr/bin/env bash
# Connect a remote agent client to a device-host agent-device proxy (Callstack pattern).
# Requires: AGENT_DEVICE_DAEMON_AUTH_TOKEN + AGENT_DEVICE_DAEMON_BASE_URL
# Prefer: http://127.0.0.1:4310/agent-device via SSH -L (zero cost) over paid ngrok.
set -euo pipefail

: "${AGENT_DEVICE_DAEMON_AUTH_TOKEN:?set AGENT_DEVICE_DAEMON_AUTH_TOKEN from host proxy output}"
BASE="${AGENT_DEVICE_DAEMON_BASE_URL:-http://127.0.0.1:4310/agent-device}"

if ! command -v npx >/dev/null 2>&1; then
  echo "npx missing — install Node.js >= 22" >&2
  exit 1
fi

echo "Connecting proxy client → ${BASE}"
npx -y agent-device connect proxy --daemon-base-url "$BASE" --daemon-auth-token "$AGENT_DEVICE_DAEMON_AUTH_TOKEN"
npx -y agent-device devices --platform ios --json
echo "Connected. Use: agent-device open <bundle> --platform ios && agent-device snapshot -i"
