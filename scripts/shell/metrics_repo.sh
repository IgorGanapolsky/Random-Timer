#!/usr/bin/env bash
# Reproducible repo size metrics (tracked files only). Optional: tokei or cloc for language split.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

echo "=== Random Timer repo metrics (git index) ==="
echo "tracked_files: $(git ls-files | wc -l | tr -d ' ')"
echo -n "tracked_lines: "
git ls-files | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}'

if command -v tokei >/dev/null 2>&1; then
  echo ""
  echo "=== tokei (if installed) ==="
  tokei . --exclude '.git' --exclude 'node_modules' --exclude '.venv' 2>/dev/null || true
elif command -v cloc >/dev/null 2>&1; then
  echo ""
  echo "=== cloc --vcs=git (if installed) ==="
  cloc . --vcs=git --quiet 2>/dev/null || true
else
  echo ""
  echo "Hint: install tokei or cloc for language breakdown."
fi
