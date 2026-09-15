# DAIR Academy Daily (lite) — scrape → rank → implement steals

Operating brief from [DAIR.AI Academy](https://academy.dair.ai/dashboard) (SSO: iganapolsky) + public [AI Papers of the Week](https://academy.dair.ai/papers).

Daily loop: scrape the free papers feed (and optional dashboard extras), rank by Random Timer ROI (WQTU / paywall / agent-stack durability), queue implementable steals, then TDD + PR.

## Anti-patterns

- Skipping paid Academy unlocks (free papers + free dashboard session are enough)
- Auto-generating bloated `AGENTS.md` / `CLAUDE.md` (ETH AGENTbench: LLM context files hurt; human lean files help)

## Health signals

| Signal | Meaning |
|--------|---------|
| `daily_scrape_papers` | Cron scrapes `academy.dair.ai/papers` |
| `rank_by_wqtu_profit_roi` | Score papers for agent/revenue/store impact |
| `queue_implementable_steals` | Emit implement queue with layer hints |
| `human_agents_md_not_llm_bloat` | Keep repo contracts human-authored and lean |

## Fitness

```bash
python3 scripts/dair_academy_daily.py --json
python3 scripts/dair_academy_gate.py --json
```

Workflow: `.github/workflows/dair-academy-daily.yml` (daily cron + dispatch).

## Seed steals (2026-09-15 session)

1. **AGENTS.md evaluation** ([resource](https://academy.dair.ai/dashboard/resources/agents-md-evaluation) / [arxiv 2602.11988](https://arxiv.org/abs/2602.11988)): human context +4%, LLM-generated −2%, all +20% cost → keep human lean contracts.
2. **Procedural Graphs** (papers week Sep 7–13): explicit procedure graph for long-horizon agents → encode as lite discipline next to GSD/SSOT.
