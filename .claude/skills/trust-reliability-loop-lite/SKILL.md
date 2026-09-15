---
name: trust-reliability-loop-lite
description: Scope, eval-first, tiered inference, recommend-first trust loop (see docs/TRUST_RELIABILITY_LOOP.md).
---

# Skill: trust-reliability-loop-lite

Follow `docs/TRUST_RELIABILITY_LOOP.md`. Source: https://music.youtube.com/watch?v=Xa1jm2VWEHk

```bash
python3 scripts/trust_reliability_loop_gate.py --json
```

Rules:
1. **Narrow workflows only** — `ops_daily_brief`, paywall/WQTU/release/CI alerts.
2. **Eval-first** — log every candidate, action, correction, outcome; optimize precision by workflow.
3. **Tiered inference** — rules → classify → extract → premium → confirm.
4. **Recommend-first** — no unconfirmed external writes; progressive autonomy per action class.
5. **Alert budget** — precision over coverage; provenance (`source_url`) everywhere.
6. **Cost per retained** — never claim unit economics from tokens alone.

Defer do-anything chat, continuous always-on reasoning, and unbounded context windows.
