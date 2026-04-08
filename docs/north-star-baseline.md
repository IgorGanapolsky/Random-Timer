# North Star baseline (internal)

Product-value metric: **WQTU** = distinct users with **≥3** `timer_completed` events in the trailing 7 days.

Canonical business rules, budget cap, and guardrails live in **`CLAUDE.md`** and **`AGENTS.md`**. This file only holds a **historical snapshot** for context (figures age out; verify in PostHog before decisions).

## Snapshot (2026-02-24 UTC)

- WQTU: `0`
- `timer_completed` (7d): `3` events, `2` users
- `open_to_completed_rate` (30d): `24.24%` (`32/132`)
- Paid-attributed users (30d): `0`
- Downloads (30d): iOS `9`, Android `0`

## Targets (from internal planning)

- Checkpoint (2026-03-31): WQTU ≥ 8  
- Quarter (2026-06-30): WQTU ≥ 25  

Replace this snapshot when you publish a new baseline with evidence.
