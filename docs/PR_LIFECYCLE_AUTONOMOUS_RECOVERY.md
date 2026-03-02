# PR Lifecycle and Autonomous Recovery

This document defines the deterministic PR lifecycle used by workflow automation in this repository.

## Scope

- `.github/workflows/pr-state-machine.yml`
- `.github/workflows/claude-review.yml`
- `.github/workflows/enforce-develop-to-main.yml`

## Lifecycle States

PR state is represented by a single label and a commit status context (`pr/state-machine`):

- `pr-state:draft`
  - PR is draft.
  - Commit status: `pending`.
- `pr-state:ci_running`
  - PR is ready for review but required checks are still pending, missing, or unresolved.
  - Commit status: `pending`.
- `pr-state:ci_green`
  - All required checks are passing.
  - Commit status: `success`.
- `pr-state:blocked`
  - One or more required checks are failing.
  - Commit status: `failure`.

Only one `pr-state:*` label should exist on a PR at any time.

## Required Check Resolution

`pr-state-machine.yml` resolves required checks in a fixed order:

1. Branch protection required status checks for the PR base branch.
2. Repository variable fallback: `PR_REQUIRED_CHECKS` (comma-separated list).
3. If neither source provides checks, state remains `ci_running` (non-guessing fallback).

This avoids non-deterministic behavior from optional/non-required checks.

## Incident Automation

When state is `pr-state:blocked`, automation opens or updates one incident issue per PR:

- Title format: `PR Incident: #<PR_NUMBER> required checks failing`
- Labels: `incident`, `pr-state-machine`
- Body includes:
  - PR URL
  - workflow run URL (evidence link)
  - base branch
  - head SHA
  - failed required check list with details links (when available)

When state recovers from `blocked` to non-blocked, the existing incident is automatically commented with recovery evidence and closed.

## Claude Review Safety Mode

`claude-review.yml` is advisory and non-blocking:

- `Claude Review` job runs with `continue-on-error: true`.
- Claude action step also uses `continue-on-error: true`.
- If `ANTHROPIC_API_KEY` is unavailable, review is skipped with an advisory notice.
- Auto-approve runs only for non-draft PRs from branches in this repository and is also non-blocking.

Result: Claude automation cannot deadlock required CI checks.

## Enforcement Workflow Safety

`enforce-develop-to-main.yml` checks out the PR base branch policy scripts (not PR head code) before validating release-branch constraints. This keeps execution deterministic and reduces risk from untrusted PR branch modifications.
