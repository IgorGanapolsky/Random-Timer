#!/bin/bash
# Wrapper that loads .env before launching the MCP server
# Claude Code MCP servers don't auto-source .env files
set -a
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPTS_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
if [ -f "$PROJECT_ROOT/.env" ]; then
  source "$PROJECT_ROOT/.env"
fi
set +a
exec python3 "$SCRIPTS_ROOT/perplexity_mcp_server.py"
