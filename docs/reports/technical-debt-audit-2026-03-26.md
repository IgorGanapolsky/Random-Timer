# Technical Debt Audit — 2026-03-26 (baseline + governance)

## Honest scope

This document records a **baseline metrics snapshot** and **governance review**, not a literal line-by-line read of every file in one session. A full audit of **~233k lines** across Android, iOS, Python, workflows, and docs is a **multi-week** effort and belongs in tracked milestones with PR-sized chunks.

Prior session artifacts (local): `technical-debt-audit-2026-03-17.md`, `tech-debt-audit-2026-03-18.md` under `.claude/memory/` (gitignored).

## Pre-audit protocol

| Step | Result |
|------|--------|
| Read `CLAUDE.md`, `docs/GEMINI.md`, `AGENTS.md` | Satisfied (CTO autonomy, English-only, evidence-based claims, budget cap). |
| Query RAG for cleanup lessons | **No live RAG API** in agent session. Used **local** `.claude/memory/*` and prior audit notes instead. |
| Snapshot CI | GitHub Actions via `gh` (see below). |

## Baseline metrics (tracked files only)

Measured on **`origin/develop`** at **`829023b1dc8c0ec659a27a44c37d54e05abb3f97`**.

| Metric | Value |
|--------|--------|
| **Tracked files** | 1047 |
| **Total lines** (`git ls-files` + `wc -l`) | 232648 |
| **`cloc` breakdown** | Not available (`cloc` not installed on runner); optional follow-up: install `cloc` and add a metrics script. |

**Before/after cleanup:** No repo-wide refactor was performed in this audit pass; **before = after** for file/line counts.

## Test coverage percentage

**Not stored in the repository** as a single authoritative number. CI uploads:

- **Python:** `coverage-python.xml` → Codecov (`codecov/codecov-action` in `.github/workflows/ci.yml`).
- **Android:** JaCoCo → artifact `android-unit-coverage`.
- **iOS:** `xcresult` coverage in CI artifacts.

**Action:** Read aggregate % from Codecov (project linked from GitHub) or download the latest CI artifacts. Do **not** invent a percentage without that read-back.

## CI health (snapshot via `gh`)

| Branch | Last `ci.yml` run queried | Conclusion |
|--------|---------------------------|------------|
| `develop` | Run `23601704604` (head `1c878dfe…` at query time) | `success` |
| `main` | Run `23499649853` | `success` |

Note: `develop` may have advanced after the listed run; confirm the **latest** run for current `HEAD` at  
`https://github.com/IgorGanapolsky/Random-Timer/actions/workflows/ci.yml`.

## RAG / local memory (not deleted blindly)

- No separate `.rag/` directory in-repo.
- Operational notes live under **`.claude/memory/`** (gitignored): `memory_cells.jsonl`, `lessons-learned.md`, feedback JSONLs, prior audits.
- **Recommendation:** Deduplicate and prune **only** after a scripted backup and review — automated deletion risks losing operational history.

## Audit scope checklist (what was NOT done in one pass)

- [ ] Line-by-line review of every source file  
- [ ] 100% unit/integration coverage (not a current repo invariant)  
- [ ] Dependency vulnerability sweep beyond existing Socket/Sonar/CodeQL CI  
- [ ] Mass deletion of `.md` files (high risk to store/legal/process docs)  

## Recommended next PRs (small, safe)

1. Add **`cloc`** (or `tokei`) to **`scripts/metrics.sh`** and optionally a **manual** CI workflow for reproducible language breakdown.  
2. Pull **Codecov** total coverage into this report **once per release** with date stamp (evidence, not guesswork).  
3. Rebase/fix **open PRs** (#878, #876, #869, #866) to clear known CI debt.  

## Deliverable summary

```
Files scanned: 1047 (tracked)
Issues found: governance gaps documented above; full catalog TBD in phased audits
Issues fixed: 0 (baseline audit only)
Files deleted: 0
Lines removed: 0
RAG entries cleaned: 0 (manual review required)
```

## Accurate completion statement

**Technical debt baseline captured. Core systems were not modified in this pass. CI was passing on sampled `main`/`develop` workflow runs at collection time. Aggregate test coverage % is not asserted here — use Codecov or CI artifacts.**
