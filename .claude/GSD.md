# GSD — Get Shit Done (Random Timer + OpenGSD)

**Upstream framework:** [open-gsd/gsd-core](https://github.com/open-gsd/gsd-core) (`@opengsd/gsd-core@1.14.0`)  
**Install (Cursor, local, core profile):** `./scripts/install_opengsd_cursor.sh`

## Phase loop (OpenGSD)

```text
Discuss → Plan → Execute → Verify → Ship
```

| Step | Artifact | Skill / command |
|------|----------|-----------------|
| Discuss | `.planning/phases/<id>/CONTEXT.md` | `gsd-discuss-phase` |
| Plan | `PLAN*.md` (+ research) | `gsd-plan-phase` |
| Execute | code + atomic commits (worktree/PR) | `gsd-execute-phase` |
| Verify | `VERIFICATION.md` | verify skill / `python3 scripts/gsd_phase_gate.py --json` |
| Ship | PR merge SHA + update `.planning/STATE.md` | ship |

**Context engineering:** heavy research/plan/execute runs in fresh-context subagents; keep the orchestrator lean. See OpenGSD docs on context rot.

**Gate:** Do not claim phase done unless `scripts/gsd_phase_gate.py` reports `ship_ready=true` (CONTEXT + PLAN + VERIFICATION present).

## Artifact GSD (repo law — unchanged)

Every automation/product cycle must still produce one of:

- Merged PR (merge SHA)
- Green workflow run URL
- Updated `marketing/data/*.json` on `develop`
- Published wiki / GitHub Release / store read-back log

OpenGSD verify is **necessary but not sufficient** without one of the artifacts above.

## Priority order

1. Revenue blockers (IAP console, paywall catalog, publish)
2. Distribution (internal signoff → Firebase / TestFlight)
3. Store parity (release branch, read-back)
4. Analytics freshness (wiki-sync, executive-metrics)
5. Hygiene (green PRs, dependabot)

## Planning SSOT

| File | Role |
|------|------|
| `.planning/STATE.md` | Where we are in the loop |
| `.planning/PROJECT.md` | Core value + constraints |
| `.planning/ROADMAP.md` | Milestone phases |
| `.planning/phases/*/` | Per-phase CONTEXT / PLAN / VERIFICATION |

## Automation vs CEO

See **`docs/AUTONOMOUS_OPERATIONS.md`** and **`.claude/scheduled_tasks.json`**.

## Code discipline

- Worktree + PR off `develop` (`docs/workflow.md`)
- Ralph Loop for multi-step fixes: `.claude/skills/ralph-mode.md`
- TDD for product code: `AGENTS.md`
- Device evidence: `scripts/agent_device_doctor.py` + `docs/DEVICE_E2E_TESTS.md`
