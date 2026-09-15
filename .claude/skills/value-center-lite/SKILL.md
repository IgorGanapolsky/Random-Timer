---
name: value-center-lite
description: >
  Apply InfoQ Rohrer value-center / VSM five questions (agency + coherence).
  Use when planning work, shipping releases, or auditing agent autonomy claims.
  Fail closed on product-only slogans without WQTU/paywall value.
---

# Skill: value-center-lite

## Instructions

1. Answer the five VSM questions for the current task (value, coordinate, fit, out-there, who-we-are).
2. Prefer **agency + coherence** over "autonomous team" slogans.
3. Classify dependencies as essential vs accidental; drop accidental paid/plugin installs.
4. Run `python3 scripts/value_center_gate.py --json` before claiming the value-center layer is ready.
5. Cite live PostHog WQTU / paywall evidence when the decision is product prioritization.

## Examples

```bash
python3 scripts/value_center_gate.py --json
PYTHONPATH=. python3 -m pytest scripts/tests/test_value_center_gate.py -q
```

## Performance Notes

- Pure Python fitness; zero new SaaS spend.

## Troubleshooting

- `block_product_not_value` → rewrite the charter value to include WQTU / paywall / $100/day.
- `block_autonomy_slogan` → set `mode` to `agency_and_coherence`.
