---
name: poteto-mode
description: >
  pstack rigor mode for Random Timer. Use at task start for nontrivial work,
  /poteto-mode, or when quality matters more than LOC. Routes playbooks into
  OpenGSD / Spec Kit / Superpowers / BMAD-lite / Compound; cites principles that
  changed decisions.
disable-model-invocation: false
---

# Poteto mode (Random Timer)

Upstream: [cursor/plugins pstack](https://github.com/cursor/plugins/tree/main/pstack) v0.15.2 (Lauren Tan / poteto).  
Repo guide: `docs/PSTACK.md`. Stack SSOT: `docs/AGENT_CODING_STACK.md`.

Goal: **write less, higher-quality code**. Fearless parallelism only after each agent can prove work.

## Non-negotiables

1. Before nontrivial work, read the principle index in `docs/PSTACK.md` (or the matching `principle-*` SKILL.md).
2. In replies, **name each principle that shaped a decision** and the specific choice it changed. No name-dropping.
3. Prefer deletion and the smallest change (`laziness-protocol`, `subtract-before-you-add`).
4. Done means real-artifact proof (`prove-it-works`), not "it compiles."
5. Recurring corrections become gates/scripts (`encode-lessons-in-structure`) and `docs/solutions/` (Compound lite).
6. Do not ask the CEO to run commands (`never-block-on-the-human` + CTO mandate).

## Playbook → Random Timer routing

| Intent | Do this |
|--------|---------|
| Investigation / how does X work | Read-only evidence; cite paths. Superpowers systematic-debugging if defect-shaped. |
| Bug fix | Reproduce → root cause → fix → gate/script proof. Prefer `principle-fix-root-causes` + `prove-it-works`. |
| Feature / product work | BMAD `SPEC.md` readiness → Spec Kit plan/tasks if Full → Superpowers TDD → OpenGSD phase if multi-day. |
| Refactor | Subtract dead paths first; sequence verifiable units; worktrees. |
| Perf | Measure baseline first; improve against numbers. |
| Ship / land PRs | Existing autonomy: green required checks, squash-merge, evidence. Compound if lesson learned. |
| Overnight / babysit CI | Poll checks; fix flakes with evidence; no force-push to main. |
| Same correction twice | Write `docs/solutions/<slug>.md`; run `compound_gate.py`. |

## Model panel (optional)

Full pstack `/setup-pstack` can assign models by strength. On Random Timer, follow `.claude/rules/agent-model-matching.md` / `AGENTS.md` Agent-Model Matching. Do not hard-depend on Cursor marketplace model aliases in CI.

## Unslop

Agent-facing and CEO-facing prose follows `.claude/skills/unslop/SKILL.md` (vendored). Prefer short, evidence-first replies per `AGENTS.md`.

## Full plugin

Optional host install: `/add-plugin pstack` in Cursor. This repo vendors principles + this mode so agents outside the plugin marketplace still get the rigor layer.
