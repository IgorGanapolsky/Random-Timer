# pstack (lite) on Random Timer

Upstream: https://github.com/cursor/plugins/tree/main/pstack (v0.15.2, MIT, Lauren Tan / poteto)

> If you want to go fast, go deep first. Write less, higher-quality code. Fearless parallelism only after agents can prove work.

## High-ROI adopted

1. **23 principles** as steerable skills under `.cursor/skills/principle-*` and `.claude/skills/principle-*`
2. **`poteto-mode`** — rigor entrypoint that routes into OpenGSD / Spec Kit / Superpowers / BMAD-lite / Compound
3. **`unslop`** — prose hygiene for agent/CEO-facing text
4. **Encode lessons in structure** → already pairs with Compound lite (`docs/solutions/`) and our gates
5. **Never block on the human** → aligns with CTO autonomy mandate
6. **Prove it works** → aligns with `docs/OPERATIONAL_RELIABILITY.md` and verification-before-completion

## Explicitly skipped (use `/add-plugin pstack` for full set)

- Full 40+ situational skills (arena, swarm, make-bot-ui, typescript-best-practices, overnight automations, …)
- Cursor marketplace model panel from `/setup-pstack` as a hard CI dependency
- Duplicating Superpowers TDD/worktree skills under new names

## Principle index (steer by name)

### Build less / rethink

- Laziness Protocol · Foundational Thinking · Redesign from First Principles · Attack the Premise
- Subtract Before You Add · Minimize Reader Load · Outcome-Oriented Execution · Experience First
- Exhaust the Design Space · Build the Lever

### Architecture

- Model the Domain · Boundary Discipline · Type System Discipline · Make Operations Idempotent
- Migrate Callers Then Delete Legacy APIs · Separate Before Serializing Shared State

### Verification

- Prove It Works · Fix Root Causes · Sequence Work into Verifiable Units · Test Behavior, Not Implementation

### Delegation / meta

- Guard the Context Window · Never Block on the Human · Encode Lessons in Structure

## Stack placement

| Layer | Tooling |
|-------|---------|
| Invariant contract | AGENTS.md / CLAUDE.md |
| Phase loop | OpenGSD |
| Feature SDD | Spec Kit + BMAD-lite |
| Process skills | Superpowers |
| Learning capture | Compound lite |
| **Rigor / principles** | **pstack lite (this doc)** |

## Gate

```bash
python3 scripts/pstack_gate.py --json
```

## Optional host plugin

In Cursor Agent chat: `/add-plugin pstack` then `/setup-pstack`. Repo-vendored principles still apply when the marketplace plugin is absent.

## Attribution

See `third_party/pstack/`.
