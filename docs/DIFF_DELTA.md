# Diff Delta (lite) — durable AI ROI, not token vanity

Operating brief from [GitClear](https://www.gitclear.com/):

> See which AI tools are **actually earning their license** — score **Diff Delta** (lineage-aware durable change), not tokens or LOC.

GitClear attributes change to the model that wrote it, then scores **durable output** against rework, defects, and review time. Moves, renames, and reformatting keep lineage so rewrites stop inflating a model’s numbers. Token-to-durable-production **yield**: generated → accepted → committed → merged → day 7 / 30 / 90. Homepage research markers: ~**8×** duplicate blocks since AI assistants went mainstream; ~**9×** higher churn from AI power users who also ship **4–10×** more volume.

## Anti-pattern

**Token vanity AI ROI** — claiming a model “earned its seat” from tokens, LOC, or pre-merge volume while ignoring survival, rework, hotspot directories, and apples-to-oranges cohort math.

## Health signals (required)

| Signal | Meaning here |
|--------|----------------|
| `score_durable_diff_delta` | Prefer Diff Delta / surviving share / rework rate over tokens & LOC |
| `yield_to_production_not_tokens` | Pre-merge leakage is not ROI; count post-merge day_30/90 survival |
| `flag_ai_hotspot_dirs` | Watch folders where AI raises defect Δ / duplication Δ |
| `same_yardstick_human_llm` | Human vs LLM cohorts use the same Diff Delta measure |

## Random Timer proxies ($20/mo — no GitClear SaaS)

Do **not** buy GitClear under the operating budget cap. Local proxies:

- Sonar `new_duplicated_lines_density` (≤3% on PRs)
- Merge + post-merge CI survival (not “generated” drafts)
- Maintainability Gap lite (`docs/MAINTAINABILITY_GAP.md`) for copy-paste sprawl
- Fixture: `marketing/data/code_health/diff_delta_discipline.json`

## Fitness

```bash
python3 scripts/diff_delta_gate.py --json
```

## Explicitly rejected

- Tokens / LOC / “4× more code” as AI license ROI
- Counting generated/accepted/committed volume as durable yield
- Comparing AI vs human with different metrics
- Paying for GitClear (or similar) while the $20/mo hard cap is in force
