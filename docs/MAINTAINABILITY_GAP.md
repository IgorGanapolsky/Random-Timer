# Maintainability Gap (lite) — output ≠ value when duplication explodes

Operating brief from [The New Stack / Steve Fenton on GitClear](https://thenewstack.io/ai-coding-duplication-rose/):

> Your AI coding spend bought **25% more output**. **Duplication rose 81%**.

GitClear’s Maintainability Gap (623M changes, 2023–2026): heavy AI users gained ~25% vs their own prior velocity—not 10x. Block duplication rose from 40.3 to 73.0 per million changed lines (+81%). Moved code (refactor signature) fell from ~21% of changed lines (2022) to ~3.8% (2026). Before AI, developers chose refactoring over copy-and-paste about 2:1; now they are roughly five times likelier to copy and paste.

## Anti-pattern

**AI copy-paste sprawl** — counting LOC, PRs, or “10x” as ROI while skipping reuse search, tests, and refactoring (“side quest” thinking).

## Health signals (required)

| Signal | Meaning here |
|--------|----------------|
| `reject_loc_as_roi` | Lines / PR volume ≠ WQTU / cycle time / quality |
| `prefer_refactor_over_copy` | Extend existing gates/helpers before pasting twins |
| `tests_refactor_are_the_work` | TDD + refactor are the mission, not optional |
| `forklift_not_racecar` | Use AI for large safe lifts, not speed theater |

## Random Timer discipline

Fixture: `marketing/data/code_health/agent_layer_discipline.json`

When adding agent-stack layers: reuse the gate+skill+fixture+SSOT pattern; do not clone near-duplicate gates with renamed vanity metrics.

## Fitness

```bash
python3 scripts/maintainability_gap_gate.py --json
```

## Explicitly rejected

- 10x / LOC / PR-count as success
- “We’ll refactor later” / tests as a side quest
- Racing-car framing for AI coding ROI
- Silent twin helpers that drift into whack-a-mole bugs
