# Value Center (lite) — agency + coherence

Source: [Beyond Autonomous Teams in Software Product Development (InfoQ, 2026-09-10)](https://www.infoq.com/news/2026/09/autonomous-software-teams/) — Simon Rohrer / Viable Systems Model via Ben Linders.

## Steal the method (not a reorg)

Autonomous teams are an article of faith. Rohrer’s shift for Random Timer:

| From | To |
|------|----|
| Products / feature teams | **Value centers** |
| Autonomy slogans | **Agency + coherence** |
| Flat “autonomous product teams” | **Nested + networked** agents (PR/gates, not hierarchy hops) |

A system’s purpose is **what it does**. Ours is measured, not wished:

- Business: **$100/day after-tax** from app sales (budget hard cap **$20/mo** external).
- Product NSM: **WQTU** (users with ≥3 `timer_completed` in trailing 7d).

## Who are we?

The **Random Timer value center**: CEO directs; CTO + specialist agents deliver value end-to-end (build, release, store, telemetry). Networking is PRs, commit statuses, and fitness gates — you do not need to traverse a human hierarchy to ship.

## Five VSM questions (every level)

Answer these before claiming “we’re autonomous and done”:

1. **What value am I delivering?** — Tie the change to WQTU, paywall attempt→success, or store reach that feeds those — not vanity installs alone.
2. **How do we coordinate?** — Backlog/PR plan, SHA-bound `internal-signoff/*`, production-signoff, CI required checks.
3. **How do we fit together?** — Conceptual integrity: does this strengthen the training/timer loop and monetization path, or is it accidental complexity?
4. **What's out there for us?** — App Review lag, Play CDN lag, spend cap, PostHog project wiring, agent SHA drift.
5. **Who are we?** — This value center’s responsibility boundary (CTO execution; CEO strategy).

## Essential vs accidental dependencies

| Class | Examples | Action |
|-------|----------|--------|
| **Essential** | Play Billing catalog, App Store Connect, PostHog WQTU, signing/OIDC, store listing metadata | Keep; prove with read-back |
| **Accidental** | Full BMAD Method install, billed Copilot review SaaS, paid model routers, “plugin farms” | Prefer lite gates / existing CI |

## Fitness (coherence without approval theater)

```bash
python3 scripts/value_center_gate.py --json
```

`ready=true` means docs + skill + gate script are present and the charter doc answers the five questions with a north-star marker.

Optional charter evaluation:

```bash
python3 scripts/value_center_gate.py --json --charter-json path/to/charter.json
```

## Explicitly rejected

- “We’re an autonomous team” with no WQTU/paywall answer.
- Pure autonomy without coherence (no gates, no SHA signoffs, no evidence).
- Buying webinars/SaaS to simulate governance.

## Adoption

- Skill: `value-center-lite` (`.cursor/skills` + `.claude/skills`)
- Gate: `scripts/value_center_gate.py`
- Artifact: `marketing/data/value_center_adoption.json`
