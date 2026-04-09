#!/usr/bin/env bash
# Cleanup igor monorepo: prune orphaned worktrees, remove stale Random-Timer variants
#
# Run from Random-Timer or igor. Operates on igor (parent of Random-Timer).
# SAFETY: Skips dirs with uncommitted changes. Reports before deleting.

set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IGOR="$(dirname "$REPO")"

cd "$IGOR"

echo "=== igor monorepo cleanup ==="
echo "IGOR_ROOT: $IGOR"
echo ""

# 1. Openclaw-console: remove worktrees (except main), then prune
if [ -d "openclaw-console/.git" ]; then
  echo "--- openclaw-console worktrees ---"
  git -C openclaw-console worktree prune 2>/dev/null || true
  for dir in openclaw-console-wt-*/; do
    [ -d "$dir" ] || continue
    dir="${dir%/}"
    full="$(realpath "$dir" 2>/dev/null || echo "$IGOR/$dir")"
    if git -C "$dir" status --porcelain 2>/dev/null | grep -q .; then
      echo "  SKIP (dirty): $dir"
      continue
    fi
    echo "  REMOVE worktree: $dir"
    git -C openclaw-console worktree remove "$full" --force 2>/dev/null || rm -rf "$dir"
  done
  git -C openclaw-console worktree prune 2>/dev/null || true
  echo ""
fi

# 2. Random-Timer: run built-in worktree cleanup
if [ -f "$REPO/.claude/hooks/worktree-cleanup.sh" ]; then
  echo "--- Random-Timer worktree cleanup ---"
  CLAUDE_PROJECT_DIR="$REPO" bash "$REPO/.claude/hooks/worktree-cleanup.sh" || true
  echo ""
fi

# 3. _worktrees, _branch-archives: remove empty or orphaned
for container in _worktrees _branch-archives; do
  [ -d "$container" ] || continue
  echo "--- $container ---"
  for dir in "$container"/*/; do
    [ -d "$dir" ] || continue
    dirname=$(basename "$dir")
    if git -C "$REPO" worktree list 2>/dev/null | grep -q "$dir"; then
      echo "  KEEP (registered): $dirname"
      continue
    fi
    if [ -f "${dir}/.git" ]; then
      if git -C "$dir" status --porcelain 2>/dev/null | grep -q .; then
        echo "  SKIP (dirty): $dirname"
        continue
      fi
    fi
    echo "  REMOVE: $container/$dirname"
    rm -rf "$dir"
  done
  [ -z "$(ls -A "$container" 2>/dev/null)" ] && rmdir "$container" 2>/dev/null || true
  echo ""
done

# 4. Random-Timer variants + feat-premium-app-listing: archive if safe
for variant in Random-Timer-english-policy Random-Timer-skill-frontmatter feat-premium-app-listing; do
  [ -d "$variant" ] || continue
  echo "--- $variant ---"
  if [ -d "$variant/.git" ] || [ -f "$variant/.git" ]; then
    if git -C "$variant" status --porcelain 2>/dev/null | grep -q .; then
      echo "  SKIP (dirty): $variant"
      continue
    fi
    # If worktree of Random-Timer, prune; else archive
    if git -C "$REPO" worktree list 2>/dev/null | grep -q "$variant"; then
      echo "  PRUNE worktree: $variant"
      git -C "$REPO" worktree remove "$(realpath "$variant")" --force 2>/dev/null || rm -rf "$variant"
    else
      echo "  ARCHIVE: $variant -> _branch-archives/"
      mkdir -p _branch-archives
      mv "$variant" "_branch-archives/${variant}-$(date +%Y%m%d)" 2>/dev/null || echo "  SKIP (mv failed): $variant"
    fi
  else
    echo "  REMOVE (not git): $variant"
    rm -rf "$variant"
  fi
  echo ""
done

echo "=== done ==="
