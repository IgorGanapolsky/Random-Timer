# Pre-Recursive Agent Ops

Practical filter from RSI / recursive-self-improvement discourse: sell and run the **pre-recursive** infrastructure businesses need today—evaluation, verification, and human-in-the-loop compound loops—not foundation-model labs.

Source framing: Dwarkesh episode on how close AI is to recursive self-improvement  
https://music.youtube.com/watch?v=PrSf7IOYu-I

Hard fleet cap remains **$20 USD/month**.

## Claim card (required)

For every notable assertion, capture all four:

1. **Claim** — e.g. agents can speed up software R&D  
2. **Dependency** — coding reliability, evals, permissions, human review, …  
3. **12-month wedge** — narrow workflow to automate now  
4. **Proof metric** — hours saved, tickets closed, error reduction, …

Incomplete cards fail closed.

## CLI

```bash
python3 scripts/agent_pre_recursive_ops.py \
  --claim "evals make agent engineering deployable" \
  --dependency "acceptance_criteria + evidence + human_review" \
  --wedge "CI triage + store ops with proof metrics" \
  --proof-metric hours_saved_per_week \
  --layer application \
  --bottleneck evaluation \
  --hours-saved 6 --effort 2 --speedup 3 \
  --acceptance-met \
  --evidence marketing/data/agent_pre_recursive_ops.json \
  --month-to-date-usd 2 \
  --json
```

## Library API

| Function | Purpose |
|----------|---------|
| `validate_claim_card` | Require claim/dependency/wedge/proof |
| `rank_wedges` | Prefer application-layer + eval bottlenecks by hours/effort |
| `approval_gate` | Evidence auto-allow for reversible work; block irreversible without human approval |
| `compound_loop_policy` | Allow only 2–5x speedup with human-in-the-loop |
| `select_infra_posture` | Application-layer automation; block foundation training under cap |
| `plan_ops_wedge` | Combined fail-closed plan report |

## Immediate wedges (Random Timer fleet)

1. CI / PR triage with acceptance + evidence (existing eval + cost audit)  
2. Store / Play ops with read-back proof before “done”  
3. Paywall / PostHog research briefs with cited queries  
4. Support / sales-engineering drafts with review gate  

Related: `scripts/agent_eval_governance.py`, `scripts/agent_cost_reliability_audit.py`.

GSD artifact: `marketing/data/agent_pre_recursive_ops.json`.
