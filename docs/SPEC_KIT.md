# Spec Kit (github/spec-kit) on Random Timer

Upstream: https://github.com/github/spec-kit (`specify-cli` **1.0.6**)

## Why (high-ROI only)

Spec Kit fixes agent failure modes we already hit:

1. **Code before intent** → forced Spec → Plan → Tasks → Implement → Converge
2. **Vague bug patches** → bug extension: assess → fix → test under `.specify/bugs/`
3. **No project principles in-session** → `.specify/memory/constitution.md`
4. **Agent lock-in** → Cursor (`cursor-agent`) + Claude skills installed side-by-side

Skipped (low ROI here): idea `assess` extension (we already use PostHog DS-first),
Hermes empty integration stub, paid catalogs.

## Install

```bash
./scripts/install_speckit.sh
# pins specify-cli==1.0.6 via uv tool; inits cursor-agent + claude + bug if needed
```

Requires [uv](https://docs.astral.sh/uv/). No new paid SaaS.

## Daily loop

1. Read `.specify/memory/constitution.md`
2. Skills: `speckit-specify` → `speckit-plan` → `speckit-tasks` → `speckit-implement` → `speckit-converge`
3. Optional quality: `speckit-clarify`, `speckit-analyze`, `speckit-checklist`
4. Bugs: `speckit-bug-assess` → `speckit-bug-fix` → `speckit-bug-test`
5. `python3 scripts/speckit_gate.py --json` must be `implement_ready` before claiming feature work done; use `--require-converge` for full Converge claims

Artifacts live under `specs/<###-slug>/` (`spec.md`, `plan.md`, `tasks.md`, optional `CONVERGENCE.md`).

## Bridge with OpenGSD

| Layer | Path | Gate |
|-------|------|------|
| Phase / roadmap | `.planning/` | `scripts/gsd_phase_gate.py` |
| Feature SDD | `specs/` + `.specify/` | `scripts/speckit_gate.py` |
| Ship evidence | PR / CI / `marketing/data` | Artifact GSD (unchanged) |

See `.claude/GSD.md` and `docs/GSD_OPENGSD.md`.

## Verification fixture

`specs/001-speckit-harness-gate/` is the first tracked feature used to prove the gate.
Do not delete without replacing another green fixture.
