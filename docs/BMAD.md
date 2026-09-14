# BMAD Method (lite) on Random Timer

Source article: https://sam-solutions.com/blog/spec-driven-development-with-bmad-method/  
Upstream OSS: `bmad-method` (MIT) — **not fully installed** (overlaps Spec Kit / Superpowers / OpenGSD).

## High-ROI adopted

1. **SPEC.md five-element contract** — Why, Capabilities (+ success conditions), Constraints, Non-goals, Success signal (`templates/bmad/SPEC.md`)
2. **Implementation readiness gate** — refuse coding until the contract is complete (`scripts/bmad_readiness_gate.py`)
3. **Proportional planning / Quick Flow** — small fixes skip Analysis→Planning→Solutioning; large work uses Spec Kit + OpenGSD (`bmad-lite` skill)
4. **Artifact handoffs** — decisions live in files, not chat memory (same as Spec Kit `specs/` + OpenGSD `.planning/`)

## Explicitly skipped

- Full `npx bmad-method install` (358-file agent framework; duplicates Spec Kit skills)
- Enterprise PRD/UX/architecture spine for every tiny fix (article warns against excessive planning)
- SaM Solutions commercial engagement

## Four phases → our stack

| BMAD phase | Random Timer mapping |
|------------|----------------------|
| Analysis | Superpowers `brainstorming` + PostHog DS-first |
| Planning | Spec Kit `/speckit-specify` + BMAD `SPEC.md` |
| Solutioning | Spec Kit `/speckit-plan` + `/speckit-tasks` + OpenGSD plan |
| Implementation | Superpowers TDD + Spec Kit implement/converge + gates |

## Quick Flow (default for small work)

1. Write `specs/<###-slug>/SPEC.md` from the template (or copy `templates/bmad/SPEC.md`)
2. `python3 scripts/bmad_readiness_gate.py --json --feature <###>` must be `ready=true`
3. Implement with TDD; verify with `verification-before-completion`

## Full Flow (multi-epic / high-risk)

Analysis → Spec Kit specify/plan/tasks → BMAD readiness → OpenGSD phase verify → ship with artifact GSD.

## Gate

```bash
python3 scripts/bmad_readiness_gate.py --json --feature 002
```

Fixture: `specs/002-bmad-lite-readiness/`
