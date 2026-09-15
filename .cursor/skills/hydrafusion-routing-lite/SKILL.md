---
name: hydrafusion-routing-lite
description: Route agent work Single/Cascade/Critique with cost accounting (see docs/HYDRAFUSION_ROUTING.md).
---

# Skill: hydrafusion-routing-lite

Follow `docs/HYDRAFUSION_ROUTING.md` and `docs/HYDRAFUSION_ORCHESTRATION.md`.

```bash
python3 scripts/hydrafusion_routing_gate.py --json
python3 scripts/hydrafusion_route.py --task "…" --risk medium --files 8
python3 scripts/hydrafusion_route.py --simulate-cost '{"pattern":"cascade","draft_cost":1,"frontier_cost":10,"pass_rate":0.75}'
```

Patterns:
- **Single** — one capable model (Quick) when enough
- **Cascade** — cheap draft → quality gate → escalate to Deep only on miss (`run_cascade` / `estimate_cascade_cost`)
- **Critique** — draft → tool-less critic (other family) → one revision → fail-safe apply

Never subscribe to HydraFusion SaaS under the hard monthly cap. Pair with agent-model-matching. Do not claim TerminalBench measured savings — use local `estimate_cascade_cost` labeled proxies.
