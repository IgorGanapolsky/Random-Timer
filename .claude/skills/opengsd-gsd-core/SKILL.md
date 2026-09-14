---
name: opengsd-gsd-core
description: Run OpenGSD Discuss→Plan→Execute→Verify→Ship for Random Timer using .planning SSOT and gsd_phase_gate.
---

# OpenGSD / gsd-core

Upstream: https://github.com/open-gsd/gsd-core

## Before coding a multi-step feature

1. Read `.planning/STATE.md` and `.planning/ROADMAP.md`
2. Install if needed: `./scripts/install_opengsd_cursor.sh`
3. Use Cursor skills: `gsd-discuss-phase` → `gsd-plan-phase` → `gsd-execute-phase`
4. Write `VERIFICATION.md` with evidence (commands, paths, CI links)
5. Run `python3 scripts/gsd_phase_gate.py --json` — refuse "done" until `ship_ready`
6. Ship PR; update STATE; satisfy artifact GSD (merge SHA / CI / `marketing/data`)

## Output quality rules (from OpenGSD)

- Heavy research/plan/execute in **fresh** subagents (Task tool / worktrees)
- Keep orchestrator context lean
- Prefer smaller phases over mega-phases
- Never skip Verify

## Related

- `.claude/GSD.md`
- `docs/GSD_OPENGSD.md`
- `scripts/gsd_phase_gate.py`
