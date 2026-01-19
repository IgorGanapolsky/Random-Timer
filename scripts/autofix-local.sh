#!/bin/zsh
set -euo pipefail

# Ensure PATH works under launchd (no shell rc files are sourced)
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

REPO_DIR="/Users/igorganapolsky/workspace/git/apps/RandomTimer"

cd "$REPO_DIR"

# Fetch latest, rebase, install deps, run autofix
git fetch --all --prune || true
git pull --rebase || true

npm ci --no-audit --no-fund
npm run autofix

# Commit and push if there are changes
if ! git diff --quiet; then
  git add -A
  git commit -m "chore: local hourly autofix (prettier + eslint)"
  git push
fi

echo "[$(date)] Autofix run completed"


