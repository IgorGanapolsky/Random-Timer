# Release Proof Report — 2026-02-26 (UTC)

Snapshot time: `2026-02-26T02:33:20Z`  
Repository: `IgorGanapolsky/Random-Timer` (default branch: `develop`)

## 1) Merged PRs and Commits (verifiable)
Latest merged PRs:

| PR | Merged At (UTC) | Merge Commit | Title |
|---|---|---|---|
| [#489](https://github.com/IgorGanapolsky/Random-Timer/pull/489) | 2026-02-25T22:48:30Z | `0a737a7d03085498205cc0fe4d99d742954001ca` | fix(ios-metadata): fallback when ASC locks screenshot deletion |
| [#487](https://github.com/IgorGanapolsky/Random-Timer/pull/487) | 2026-02-25T22:39:08Z | `d1b454eea0a9bcb83e7be7109cc80453da87ecaa` | fix(asc): tolerate screenshot delete state-lock during metadata reset |
| [#484](https://github.com/IgorGanapolsky/Random-Timer/pull/484) | 2026-02-25T22:20:08Z | `ef75b44bab27b117aaa707d8dfe2897e20278da4` | fix(android): icon parity with iOS |
| [#483](https://github.com/IgorGanapolsky/Random-Timer/pull/483) | 2026-02-25T22:29:53Z | `6ac6db1b15ba4efc28b48b9f6197301f5a4eb071` | feat(ios-listing): high-ROI App Store creative + copy refresh |
| [#482](https://github.com/IgorGanapolsky/Random-Timer/pull/482) | 2026-02-25T21:30:31Z | `03a182898d81277bbfd68a713bfc5073c8c40b71` | ci: keep develop green when metrics/auth prerequisites are missing |

Latest commits on `develop`:

| SHA | Commit Date (UTC) | Subject |
|---|---|---|
| [`0a737a7`](https://github.com/IgorGanapolsky/Random-Timer/commit/0a737a7d03085498205cc0fe4d99d742954001ca) | 2026-02-25T22:48:30Z | fix(ios-metadata): fallback when ASC locks screenshot deletion (#489) |
| [`d1b454e`](https://github.com/IgorGanapolsky/Random-Timer/commit/d1b454eea0a9bcb83e7be7109cc80453da87ecaa) | 2026-02-25T22:39:08Z | fix(asc): tolerate screenshot delete state-lock during metadata reset (#487) |
| [`6ac6db1`](https://github.com/IgorGanapolsky/Random-Timer/commit/6ac6db1b15ba4efc28b48b9f6197301f5a4eb071) | 2026-02-25T22:29:53Z | feat(ios-listing): high-ROI App Store creative + copy refresh (#483) |
| [`ef75b44`](https://github.com/IgorGanapolsky/Random-Timer/commit/ef75b44bab27b117aaa707d8dfe2897e20278da4) | 2026-02-25T22:20:08Z | fix(android): icon parity with iOS (#484) |
| [`03a1828`](https://github.com/IgorGanapolsky/Random-Timer/commit/03a182898d81277bbfd68a713bfc5073c8c40b71) | 2026-02-25T21:30:31Z | ci: keep develop green when metrics/auth prerequisites are missing |

## 2) CI Runs
`ci.yml` (pushes to `develop`):
- Latest 5: all `success`.
- Last 13 totals: `success=7`, `failure=6`, `cancelled=0`.

Latest 5 `ci.yml` push runs:
- [22419385955](https://github.com/IgorGanapolsky/Random-Timer/actions/runs/22419385955) `success` (`0a737a7`) at 2026-02-25T22:48:33Z
- [22419079644](https://github.com/IgorGanapolsky/Random-Timer/actions/runs/22419079644) `success` (`d1b454e`) at 2026-02-25T22:39:11Z
- [22418770916](https://github.com/IgorGanapolsky/Random-Timer/actions/runs/22418770916) `success` (`6ac6db1`) at 2026-02-25T22:29:56Z
- [22418472859](https://github.com/IgorGanapolsky/Random-Timer/actions/runs/22418472859) `success` (`ef75b44`) at 2026-02-25T22:20:12Z
- [22416783257](https://github.com/IgorGanapolsky/Random-Timer/actions/runs/22416783257) `success` (`03a1828`) at 2026-02-25T21:30:34Z

## 3) Metadata Sync Run Status (`ios-metadata-sync.yml`)
- Latest run: [22419392663](https://github.com/IgorGanapolsky/Random-Timer/actions/runs/22419392663) on `develop` (`0a737a7`) => `success` at 2026-02-25T22:48:46Z.
- Last 20 totals: `success=9`, `failure=11`, `cancelled=0`.

Recent 5 runs:
- [22419392663](https://github.com/IgorGanapolsky/Random-Timer/actions/runs/22419392663) `success`
- [22419085644](https://github.com/IgorGanapolsky/Random-Timer/actions/runs/22419085644) `failure`
- [22418783530](https://github.com/IgorGanapolsky/Random-Timer/actions/runs/22418783530) `failure`
- [22417990594](https://github.com/IgorGanapolsky/Random-Timer/actions/runs/22417990594) `failure`
- [22368062054](https://github.com/IgorGanapolsky/Random-Timer/actions/runs/22368062054) `success`

## 4) Artifact Facts (Screenshots + Metadata Fields)
Source: `python3 scripts/asc_verify_ready.py --version 1.2.1 --skip-build-check --json .artifacts/asc_verify_ready_20260226.json`

Verified App Store Connect facts:
- App/version/state: `app_id=6758355312`, `version=1.2.1`, `app_store_state=WAITING_FOR_REVIEW`
- Build linkage: `build=20`, `processingState=VALID` (check executed in metadata-only mode)
- Screenshot counts (COMPLETE delivered):
  - `APP_IPHONE_67`: `4/4 COMPLETE`
  - `APP_IPAD_PRO_3GEN_129`: `3/3 COMPLETE`
- Screenshot delivery state counts:
  - iPhone: `{"COMPLETE": 4}`
  - iPad: `{"COMPLETE": 3}`
- Metadata fields present:
  - Localization `en-US`: `description_len=1137`, `keywords_len=95`
  - `supportUrl=https://github.com/IgorGanapolsky/Random-Timer/issues`
  - `privacyPolicyUrl=https://github.com/IgorGanapolsky/Random-Timer/blob/main/PRIVACY_POLICY.md`

Note: `Pricing Set` and `Age Rating Completed` checks were marked as skipped by script due App Store Connect endpoint path errors (`HTTP 404 PATH_ERROR`) in this API route.

## 5) Open Security Alerts (Counts)
GitHub API counts at snapshot time:
- Code scanning open alerts: `0`
- Secret scanning open alerts: `0`
- Dependabot open alerts: `0`

## 6) Unresolved Review Thread Counts
Open PRs:
- Open PR count: `0`
- Unresolved review threads on open PRs: `0`

Recent merged PRs (last 10):
- Total unresolved review threads: `11`
- Non-zero PRs: `#483 (1)`, `#481 (4)`, `#480 (4)`, `#475 (2)`

## Evidence Commands Used
- `gh pr list -R IgorGanapolsky/Random-Timer --state merged --limit 5 --json number,title,mergedAt,mergeCommit,url`
- `gh api '/repos/IgorGanapolsky/Random-Timer/commits?sha=develop&per_page=5'`
- `gh run list -R IgorGanapolsky/Random-Timer --workflow ci.yml ...`
- `gh run list -R IgorGanapolsky/Random-Timer --workflow ios-metadata-sync.yml ...`
- `python3 scripts/asc_verify_ready.py --version 1.2.1 --skip-build-check --json .artifacts/asc_verify_ready_20260226.json`
- `gh api /repos/IgorGanapolsky/Random-Timer/{code-scanning,secret-scanning,dependabot}/alerts?...`
- `gh api graphql` queries for unresolved review threads (open + merged PR sets)
