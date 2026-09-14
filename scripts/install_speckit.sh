#!/usr/bin/env bash
# Install / refresh GitHub Spec Kit for Random Timer (zero-cost uv tool).
# Upstream: https://github.com/github/spec-kit
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PIN="${SPECKIT_CLI_VERSION:-1.0.6}"
export PATH="${HOME}/.local/bin:${PATH}"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required: https://docs.astral.sh/uv/" >&2
  exit 1
fi

echo "Installing specify-cli==${PIN}"
uv tool install "specify-cli==${PIN}" --force

if [[ ! -d .specify ]]; then
  echo "Initializing Spec Kit (cursor-agent) into repo"
  specify init --here --force --non-interactive --integration cursor-agent --ignore-agent-tools
  specify integration install claude --force || true
  specify extension add bug --force || true
else
  echo ".specify present — skipping init (re-run specify init --here --force to refresh shared templates)"
fi

echo "Done. Skills: /speckit-specify /speckit-plan /speckit-tasks /speckit-implement /speckit-converge"
echo "Bug loop: /speckit-bug-assess → /speckit-bug-fix → /speckit-bug-test"
echo "Gate: python3 scripts/speckit_gate.py --json"
