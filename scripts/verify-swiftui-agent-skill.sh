#!/usr/bin/env bash
set -euo pipefail

CODEX_HOME_DIR="${CODEX_HOME:-$HOME/.codex}"
SKILL_NAME="${SWIFTUI_AGENT_SKILL_NAME:-swiftui-pro}"
TARGET_DIR="$CODEX_HOME_DIR/skills/$SKILL_NAME"

required_paths=(
  "$TARGET_DIR/SKILL.md"
  "$TARGET_DIR/agents"
  "$TARGET_DIR/references"
)

for path in "${required_paths[@]}"; do
  if [[ ! -e "$path" ]]; then
    echo "Missing SwiftUI skill path: $path" >&2
    exit 1
  fi
done

echo "SwiftUI skill verified: $TARGET_DIR"
