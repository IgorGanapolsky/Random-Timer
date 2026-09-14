#!/usr/bin/env bash
# SessionStart: inject obra/superpowers using-superpowers bootstrap (repo-local).
# Upstream: https://github.com/obra/superpowers (v6.3.0)
# Visual companion traffic: disabled for Random Timer.
set -euo pipefail
export SUPERPOWERS_DISABLE_TELEMETRY=1

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SKILL="${ROOT}/.cursor/skills/using-superpowers/SKILL.md"
if [[ ! -f "$SKILL" ]]; then
  SKILL="${ROOT}/.claude/skills/using-superpowers/SKILL.md"
fi
if [[ ! -f "$SKILL" ]]; then
  printf '%s\n' '{"additional_context":"Superpowers bootstrap skill missing. Run ./scripts/install_superpowers.sh"}'
  exit 0
fi

content=$(cat "$SKILL")
escape_for_json() {
  local s="$1"
  s="${s//\\/\\\\}"
  s="${s//\"/\\\"}"
  s="${s//$'\n'/\\n}"
  s="${s//$'\r'/\\r}"
  s="${s//$'\t'/\\t}"
  printf '%s' "$s"
}
escaped=$(escape_for_json "$content")
ctx="<EXTREMELY_IMPORTANT>\nYou have Superpowers (obra/superpowers v6.3.0, vendored).\n\n**Random Timer bridge:** Spec Kit = feature SDD (docs/SPEC_KIT.md). OpenGSD = phase loop (docs/GSD_OPENGSD.md). Superpowers = process skills (TDD, debug, verify, worktrees, subagents). Prefer Superpowers for how; Spec Kit/OpenGSD for where artifacts live.\n\n**Below is using-superpowers:**\n\n${escaped}\n</EXTREMELY_IMPORTANT>"
printf '{\n  "additional_context": "%s"\n}\n' "$ctx"
exit 0
