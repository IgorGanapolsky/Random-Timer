---
name: maintainability-gap-lite
description: >
  Counter AI copy-paste sprawl (GitClear: +25% output, +81% duplication).
  Prefer refactor/reuse; treat tests+refactor as the mission; reject LOC/10x ROI.
---

# Skill: maintainability-gap-lite

## Instructions

1. Do not claim ROI from LOC, PR count, or “10x” AI speed.
2. Before adding a twin helper/gate, search existing patterns and prefer refactor/extract.
3. Treat tests and refactoring as the work—not a boss-permission side quest.
4. Use AI as a forklift (large coordinated changes), not a racing car.
5. Run `python3 scripts/maintainability_gap_gate.py --json` before claiming discipline ready.

## Examples

```bash
python3 scripts/maintainability_gap_gate.py --json
PYTHONPATH=. python3 -m pytest scripts/tests/test_maintainability_gap_gate.py -q
```

## Performance Notes

- Pure Python; $0 SaaS (no GitClear subscription required for this lite gate).

## Troubleshooting

- `block_output_vanity_roi` → use economic metrics / verified outcomes
- `block_copy_without_reuse_search` → search + link existing helper first
- `block_side_quest_practices` → set tests/refactor to required
