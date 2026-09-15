---
name: spec-governance-lite
description: >
  InfoQ when-SDD-pays-off targeting: hard multi-constraint work gets staged
  approved baseline + attributable drift review; easy tasks use reason-first.
  Never claim specs raise bug recall; claim attribution. Human stays Accountable.
---

# Skill: spec-governance-lite

## Instructions

1. Classify the task (`easy` / `medium` / `hard`) via `scripts/spec_governance_gate.py --task ...`.
2. Hard work: Spec Kit artifacts + named invariants; staged baseline then fresh generate; drift findings cite clauses.
3. Easy work: reason-first; do not inflate ceremony.
4. Never claim the baseline raises recall; claim attributable, contract-anchored review.
5. Keep a human Accountable for reconciliation (model may be Responsible for generation).

## Examples

```bash
python3 scripts/spec_governance_gate.py --json --task "rename typo in README"
python3 scripts/spec_governance_gate.py --json --task "paywall gate with catalog load"
PYTHONPATH=. python3 -m pytest scripts/tests/test_spec_governance_gate.py -q
```

## Performance Notes

- Pure Python; $0 SaaS.

## Troubleshooting

- `block_false_recall_claim` → rewrite claim to attribution, not recall.
- `block_inline_spec_prompt` → approve `specs/<###>/` then generate in a new step.
- `block_unattributed_drift` → add `invariant:` / clause id per finding.
