# Technical Debt Audit — 2026-05-31

## Honest scope

This audit records **measured baselines**, **CI health**, **hygiene**, **Python coverage**, **RAG status**, and a **prioritized backlog**. It does **not** claim a literal line-by-line review of every file (**1,594** tracked files; **~303,552** tracked lines). Mass deletion of `.md` or `auto/*` branches requires CEO-approved phases.

Prior audits: [2026-05-26](./technical-debt-audit-2026-05-26.md), [2026-04-03](./technical-debt-audit-2026-04-03.md), [2026-03-26](./technical-debt-audit-2026-03-26.md).

## Pre-audit protocol

| Step | Result | Evidence |
|------|--------|----------|
| Read `CLAUDE.md`, `AGENTS.md`, `docs/GEMINI.md` | Done | Workspace rules |
| Query RAG | **Verified** | `python3 .claude/scripts/memory/memory_manager.py --recall` → 4 cells (credentials, code-editing, general, testing) |
| File / line counts | **1,594** files, **303,552** lines | `bash scripts/shell/metrics_repo.sh` @ `origin/develop` `a8b00ac4` |
| Python coverage | **66%** (`scripts/`), **733** tests passed | `uv run pytest scripts/tests/ --cov=scripts -q` |
| CI `develop` | **success** | [26714149790](https://github.com/IgorGanapolsky/Random-Timer/actions/runs/26714149790) |
| Hygiene gate | **0 errors** | `bash scripts/shell/hygiene-check.sh` |
| Operational dry run | **2 blocking failures** | `python3 scripts/operational_verification_bundle.py` |

### Core system snapshot (before changes)

| System | Status |
|--------|--------|
| **RAG (`memory_manager.py`)** | Readable/writable; 4 cells; `--maintain` pruned 0 / merged 0 |
| **Orchestration (`zernio_orchestrate.py`)** | ~65% coverage; live publish path under-tested |
| **CI (`ci.yml`)** | Green on `develop` tip |
| **AdMob GSD** | `admob_status.json`: Android **APPROVED**, `rewarded_rollout` present on `develop` |
| **Monitoring / metrics** | Executive metrics on `develop` stale vs wiki-sync cadence; see JSON ages below |

## Baseline metrics

**Command:** `bash scripts/shell/metrics_repo.sh`  
**Git SHA:** `a8b00ac4` (`origin/develop`)

| Metric | Value |
|--------|-------|
| Tracked files | **1,594** |
| Tracked lines | **303,552** |
| Tracked `.md` | **253** |
| Tracked `.py` (under `scripts/`) | ~**48k** lines (wc aggregate) |
| Extension mix (top) | mp3, md, py, kt, swift (unchanged from May 26 audit) |

## Test coverage report

**Command:** `uv run pytest scripts/tests/ --cov=scripts --cov-report=term-missing:skip-covered -q`  
**Date:** 2026-05-31

| Metric | Before this PR | After this PR (expected) |
|--------|----------------|---------------------------|
| Tests passed | **733** | **735+** |
| Aggregate `scripts/` coverage | **66%** | **~66–67%** (small gain on `verify_app_ads_txt.py`) |
| CI `--cov-fail-under` | **66** | Unchanged |

### Lowest-covered production scripts (&lt;70%)

| Module | Coverage | Priority |
|--------|----------|----------|
| `scripts/verify_release.py` | ~61% | P0 — release gate |
| `scripts/zernio_orchestrate.py` | ~65% | P1 — growth publish |
| `scripts/verify_public_store_versions.py` | ~68% | P1 — store read-back |
| `scripts/verify_app_ads_txt.py` | ~48% → improving | P1 — AdMob P1 |
| `scripts/upload_store_listing_anchor.py` | ~50% | P2 |

**Not measured:** Android JaCoCo / iOS Xcode coverage (requires JVM/Xcode CI jobs).

### Test gaps (backlog)

- [ ] `cro_optimization.py` — no dedicated tests; weekly workflow depends on it
- [ ] `posthog_dashboard.py` — workflow without unit tests
- [ ] RAG ingest/recall integration test in CI (optional smoke)
- [ ] Native billing catalog empty path (Maestro / unit on `ProManager`)

## CI health report

| Branch | Run | Conclusion |
|--------|-----|------------|
| `develop` | [26714149790](https://github.com/IgorGanapolsky/Random-Timer/actions/runs/26714149790) | **success** |
| `main` | [26584105734](https://github.com/IgorGanapolsky/Random-Timer/actions/runs/26584105734) (2026-05-28 dispatch) | **success** — not re-run on today's `develop` integration |

**Operational bundle blockers (local dry run):**

1. `repo_marketing_version_sync` — repo **1.3.42** vs public release **1.3.43**
2. `native_release_last_success` — last `develop` native-release run **failed** ([26686895967](https://github.com/IgorGanapolsky/Random-Timer/actions/runs/26686895967))

**Advisory:** stale `paywall_conversion_report.json`, `north_star.json` (&gt;48h on disk vs CI artifacts).

## Issues found

| # | Category | Finding | Action this PR |
|---|----------|---------|----------------|
| 1 | **Safety** | `maintenance_loop.sh` ran `rm -rf .claude/worktrees/*` and referenced removed `native-android/*.py` | **Replaced** with safe loop (hygiene + metrics + pytest only) |
| 2 | Python | `verify_app_ads_txt.py` under-tested | **Added** HTTP + `main()` exit tests |
| 3 | Docs | New audit report | **This file** |
| 4 | Dead scripts | `play_console_complete.py`, `fully_autonomous_setup.py`, etc. | **Documented** — delete in phased PR |
| 5 | Stale JSON | `live_growth_snapshot.json` (Feb 2026), old north_star copies | **Wiki-sync / executive-metrics** refresh (CI) |
| 6 | Version drift | develop **1.3.42** vs stores **1.3.43** | **Separate** `chore/bump-develop-1.3.43` |
| 7 | Revenue | Paywall catalog empty on 1.3.40+ | **Product** fix — see `monetization_decision_brief.json` |
| 8 | RAG | No worthless cells after maintain | **0** pruned; credentials PAT lesson retained |
| 9 | Docs | 253 `.md` files | **No mass delete** |
| 10 | TODO/FIXME | Sparse in py/kt/swift | Triage only |

## Issues fixed (this PR)

```
Files scanned: 1594 (tracked index)
Issues found: 10+ (prioritized set)
Issues fixed: 2 (maintenance_loop safety, verify_app_ads_txt tests)
Files deleted: 0
Lines removed: ~25 (hazardous shell) + report added
RAG entries cleaned: 0 pruned, 0 merged
```

## Deleted files

**None** in this PR (evidence-based deletion deferred to phased backlog).

## Refactored modules

| Module | Change |
|--------|--------|
| `scripts/shell/maintenance_loop.sh` | Safe maintenance only |
| `scripts/tests/test_verify_app_ads_txt.py` | +2 tests |

## RAG cleanup summary

| Action | Count |
|--------|-------|
| `--recall` at start | 4 cells surfaced |
| `--maintain` (decay + consolidate) | 0 pruned, 0 merged |
| New ingest (audit) | Scheduled post-merge |

**Self-assessment:** Local `memory_manager.py` RAG is **useful** for session continuity; it is **not** a vector DB. External LangSmith/MCP gateway **not verified**.

## Phased backlog (CEO / next PRs)

1. **P0** — Bump `develop` to **1.3.43**; fix Play paywall catalog empty (`CATALOG-EMPTY`).
2. **P0** — Raise `verify_release.py` coverage; fix `native-release` on `develop`.
3. **P1** — Remove or archive dead Play Selenium scripts (`play_console_complete.py`, etc.).
4. **P1** — Consolidate `AGENTS.md` / `GEMINI.md` pointers (no duplicate North Star blocks).
5. **P2** — Prune stale `auto/*` remote branches (automation policy).
6. **P2** — Native Android/iOS coverage gates in CI.

## Completion status

**Not** claiming: *"Technical debt audit complete. Core systems verified operational. CI passing. Test coverage at 100%."*

**Accurate status:**

- Audit **documented** with before metrics and prioritized backlog.
- **Protected systems:** RAG OK, CI green on `develop`, orchestration unchanged (tests pass).
- Coverage remains **66%** on `scripts/` — phased work required.
- Operational dry run still has **2 blocking failures** (version sync + native-release).

**Follow-up audit:** After P0 catalog + version bump merges (target **2026-06-07**).
