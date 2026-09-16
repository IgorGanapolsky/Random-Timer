# AI Operating Model lite

Source: [YouTube Music / podcast thesis](https://music.youtube.com/watch?v=c-u8E15Lj8s) — treat AI adoption as an **operating-model change**, not a tool rollout.

Highest ROI under the **$20/mo hard cap**: process redesign, manager-led habits, enablement, and measurable behavior — not more model licenses or seat count.

Pairs with `docs/WORKFLOW_ECONOMICS.md` (completion loop + economic metrics). This doc owns the **adoption playbook**.

## Anti-pattern

Buy another AI subscription → hope people “use it” → reward prompts/logins → no SOP rebuild → pilot never becomes the way work ships.

## Highest-ROI moves (binding)

| Improvement | Why it pays back |
|-------------|------------------|
| One expensive, repetitive workflow + clear owner | Concentrates learning; stops orphan experiments |
| Baseline before AI (time, cost, quality, throughput) | Proves movement; kills vanity ROI |
| Rebuild AI-native SOP from scratch | Human inputs, model outputs, mandatory checks, approvals, logs |
| Fund enablement before tool spend | Champion + templates + office hours beat another license |
| Weekly AI operating ritual | Metrics review, one working example, failures, one next improvement |
| Measure behavior and business output | Cycle time, conversion, rework, cost/deliverable, margin — not seat utilization |
| ROI with full total cost | Labor + integration + governance + training + review, not just API fees |

## Prioritization

```text
ROI = (Financial value − Total cost) / Total cost
```

Pursue first when: high volume, high labor cost, low error tolerance **after QA**, fast deploy, and a manager willing to enforce the new process.

## 30-day plan

1. **Week 1** — Select one workflow, appoint owner, capture baseline.
2. **Week 2** — Redesign SOP with AI checkpoints, templates, QA, fallback/escalation.
3. **Week 3** — Pilot with 3–10 real runs; collect failures and improvements.
4. **Week 4** — Quantify, standardize the winner, train next cohort, **then** expand.

## Random Timer reference pilot

**`intake_to_delivery`** — customer/internal request → clarified spec → plan → draft tasks → tests → status updates, with human approval at key handoffs.

Baseline fixture: `marketing/data/code_health/ai_operating_model_discipline.json`  
Owner: CTO (agents execute; CEO directs).

## Fitness

```bash
python3 scripts/ai_operating_model_gate.py --json
```

## Explicitly rejected

- Tool/license rollout without SOP rebuild
- Expanding seats before enablement
- Rewarding prompt counts or seat utilization as success
- Claiming ROI from API fees alone (omit labor/training/review)
- Expanding to the next cohort before the 30-day pilot is quantified
