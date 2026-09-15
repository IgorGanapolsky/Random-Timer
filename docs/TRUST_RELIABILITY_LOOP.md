# Trust Reliability Loop lite

Source thesis: [always-on consumer AI assistant economics](https://music.youtube.com/watch?v=Xa1jm2VWEHk).

Highest ROI is **not** more autonomous capability — it is **tighter scope**, **cheaper inference**, and a **measurable trust/reliability loop**. Episode constraints: long-running-agent behavior, evaluation, user trust, and difficult consumer unit economics under flat subscriptions.

## Anti-pattern

Ship a general-purpose always-on agent that continuously reasons, writes externally without confirmation, and optimizes “agent quality” instead of workflow precision → users mute alerts, margins die, trust collapses.

## Highest-ROI bets (binding)

| Priority | Improvement | Why it pays back |
|----------|-------------|------------------|
| 1 | Narrow to a few high-frequency, high-stakes workflows | Easy to validate; recurring value without open-ended agent risk |
| 2 | Eval-first operating system | Log candidates, actions, corrections, outcomes; precision/recall **by workflow** |
| 3 | Tiered inference pipeline | Rules → cheap classify → extract → premium only when needed |
| 4 | Recommend-first / read-only default + progressive autonomy | Provenance + approve/dismiss; grant write rights per action class |
| 5 | Explicit editable memory | “Why I remembered,” edit, forget, retention controls |
| 6 | Alert precision over coverage | Alert budget, batching, quiet hours; escalate only if time-sensitive |
| 7 | Cost per retained user/household | Cap background spend; dedupe; cache; reprocess on material change |

## Decision ladder (event-driven)

```text
Ingest change → Rules/metadata → Classify → Extract → Premium (rare) → User confirm
```

Never continuous always-on reasoning. Call a stronger model only when a material, user-relevant decision is required.

## Random Timer narrow workflows

| workflow_id | Job | Metric |
|-------------|-----|--------|
| `ops_daily_brief` | Daily ops digest (CI, store, paywall, North Star) | `actionable_alert_precision` |
| `paywall_failure_alert` | Attempt→success failure surfacing | `actionable_alert_precision` |
| `wqtu_north_star_alert` | WQTU / North Star drift | `weekly_retained_users` / `wqtu` |
| `release_conflict_alert` | Release/store conflict | `correction_rate` |
| `ci_precision_alert` | High-signal CI failures only | `actionable_alert_precision` |

Fixture: `marketing/data/workflows/ops_daily_brief.json` (mode=`recommend_first`).

## KPIs

- Weekly retained users / **WQTU**
- Actionable-alert precision (by workflow)
- Correction rate
- Cost per retained user
- Progressive-autonomy grant rate

Reject as ROI: open-ended chat engagement, raw token volume, “feels helpful” summaries without precision.

## Explicitly deferred

- General-purpose “do anything” chat as the product
- Fully autonomous email/messaging/calendar/purchase writes
- Broad third-party integrations before retention is proven
- Multi-agent orchestration that does not move a measured workflow metric
- Long-lived unbounded context instead of compact, source-linked structured memory

## Fitness

```bash
python3 scripts/trust_reliability_loop_gate.py --json
python3 scripts/trust_reliability_loop_gate.py --json --claim-json '{"action":"recommend","workflow_id":"ops_daily_brief","eval_logged":true,"source_url":"https://example.test","mode":"recommend_first"}'
```

Pairs with: `docs/WORKFLOW_ECONOMICS.md`, `docs/HYDRAFUSION_ROUTING.md`, `docs/LLM_RESPONSE_CACHE.md`, `docs/AGENTZIP_MEMORY.md`.
