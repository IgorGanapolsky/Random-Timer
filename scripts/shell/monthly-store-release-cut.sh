#!/usr/bin/env bash
# monthly-store-release-cut.sh — Cut release/v* from develop after optional monthly audio PR merge.
#
# Environment:
#   GITHUB_REPOSITORY  owner/name (GitHub Actions)
#   GITHUB_OUTPUT      key=value lines for workflow outputs
#   SKIP_AUDIO_MERGE=1 skip feat/audio-pack-YYYY-MM merge attempt
#   DRY_RUN=1          print plan only; no bump/commit/push
#
# Outputs (GITHUB_OUTPUT when set):
#   version=1.2.3
#   pushed=true|false
#   skip_reason=...    optional

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

write_kv() {
  local kv="$1"
  if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
    echo "$kv" >> "$GITHUB_OUTPUT"
  fi
  return 0
}

SKIP_AUDIO_MERGE="${SKIP_AUDIO_MERGE:-0}"
DRY_RUN="${DRY_RUN:-0}"

git fetch origin develop
git checkout develop
git pull --ff-only origin develop

if [[ "${SKIP_AUDIO_MERGE}" != "1" && -n "${GITHUB_REPOSITORY:-}" ]]; then
  MONTH_UTC=$(date -u +%Y-%m)
  AUDIO_BRANCH="feat/audio-pack-${MONTH_UTC}"
  PR_NUM=$(gh pr list --repo "$GITHUB_REPOSITORY" --base develop --state open \
    --json number,headRefName \
    --jq "map(select(.headRefName==\"${AUDIO_BRANCH}\")) | .[0].number // empty" 2>/dev/null || true)
  if [[ -n "${PR_NUM}" ]]; then
    echo "Attempting squash merge of PR #${PR_NUM} (${AUDIO_BRANCH})"
    if gh pr merge "$PR_NUM" --repo "$GITHUB_REPOSITORY" --squash --delete-branch; then
      git fetch origin develop
      git pull --ff-only origin develop
    else
      echo "::warning::Monthly audio PR #${PR_NUM} did not merge; continuing with current develop"
    fi
  else
    echo "No open PR for ${AUDIO_BRANCH} (monthly audio may already be merged or not generated yet)"
  fi
fi

NEW_VERSION=$(python3 "$REPO_ROOT/scripts/monthly_release_utils.py" --repo-root "$REPO_ROOT")
write_kv "version=${NEW_VERSION}"

if git ls-remote --heads origin "refs/heads/release/v${NEW_VERSION}" | grep -q .; then
  echo "Remote already has release/v${NEW_VERSION}; skipping cut"
  write_kv "pushed=false"
  write_kv "skip_reason=branch_exists"
  exit 0
fi

if [[ "$DRY_RUN" == "1" ]]; then
  echo "DRY_RUN: would create release/v${NEW_VERSION} from develop @ $(git rev-parse --short HEAD)"
  write_kv "pushed=false"
  write_kv "dry_run=true"
  exit 0
fi

git checkout -b "release/v${NEW_VERSION}"

bash "$REPO_ROOT/scripts/shell/bump-version.sh" "$NEW_VERSION"

NEW_CODE=$(python3 "$REPO_ROOT/scripts/source_versions.py" --repo-root "$REPO_ROOT" --format value --key ANDROID_VERSION_CODE)
ANDROID_CHANGELOG="$REPO_ROOT/native-android/fastlane/metadata/android/en-US/changelogs/${NEW_CODE}.txt"
if [[ -f "$ANDROID_CHANGELOG" ]]; then
  {
    echo "Monthly Pro voice callouts and sound arsenal refresh. Stability fixes."
    tail -n +2 "$ANDROID_CHANGELOG" || true
  } >"${ANDROID_CHANGELOG}.tmp"
  mv "${ANDROID_CHANGELOG}.tmp" "$ANDROID_CHANGELOG"
fi

IOS_RN="$REPO_ROOT/native-ios/fastlane/metadata/en-US/release_notes.txt"
if [[ -f "$IOS_RN" ]]; then
  {
    echo "Monthly Pro audio refresh — voice callouts and sound library."
    echo ""
    cat "$IOS_RN"
  } >"${IOS_RN}.tmp"
  mv "${IOS_RN}.tmp" "$IOS_RN"
fi

git add -A
if git diff --cached --quiet; then
  echo "::error::No staged changes after bump (unexpected)" >&2
  exit 1
fi

git commit -m "chore(release): v${NEW_VERSION} monthly Pro audio storefront"

git push -u origin "HEAD:refs/heads/release/v${NEW_VERSION}"

if [[ -n "${GITHUB_REPOSITORY:-}" ]]; then
  EXISTING=$(gh pr list --repo "$GITHUB_REPOSITORY" --base main --head "release/v${NEW_VERSION}" \
    --json number --jq '.[0].number // empty' 2>/dev/null || true)
  if [[ -z "${EXISTING}" ]]; then
    gh pr create --repo "$GITHUB_REPOSITORY" --base main --head "release/v${NEW_VERSION}" \
      --title "Release v${NEW_VERSION}" \
      --body "Automated monthly storefront release. Includes the scheduled Pro voice callouts + sound arsenal refresh when merged into \`develop\` before this cut.

- Approve **production-signoff** on the [Native App Release](https://github.com/${GITHUB_REPOSITORY}/actions/workflows/native-release.yml) run for this branch.
- Confirm store metadata/changelogs if needed."
  else
    echo "PR to main already exists (#${EXISTING})"
  fi
fi

write_kv "pushed=true"
echo "Pushed release/v${NEW_VERSION}"
