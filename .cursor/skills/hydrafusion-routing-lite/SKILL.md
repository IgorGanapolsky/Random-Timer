---
name: hydrafusion-routing-lite
description: Route agent work Single/Cascade/Critique with cost accounting (see docs/HYDRAFUSION_ROUTING.md).
---

# Skill: hydrafusion-routing-lite

Follow `docs/HYDRAFUSION_ROUTING.md` and `docs/HYDRAFUSION_ORCHESTRATION.md`.

```bash
python3 scripts/hydrafusion_routing_gate.py --json
python3 scripts/hydrafusion_route.py --task "…" --risk medium --files 8
```

Patterns:
- **Single** — one capable model (Quick) when enough
- **Cascade** — cheap draft → quality gate → escalate to Deep only on miss
- **Critique** — draft → tool-less critic (other family) → one revision → fail-safe apply

Never subscribe to HydraFusion SaaS under the hard monthly cap. Pair with agent-model-matching.
