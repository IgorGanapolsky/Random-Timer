#!/usr/bin/env bash
# Safe maintenance loop — hygiene + Python tests only.
# Does NOT delete worktrees or native-android scripts (prior version was hazardous).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

LOG_FILE="logs/maintenance_$(date +%Y%m%d).log"
mkdir -p logs

exec > >(tee -a "$LOG_FILE") 2>&1

echo "--- Maintenance loop (safe): $(date -u +"%Y-%m-%dT%H:%M:%SZ") ---"

echo "==> Hygiene check"
bash scripts/shell/hygiene-check.sh

echo "==> Repo metrics"
bash scripts/shell/metrics_repo.sh

echo "==> Python unit tests (scripts/)"
if command -v uv >/dev/null 2>&1; then
  uv run pytest scripts/tests/ -q --tb=no
else
  python3 -m pytest scripts/tests/ -q --tb=no
fi

echo "--- Maintenance loop complete ---"
