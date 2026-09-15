# Workflow Economics (lite) — escape AI pilot purgatory

Operating brief: turn isolated AI demos into measurable, repeatable operational systems. Highest ROI is usually **workflow selection + deep integration + metrics**, not a newer model.

## Anti-pattern

Broad “enterprise chatbot” with no owner, no constrained success criterion, and no system of record write path → **pilot purgatory**.

## Completion loop (design for completion)

```text
Trigger → Context retrieval → Decision → Action → Verification → Audit trail
```

Copilot summaries alone do not remove queue time. Completed work does.

## Operating model checklist

| Improvement | Why it drives ROI |
|-------------|-------------------|
| One accountable process owner | Stops orphan experiments |
| Baseline before launch | Proves hours/cycle-time/quality movement |
| Integrate with systems of record | Output becomes operational |
| Human approval only at material risk | Keeps automation savings |
| Eval from real work | Reliability users feel |
| Instrument every run | Failures and cost/task visible |
| Reusable agent components | Lowers next-workflow cost |

## Weekly economic metrics

Prefer: `automation_rate`, `cycle_time_hours`, `cost_per_completed_task`, `quality_rate`, `capacity_hours_released`, `conversion_uplift`, `wqtu`, `paywall_attempt_success_rate`.

Reject as ROI: interest, demo likes, raw usage, token counts.

## Random Timer reference workflow

**`native_release_completion`** (fixture: `marketing/data/workflows/native_release_completion.json`)

- Owner: CTO
- Metric: `cycle_time_hours` (trigger → verified store outcome)
- SoR: GitHub Actions + store consoles/APIs
- Approvals: production-signoff (material risk); internal envs under standing grant
- Audit: Actions run URL + GitHub Release tag

Next expansion candidate (same bar): paywall attempt→success ops with PostHog baseline — only after weekly metric movement is logged.

## Fitness

```bash
python3 scripts/workflow_economics_gate.py --json
python3 scripts/workflow_economics_gate.py --json \
  --charter-json marketing/data/workflows/native_release_completion.json
```

## 30-day play (this repo)

1. One workflow, one owner, one economic metric, one user group.
2. Map exceptions + data sources.
3. Ship connected to real tools (not a standalone chat UI).
4. Shadow/draft first when risk is high.
5. Automate low-risk actions; log everything.
6. Expand only after the weekly metric moves.

## Explicitly rejected

- Model-shopping as the first lever
- Pilots without baselines
- Claiming ROI from demo interest
