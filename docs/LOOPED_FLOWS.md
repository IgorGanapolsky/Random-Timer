# Looped Flows (lite) — more reasoning without more parameters

Operating brief from [elvis @omarsar0](https://x.com/omarsar0/status/2098807354343260366) on [Thinking with Looped Flows](https://arxiv.org/abs/2609.11801) (Suleymanzade et al.):

> Looped models are great because you get **more reasoning out of a model without adding parameters**.

Paper: looped models recurrently update a hidden state at inference. Training usually backpropagates through only the last one/few updates, so **early updates never learn to set up later ones**. Looped flows train the recurrence with **local denoising objectives** (decreasing noise + shared noise ties each update to the next). At inference, a **finer time grid** spends more compute; different starting noise can yield different valid answers on multi-solution tasks. Reported wins over prior looped models on five of six reasoning benchmarks (e.g. 58.8% ARC-AGI-1, 12.2% ARC-AGI-2).

## Anti-pattern

**Last-step-only credit assignment** — a single giant prompt / one final check, with no intermediate local objectives that carry state forward. When gradients (or agent credit) only hit the last step, early work never “learns” to set up the later fix.

## Health signals (required)

| Signal | Meaning here |
|--------|----------------|
| `reason_by_recurrence_not_params` | Prefer more verify/refine loops over bigger model / more tools |
| `early_steps_set_up_later` | Design step N so step N+1 inherits useful state |
| `local_objectives_chain` | Each loop has a local check tied to the next (shared context) |
| `adaptive_compute_grid` | Harder failures get a finer grid (more loops), not one deeper hopium |

## Random Timer discipline

Operational analogy only — we do **not** train neural nets or buy new inference SaaS.

- Diagnosis → local fix → re-verify → next local objective (shared evidence across loops)
- CI / Sonar / gate re-runs are the “finer time grid”
- Fixture: `marketing/data/code_health/looped_flows_discipline.json`

## Fitness

```bash
python3 scripts/looped_flows_gate.py --json
```

## Explicitly rejected

- “Just use a larger model” as the first move on a hard bug (escalation OK after ≥2 failed recurrent loops)
- Single-shot agent turns with no intermediate verify loops
- Optimizing only the final check while early steps stay unvalidated
- Untied parallel loops that do not share context / noise
