---
name: bmad-lite
description: Route work through BMAD-lite Quick or Full flow using SPEC.md five-element contract and scripts/bmad_readiness_gate.py before coding; bridges Spec Kit and OpenGSD.
---

# BMAD-lite

Article: https://sam-solutions.com/blog/spec-driven-development-with-bmad-method/

## When

Starting a feature or fix where the agent might invent product decisions.

## Route

- **Quick Flow** (small/clear): copy `templates/bmad/SPEC.md` → `specs/<###-slug>/SPEC.md`, fill five sections, run readiness gate, then TDD implement.
- **Full Flow** (high-risk/multi-epic): Superpowers brainstorm → Spec Kit specify/plan/tasks → BMAD readiness with `--require-spec-kit` → OpenGSD verify → ship.

## Gate

```bash
python3 scripts/bmad_readiness_gate.py --json --feature <###>
# Full: add --require-spec-kit
```

## Do not

- Install full `bmad-method` by default
- Skip Non-goals (agents invent scope)
- Claim ready without gate evidence
