#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "==> Verifying MCP config"
grep -q '"mcp-memory-gateway@0.8.0"' .mcp.json
grep -q '"mcp-memory-gateway@0.8.0"' .cursor/mcp.json

echo "==> Verifying tracked project config"
test -f .rlhf/config.json

echo "==> Running gateway doctor"
DOCTOR_EXIT=0
npx -y mcp-memory-gateway@0.8.0 doctor || DOCTOR_EXIT=$?
if [ "$DOCTOR_EXIT" -ne 0 ] && [ "$DOCTOR_EXIT" -ne 1 ]; then
  exit "$DOCTOR_EXIT"
fi

echo "==> Reading gateway summary"
npx -y mcp-memory-gateway@0.8.0 summary

echo "==> Reading gateway lessons"
npx -y mcp-memory-gateway@0.8.0 lessons --query="verification" --limit=5
