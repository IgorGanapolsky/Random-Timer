# Superpowers (obra/superpowers) on Random Timer

Upstream: https://github.com/obra/superpowers (**v6.3.0**)

## Why (high-ROI)

Superpowers forces process skills before coding:

1. **verification-before-completion** — evidence before done claims (pairs with Spec Kit / OpenGSD gates)
2. **systematic-debugging** — root-cause process before patch spam
3. **test-driven-development** — RED-GREEN-REFACTOR enforcement
4. **using-git-worktrees** / **finishing-a-development-branch** — matches repo worktree law
5. **subagent-driven-development** / **dispatching-parallel-agents** — Task tool discipline
6. **brainstorming** + **writing-plans** / **executing-plans** — design before code
7. Session bootstrap via `using-superpowers` (Cursor `sessionStart` hook)

Skipped: `writing-skills` (upstream meta), visual companion traffic (disabled).

## Install / refresh

```bash
./scripts/install_superpowers.sh
```

Clones `obra/superpowers@v6.3.0` into a temp dir and syncs skills; wires the session hook.
Env: `SUPERPOWERS_DISABLE_TELEMETRY=1` (set in the session hook).

## Gate

```bash
python3 scripts/superpowers_gate.py --json
```

`ready=true` when 13 required skills + hook wiring are present.

## Bridge

| Layer | Tooling |
|-------|---------|
| Process skills (how) | Superpowers |
| Feature SDD artifacts | Spec Kit (`docs/SPEC_KIT.md`) |
| Phase roadmap | OpenGSD (`docs/GSD_OPENGSD.md`) |
| Ship evidence | Artifact GSD (merge SHA / CI / marketing JSON) |

## BMAD-lite

Five-element SPEC + readiness: see `docs/BMAD.md` and `python3 scripts/bmad_readiness_gate.py --json`.

## Compound Engineering lite

Learning capture (`docs/solutions/`): see `docs/COMPOUND_ENGINEERING.md` and `python3 scripts/compound_gate.py --json`.
