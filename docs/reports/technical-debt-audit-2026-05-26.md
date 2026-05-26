# Technical Debt Audit — 2026-05-26

## Honest scope

This pass records **measured baselines**, **CI health**, **hygiene gate status**, and **Python automation coverage** with command evidence. It does **not** claim a literal line-by-line review of every file (1,550 tracked files; ~300k lines). Phased PRs remain the execution model. Prior audits: [2026-03-26](./technical-debt-audit-2026-03-26.md), [2026-04-03](./technical-debt-audit-2026-04-03.md).

## Pre-audit protocol

| Step | Result |
|------|--------|
| Read `CLAUDE.md`, `docs/GEMINI.md`, `AGENTS.md` | Reviewed (workspace rules + canonical Gemini path). |
| Query RAG for cleanup lessons | **Not verified in this session.** No live RAG/MCP memory gateway was read or written. Local `.claude/memory/` is gitignored. |
| Snapshot CI | `gh run list` / `gh run view` on `develop` (see below). |
| Snapshot core systems | Marine voice pack verified in prior session; store-verify skill merged (#1614); orphan Angst MMA MP3s removed (#1616). |

## Baseline metrics (tracked files)

**Command:** `bash scripts/shell/metrics_repo.sh`  
**Git SHA:** `2df334511930d80995fcd044cc19ca20bc95a413` (`develop` tip at audit start)

| Metric | Before cleanup PR | After cleanup PR (expected) |
|--------|---------------------|-----------------------------|
| **Tracked files** | 1550 | 1552 (+`uv.lock` churn, +report) |
| **Tracked lines** | 299,676 | ~300k (report + lockfile) |

**Extension mix (top):** 337 mp3, 246 md, 227 py, 110 kt, 53 swift (audio + native + automation).

## Hygiene gate

**Command:** `bash scripts/shell/hygiene-check.sh`

| Run | Errors | Warnings |
|-----|--------|----------|
| Before fixes | 3 (absolute paths in `.cursor/mcp.json`, `.mcp.json`, `docs/CLAUDE_CODE_API_KEY_HELPER.md`) | 0 |
| After fixes | **0** | **0** |

## Test coverage (Python `scripts/` only)

**Command:** `uv run pytest scripts/tests/ --cov=scripts --cov-report=term -q`  
**Date:** 2026-05-26

| Metric | Value |
|--------|-------|
| Tests passed | **702** |
| Aggregate `scripts/` coverage | **66%** |
| `verify_elevenlabs_voices.py` | **94%** (duplicate dict key removed in this PR) |

**Not measured here:** Android/iOS unit coverage, Codecov dashboard rollup, Maestro/device suites.

**Local dev parity fix:** `PyYAML` added to `pyproject.toml` (CI already installed `PyYAML==6.0.2`; local `uv run pytest` failed without it).

## CI health

| Branch | Run | Conclusion | URL |
|--------|-----|------------|-----|
| `develop` | `26460600654` | **success** | https://github.com/IgorGanapolsky/Random-Timer/actions/runs/26460600654 |

Workflow: `ci.yml` on merge commit `2df33451` (includes #1614 + #1616).

## Issues found and fixed (this PR)

| Category | Finding | Action |
|----------|---------|--------|
| Hygiene | Machine-specific absolute paths in MCP config + API key helper doc | Use `$HOME` in `.cursor/mcp.json`, `.mcp.json`, `docs/CLAUDE_CODE_API_KEY_HELPER.md` |
| Python | Duplicate `EXAVITQu4vr4xnSDxMaL` key in `SUPPORTED_VOICE_ENDPOINTS` | Remove duplicate entry |
| Tooling | `PyYAML` missing from `pyproject.toml` / `uv.lock` | Add dependency for local=test parity with CI |
| Voice (prior PR) | Orphan Angst MMA MP3s (not in catalog) | **Already merged** #1616 |
| CI (prior PR) | Public store verify 30m timeouts | **Already merged** #1614 + `.claude/skills/store-verify-ci.md` |

## Issues found — not fixed (phased backlog)

| Category | Finding | Recommended phase |
|----------|---------|-------------------|
| Coverage | `verify_release.py` ~61% | Add App Store Connect / Play CLI smoke tests |
| Coverage | `zernio_orchestrate.py` live-publish path | Mock `zernio_create_post` + env `ZERNIO_AUTO_PUBLISH=1` |
| Coverage | Native Android/iOS | JaCoCo / Xcode coverage gates (separate from `scripts/`) |
| RAG | External memory gateway | Verify gateway in-session before prune/write |
| Docs | 246 tracked `.md` files | Consolidate only with CEO-approved deletes |
| TODO/FIXME | Sparse in py/kt/swift | Triage per file (not mass-deleted) |
| Open PRs | #1612, #1598 | Hygiene merge or close |

## RAG cleanup summary

```
RAG entries read: 0 (gateway not verified)
RAG entries cleaned: 0
RAG lessons logged: 0 (this report is the durable artifact)
```

## Protected components (post-change verification)

| Component | Status |
|-----------|--------|
| CI pipeline (`develop`) | **success** at `26460600654` |
| Hygiene pre-push gate | **pass** (0 errors) |
| Python tests | **702 passed**, 66% `scripts/` coverage |
| Marine voice pack | Unchanged (prior evidence; not re-audited in this PR) |
| ElevenLabs voice contract | Clyde allowlist; Angst blocked in generator + verifier |

## Deliverable summary

```
Files scanned: 1550 (git tracked enumeration)
Issues found: 6 (hygiene paths, PyYAML parity, duplicate dict key, + backlog table)
Issues fixed in PR: 4
Files deleted: 0 (deletions in #1616 already on develop)
Lines removed: ~1 (duplicate dict line)
RAG entries cleaned: 0 (not verified)
```

## Phase 3 — automation coverage (2026-05-26, PR follow-up)

**Command:** `uv run pytest scripts/tests/ --cov=scripts --cov-report=term -q`

| Metric | Baseline (#1617) | After Phase 3 |
|--------|------------------|---------------|
| Tests passed | 702 | **712** |
| Aggregate `scripts/` coverage | 66% | **66%** (unchanged aggregate; targeted modules raised) |
| `validate_release_branch.py` | ~56% | **93%** |
| `verify_public_store_versions.py` | ~66% | **68%** (`poll_until_public` fail-fast path) |
| `zernio_orchestrate.py` | ~57% | **65%** (`cmd_sync_latest` dry-run + routing) |
| `upload_store_listing_anchor.py` | ~50% | CLI covered via `test_upload_store_listing_anchor_main.py` |

**Still not claimed:** native Android/iOS 100% coverage, mass doc consolidation (246 `.md` files), RAG gateway prune (gateway **not verified**), `verify_release.py` ~61%, full `zernio_orchestrate` live-publish path.

## Accurate completion statement

**Technical debt audit baseline complete for 2026-05-26. Phase 3 raised coverage on release-branch validation, public-store polling, Zernio sync dry-run, and Anchor upload CLI. Core systems verified operational on `develop` CI. Hygiene gate passing. Python `scripts/` coverage remains ~66% (712 tests). Literal “all debt” (native coverage, doc purge, RAG) is phased work — not claimed.**
