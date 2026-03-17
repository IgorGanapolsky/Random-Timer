#!/usr/bin/env bash
set -euo pipefail

CODEX_HOME_DIR="${CODEX_HOME:-$HOME/.codex}"
SKILLS_DIR="$CODEX_HOME_DIR/skills"
SKILL_NAME="${SWIFTUI_AGENT_SKILL_NAME:-swiftui-pro}"
TARGET_DIR="$SKILLS_DIR/$SKILL_NAME"
INSTALLER_ROOT="$CODEX_HOME_DIR/skills/.system/skill-installer"
INSTALLER_SCRIPT="$INSTALLER_ROOT/scripts/install-skill-from-github.py"

if [[ ! -f "$INSTALLER_SCRIPT" ]]; then
  echo "SwiftUI skill installer helper not found: $INSTALLER_SCRIPT" >&2
  exit 1
fi

if [[ -f "$TARGET_DIR/SKILL.md" ]]; then
  echo "SwiftUI skill already installed: $TARGET_DIR"
  exit 0
fi

mkdir -p "$SKILLS_DIR"

python3 "$INSTALLER_SCRIPT" \
  --repo twostraws/SwiftUI-Agent-Skill \
  --path swiftui-pro \
  --dest "$SKILLS_DIR" \
  --name "$SKILL_NAME"

echo "Installed SwiftUI skill to $TARGET_DIR"
