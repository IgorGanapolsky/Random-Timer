# OpenGSD (gsd-core) on Random Timer

Upstream: https://github.com/open-gsd/gsd-core

## Why

OpenGSD fixes three failure modes we hit as agents:

1. **Context rot** — long sessions degrade quality → fresh-context subagents for plan/execute
2. **No shared memory** — sessions forget → `.planning/STATE.md` + phase artifacts
3. **No verify** — unit-green ≠ done → `VERIFICATION.md` + `scripts/gsd_phase_gate.py`

## Install

```bash
./scripts/install_opengsd_cursor.sh
# pins @opengsd/gsd-core@1.14.0 --cursor --local --profile=core
```

Heavy runtime under `.cursor/gsd-core/` stays **gitignored**. Skills + hooks are tracked.

## Daily loop

1. Read `.planning/STATE.md`
2. Mentions: `gsd-discuss-phase` → `gsd-plan-phase` → `gsd-execute-phase`
3. `python3 scripts/gsd_phase_gate.py --json` must be `ship_ready` before claiming done
4. Ship PR; update STATE; leave a `marketing/data` or CI artifact

## Compatibility

Repo still enforces Random-Timer **artifact GSD** (merge SHA / CI URL / `marketing/data/*.json`). See `.claude/GSD.md`.

## Spec Kit

Feature-level SDD: see `docs/SPEC_KIT.md` and `python3 scripts/speckit_gate.py --json`.

## Superpowers

Process skills: see \`docs/SUPERPOWERS.md\` and \`python3 scripts/superpowers_gate.py --json\`.
