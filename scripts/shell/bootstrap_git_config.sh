#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
hooks_dir="$(git rev-parse --git-path hooks)"
managed_hook="$hooks_dir/pre-commit"
managed_marker="# random-timer-managed-hook"
precommit_script="$repo_root/scripts/pre-commit"
hook_name="random-timer-pre-commit"

git_version="$(git version | awk '{print $3}')"

version_ge() {
  local left="$1"
  local right="$2"
  local first
  first="$(printf '%s\n%s\n' "$left" "$right" | sort -V | head -n1)"
  [[ "$first" == "$right" ]]
}

remove_managed_hook_wrapper() {
  if [[ ! -f "$managed_hook" ]]; then
    return
  fi

  if grep -q "$managed_marker" "$managed_hook"; then
    rm -f "$managed_hook"
    return
  fi

  if grep -Fq 'exec ./scripts/pre-commit "$@"' "$managed_hook"; then
    rm -f "$managed_hook"
    return
  fi

  if cmp -s "$managed_hook" "$precommit_script"; then
    rm -f "$managed_hook"
  fi
}

install_managed_hook_wrapper() {
  mkdir -p "$hooks_dir"
  cat >"$managed_hook" <<EOF
#!/usr/bin/env bash
$managed_marker
exec "$precommit_script" "\$@"
EOF
  chmod +x "$managed_hook"
  echo "Installed worktree-safe pre-commit wrapper at $managed_hook"
}

configure_hook_via_git_254() {
  git config --local --unset-all "hook.$hook_name.event" 2>/dev/null || true
  git config --local --unset-all "hook.$hook_name.command" 2>/dev/null || true
  git config --local "hook.$hook_name.command" "$precommit_script"
  git config --local --add "hook.$hook_name.event" pre-commit
  git config --local "hook.$hook_name.enabled" true
  remove_managed_hook_wrapper
  echo "Configured pre-commit via hook.$hook_name.* repo-local config"
}

configure_compare_branches_via_git_254() {
  git config --local status.compareBranches "@{upstream} @{push}"
  echo "Configured git status branch comparisons for @{upstream} and @{push}"
}

main() {
  if [[ ! -x "$precommit_script" ]]; then
    echo "Missing executable pre-commit script at $precommit_script" >&2
    exit 1
  fi

  if version_ge "$git_version" "2.54.0"; then
    configure_hook_via_git_254
    configure_compare_branches_via_git_254
  else
    install_managed_hook_wrapper
    echo "Git $git_version does not support config-defined hooks or status.compareBranches yet; skipped 2.54-only setup"
  fi
}

main "$@"
