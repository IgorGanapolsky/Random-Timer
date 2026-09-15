---
name: agent-integrity-lite
description: >
  Hold agents to a human integrity standard: verified read-back, critical
  judgment points, bidirectional research↔product loop. Block velocity-without-
  integrity and absolute expert-capture claims (Terra / CTech).
---

# Skill: agent-integrity-lite

## Instructions

1. Do not compete with agents on speed; set the integrity standard they must meet.
2. Refuse “done” / “looks right” without verified read-back evidence.
3. Keep a bidirectional research↔product loop (muscle memory).
4. Place humans only at critical judgment points (material risk).
5. Never claim expert judgment is fully captured — keep finding missed instincts.
6. Run `python3 scripts/agent_integrity_gate.py --json` before claiming the layer ready.

## Examples

```bash
python3 scripts/agent_integrity_gate.py --json
PYTHONPATH=. python3 -m pytest scripts/tests/test_agent_integrity_gate.py -q
```

## Performance Notes

- Pure Python; $0 SaaS.

## Troubleshooting

- `block_velocity_without_integrity` → add verified_readback + remove “looks right”
- `block_absolute_expert_capture` → drop absolute-truth language
- `block_one_way_loop` → fill both research_to_product and product_to_research
