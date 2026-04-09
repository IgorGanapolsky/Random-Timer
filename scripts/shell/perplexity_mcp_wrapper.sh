#!/bin/bash
# Wrapper that loads .env before launching the MCP server
# Claude Code MCP servers don't auto-source .env files
set -a
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
if [ -f "$PROJECT_DIR/.env" ]; then
  source "$PROJECT_DIR/.env"
fi
set +a
exec python3 "$SCRIPT_DIR/perplexity_mcp_server.py"
