# Technical debt audit — 2026-09-14 (Phases 1–2)

## Scope honesty

This is **not** a completed line-by-line pass of every file. The repo has ~1614 tracked files (~50k Python / ~18k Kotlin / ~12k Swift lines). A true full audit + 100% coverage is multi-sprint.

## Baseline → Phase 2 (evidence)

| Metric | Before | After Phase 2 |
|--------|------:|------:|
| Tracked files | 1614 | 1614+ |
| Python `scripts` coverage | **67%** | **70%** |
| Python tests passed | 796 (earlier sample) / 1561 full | **1561** |
| CI `--cov-fail-under` | 66 | **68** |
| Hygiene check | PASS | PASS |

Commands:

```bash
bash scripts/shell/hygiene-check.sh
python -m pytest scripts/tests/ -q --cov=scripts --cov-report=term --cov-fail-under=68
```

## Protected systems snapshot

| System | Status |
|--------|--------|
| ROSE-lite | Session cells empty / **not verified** |
| ThumbGate RAG | Prior cleanup lessons noise-only; Phase 1 lesson logged |
| Orchestration | Unchanged |
| CI Python gate | Floor raised 66→68; local 70% |

## Phase 1 fixes (merged #1926)

1. Ignore `.tmp/` and `.venv-audit/`
2. Rename `.claude/GEMINI.md` → `.claude/pr-hygiene-session.md`
3. Hygiene contract for `.tmp/` ignore

## Phase 2 fixes

New unit tests (24) covering previously untested large scripts:

- `scripts/tests/test_aso_keyword_rotation.py`
- `scripts/tests/test_posthog_dashboard.py`
- `scripts/tests/test_backlinks_referral_generators.py`
- `scripts/tests/test_generate_monthly_audio_pack.py`

## Files deleted

None (Wave 3 archives stale docs with SSOT review).

## Gaps remaining

- `scripts/complete_all_declarations.py` — Playwright UI automation; needs integration harness, not unit mocks
- Android/iOS coverage artifact read-back (Wave 4)
- Dead-code deletes only with import-graph evidence (Wave 5)
- Monorepo 100% coverage — **not claimed**

## Completion status

**Phases 1–2 complete. Full monorepo debt audit NOT complete. Scripts coverage 70% (CI floor 68%).**
