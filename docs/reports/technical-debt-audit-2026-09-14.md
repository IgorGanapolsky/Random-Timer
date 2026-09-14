# Technical debt audit — 2026-09-14 (Phase 1)

## Scope honesty

This is **not** a completed line-by-line pass of every file. The repo has ~1614 tracked files (~50k Python / ~18k Kotlin / ~12k Swift lines). A true full audit + 100% coverage is multi-sprint. Phase 1 = baseline + safe hygiene.

## Baseline (evidence)

| Metric | Value |
|--------|------:|
| Tracked files | 1614 |
| Text tracked files | 1148 |
| Python lines | 50235 |
| Kotlin lines | 17773 |
| Swift lines | 11648 |
| Markdown lines | 20863 |
| `scripts/tests` files | 126 |
| Python `scripts` coverage (local) | **67%** (796 passed) |
| CI `--cov-fail-under` | 66 |
| Hygiene check | PASS (0 errors) |

Commands:

```bash
bash scripts/shell/hygiene-check.sh
python -m pytest scripts/tests/ -q --cov=scripts --cov-report=term --cov-fail-under=0
```

## Protected systems snapshot

| System | Status |
|--------|--------|
| ROSE-lite | Session file present; `cells=[]` / memory match **not verified** |
| ThumbGate RAG lessons for cleanup | No useful prior cleanup lessons (noise only) |
| Orchestration | Unchanged this phase |
| CI Python gate | Local suite meets ≥66% |

## Phase 1 fixes

1. Ignore `.tmp/` and `.venv-audit/` (191 untracked `.tmp` files were not ignored — accidental-add risk).
2. Rename `.claude/GEMINI.md` → `.claude/pr-hygiene-session.md` (content was PR hygiene, not Gemini policy). Canonical Gemini remains `docs/GEMINI.md`.
3. Hygiene contract test requires `.tmp/` / `.venv-audit/` in `.gitignore`.

## Not deleted (yet)

Stale dated audits / gap analyses remain for history. Wave 3 may archive after CEO/SSOT review.

## Untested large scripts (Wave 2)

See `marketing/data/tech_debt_audit.json` → `issues_found_not_yet_fixed.untested_large_scripts_top`.

## Completion status

**Phase 1 complete. Full monorepo debt audit NOT complete. Core hygiene verified. Python scripts coverage 67% (CI floor 66%).**
