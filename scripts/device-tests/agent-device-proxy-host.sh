#!/usr/bin/env bash
# Start Callstack agent-device proxy on the device-host Mac (Simulator/ADB).
# Zero-cost path: bind loopback; expose via Tailscale SSH tunnel from the agent machine.
# Do NOT commit the printed daemon auth token.
set -euo pipefail

PORT="${AGENT_DEVICE_PROXY_PORT:-4310}"
HOST="${AGENT_DEVICE_PROXY_HOST:-127.0.0.1}"

if ! command -v npx >/dev/null 2>&1; then
  echo "npx missing — install Node.js >= 22" >&2
  exit 1
fi

echo "Starting agent-device proxy on ${HOST}:${PORT}"
echo "Remote clients: SSH -L ${PORT}:127.0.0.1:${PORT} <this-mac>  OR Tailscale + connect proxy"
echo "Docs: https://oss.callstack.com/agent-device/docs/remote-proxy"
exec npx -y agent-device proxy --host "$HOST" --port "$PORT"
