# HydraFusion Routing (lite) — multi-model Single / Cascade / Critique

Operating brief from [InfoQ — GitHub Copilot's Project HydraFusion](https://www.infoq.com/news/2026/09/github-hydrafusion/) (Olimpiu Pop, 2026-09-13):

> Treat workflow execution as an **optimisation challenge**: dynamically build execution plans across models instead of pinning one static frontier model. Route with **Single**, **Cascade**, or **Critique**; keep **complete cost accounting**, **bounded execution**, **isolated review**, **fail-safe apply**, and **validated routing**.

HydraFusion research preview (Copilot CLI `/experimental`) reported matching Opus-class quality while cutting estimated cost ~65–67% on TerminalBench / CheckpointBench. We **steal the routing discipline**, not the paid Copilot experimental product.

## Patterns (required vocabulary)

| Pattern | When | Behaviour |
|---------|------|-----------|
| **Single** | Task is within one capable model's reach | One model runs end-to-end (latency-first) |
| **Cascade** | Cheap draft may pass a quality gate | Efficient model drafts → gate → escalate only on miss |
| **Critique** | High-stakes / multi-step correctness | Draft model → **tool-less** critic from another family → one structured revision |

## Operating principles (health signals)

| Signal | Meaning here |
|--------|----------------|
| `complete_cost_accounting` | Count tokens/cost for every leg: draft, critique, revision, escalate, retry, fallback |
| `bounded_execution` | Hard timeouts + cancellation; no unbounded agent loops |
| `isolated_critique` | Critic is read-only / tool-less (Rubber Duck); never mutates repo |
| `fail_safe_apply` | Reject patches if validation fails or execution cancelled |
| `validated_routing` | Pre-check model availability / bindings before spend |

## Random Timer proxies (hard monthly cap — no HydraFusion subscription)

Do **not** buy Copilot HydraFusion / paid experimental multi-model SaaS for this layer. Local proxies:

- **Planner CLI:** `python3 scripts/hydrafusion_route.py --task "…" --risk medium --files 8`
- **Presence + claim gate:** `scripts/hydrafusion_routing_gate.py` (this layer)
- **Operator brief:** `docs/HYDRAFUSION_ORCHESTRATION.md` (GitHub Blog primary; InfoQ digest)
- Pair with Agent-Model Matching (`.claude/rules/agent-model-matching.md`): Quick draft → Deep escalate; Visual/Opus-class critique without tools
- Pair with LLM Response Cache (skip unchanged calls) and Workflow Economics (completion loop)
- Fixture: `marketing/data/code_health/hydrafusion_routing_discipline.json`

Default routing for this repo (also emitted by `hydrafusion_route.py`):

1. **Single** — search, scaffolding, trivial edits (Quick / Flash / Haiku class)
2. **Cascade** — feature work: Quick draft → tests/lint gate → Deep only if gate fails
3. **Critique** — release, store metadata, security-sensitive, or merge-critical diffs: draft → isolated critic → one revision → fail-safe apply

## Anti-pattern

**Always-Opus / always-frontier** — paying frontier rates for every leg with no cascade gate, no critic isolation, no per-leg accounting, and no validated routing.

## Fitness

```bash
python3 scripts/hydrafusion_routing_gate.py --json
python3 scripts/hydrafusion_route.py --task "Implement paywall fix" --risk medium --files 8
python3 scripts/hydrafusion_route.py --simulate-cost '{"pattern":"cascade","draft_cost":1,"frontier_cost":10,"gate_cost":0.2,"pass_rate":0.75}'
python3 scripts/hydrafusion_route.py --run-cascade '{"draft_cost":1,"escalate_cost":10,"gate_cost":0.2,"gate_signals":{"tests_passed":true,"evidence_present":true,"secrets_leaked":false,"patch_validated":true}}'
```

`estimate_cascade_cost` is the local savings proxy (not TerminalBench). Default Cascade at 75% gate pass rate yields ~63% expected cost cut vs always-frontier — above the InfoQ ~60% proxy floor. Fixture: `marketing/data/code_health/hydrafusion_cascade_benchmark.json` (label=`infoq_reported_proxy_not_repo_measured`).

## Explicitly rejected

- Subscribing to HydraFusion / Copilot experimental as a hard dependency under the $20/mo cap
- Letting a critic model execute tools or apply patches
- Applying unvalidated or cancelled workflow patches
- Claiming cost savings without complete leg accounting
- Unbounded agent loops without timeout/cancel handles
