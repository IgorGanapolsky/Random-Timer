# Agent Integrity (lite) — human is the standard agents are held to

Operating brief from [Terra / Ofek Haviv (CTech)](https://www.calcalistech.com/ctechnews/article/km507avs3):

> The researcher of the future isn't competing with agents on speed. Their value is in being the **standard the agents are held to**: the one making sure velocity doesn't come at the cost of integrity.

## Anti-pattern

**Velocity without integrity** — claiming “done” because it looks right, shipping fast without verified read-back, or declaring expert judgment fully captured in a finished playbook.

## Four pillars

| Pillar | Meaning here |
|--------|----------------|
| `human_standard` | Humans set the quality bar; agents take high-volume speed work |
| `velocity_with_rigor` | Speed is allowed only with evidence (API/store/CI read-back) |
| `research_product_loop` | Bidirectional “muscle memory”: research→product and product→research |
| `critical_judgment_human` | Humans hold the line at material risk (e.g. production-signoff) |

## Research ↔ product feedback loop

1. Formalize tacit expert instincts into agent-executable workflows (completion stages, gates).
2. Run agents; observe where they succeed, get stuck, or diverge from expert judgment.
3. Those gaps become the next research questions — never declare absolute capture.

## Random Timer reference

Fixture: `marketing/data/integrity/native_release_integrity.json`

- Human standard: CTO evidence read-back before “done”
- Rigor: CI + Publisher/ASC API verify
- Critical judgment: `production-signoff`
- Loop: CDN lag vs API truth → new verification research

## Fitness

```bash
python3 scripts/agent_integrity_gate.py --json
```

## Explicitly rejected

- Competing with agents on raw speed as the differentiator
- “Looks right” as proof
- Absolute / finished expert-judgment playbooks
- One-way research dump with no product feedback
