---
name: compound-lite
description: >
  Capture Compound Engineering learnings into docs/solutions/ after non-trivial
  work. Use when finishing a PR, repeating a correction, or when the user shares
  Superpowers vs GSD vs Compound Engineering. Do not install the full EveryInc
  plugin by default.
---

# Compound Engineering lite

Article: https://theaiengineer.substack.com/p/superpowers-vs-gsd-vs-compound-engineering

Compound Engineering sits **on top of** Superpowers or OpenGSD. It does not replace their checkpoints. The durable idea is the fourth step: write what you learned so the next agent reads it.

## When to use

- After merging (or finishing) non-trivial work
- When the same correction appears twice
- When the CEO pastes Compound Engineering / Every CE references

## Steps

1. Copy `templates/compound/SOLUTION.md` → `docs/solutions/<slug>.md`
2. Fill Problem, What worked, Prevention, Evidence (no placeholders)
3. Prefer Prevention as a gate, skill, or AGENTS.md / CLAUDE.md bullet
4. Verify: `python3 scripts/compound_gate.py --json --slug <slug>` → `ready=true`
5. Commit the solution note with the fix PR when possible

## Do not

- Install the full 33-skill plugin unless CEO explicitly asks
- Run parallel reviewer farms on every commit (token burn)
- Claim “compounded” without a gate-green `docs/solutions/` file
- Confuse this with PlayerZero hawk metrics (`docs/AGENT_COMPOUNDING_ROI.md`)
