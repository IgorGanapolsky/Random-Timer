# Compound Engineering (lite) on Random Timer

Source article: https://theaiengineer.substack.com/p/superpowers-vs-gsd-vs-compound-engineering  
Upstream doctrine: https://every.to/guides/compound-engineering  
Plugin (not fully installed): https://github.com/EveryInc/compound-engineering-plugin

## One-line framing (from the article)

Superpowers / OpenGSD / Ralph are **lengths of rope** (where the agent must stop).  
**Compound Engineering is not a rival rope** — it is the fourth loop step that writes each correction into files the next run loads.

## High-ROI adopted

1. **Plan → Work → Review → Compound** — the compound step is mandatory after non-trivial work or a repeated correction
2. **`docs/solutions/`** — searchable markdown with YAML frontmatter (`templates/compound/SOLUTION.md`)
3. **Gate** — `scripts/compound_gate.py` rejects missing sections and placeholders
4. **Compose with existing stack** — Superpowers for plan/TDD, OpenGSD for phases, Spec Kit / BMAD-lite for feature specs

## Explicitly skipped

- Full `/plugin install compound-engineering` (33 skills; weekly command churn)
- Default **parallel multi-persona reviewer farm** (token-heavy; article says gate to security/money PRs)
- `/ce-lfg` 50-agent mega-pipeline
- Treating Compound Engineering as a replacement for Superpowers or OpenGSD

## Stack map

| Layer | Tooling |
|-------|---------|
| Process checkpoints (how) | Superpowers |
| Feature SDD | Spec Kit + BMAD-lite `SPEC.md` |
| Phase roadmap | OpenGSD (`.planning/`) |
| Learning capture (compound) | **CE-lite `docs/solutions/`** |
| Hawk metrics / lifecycle ROI | `docs/AGENT_COMPOUNDING_ROI.md` (PlayerZero method; separate) |
| Ship evidence | Merge SHA / CI / `marketing/data` |

## When to compound

- Same correction appeared twice in a week
- Non-trivial bugfix or process failure that would otherwise live only in chat
- After a phase/PR where Prevention can be encoded as a gate or rule

Skip for one-line typo PRs (article: short rope / bare prompt is fine).

## Gate

```bash
python3 scripts/compound_gate.py --json
python3 scripts/compound_gate.py --json --slug 003
```

Fixture: `docs/solutions/003-compound-lite-readiness.md`

## Verify install (no upstream plugin)

```bash
./scripts/install_compound_lite.sh
```

## pstack bridge

`encode-lessons-in-structure` maps to Compound write-ups under `docs/solutions/` — see `docs/PSTACK.md`.
