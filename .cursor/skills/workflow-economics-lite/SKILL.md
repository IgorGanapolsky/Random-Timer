---
name: workflow-economics-lite
description: >
  Escape AI pilot purgatory: require completion-loop workflows with one owner,
  baseline, economic metric, system-of-record integration, and audit trail.
  Block orphan chatbots and interest-as-ROI claims.
---

# Skill: workflow-economics-lite

## Instructions

1. Refuse orphan chatbot / demo pilots without owner + baseline + economic metric.
2. Design Trigger→Context→Decision→Action→Verification→Audit before building UI.
3. Prefer high-volume digital workflows already in SoR (release ops, funnel ops).
4. Human approval only at material risk; instrument every run.
5. Run `python3 scripts/workflow_economics_gate.py --json` before claiming a workflow is production-ready.

## Examples

```bash
python3 scripts/workflow_economics_gate.py --json
PYTHONPATH=. python3 -m pytest scripts/tests/test_workflow_economics_gate.py -q
```

## Performance Notes

- Pure Python; $0 SaaS.

## Troubleshooting

- `block_orphan_pilot` → add owner, baseline value, economic metric, SoR.
- `block_incomplete_completion_loop` → fill all six stages.
- `block_interest_not_roi` → replace usage/demo with cycle time / automation rate / WQTU.
