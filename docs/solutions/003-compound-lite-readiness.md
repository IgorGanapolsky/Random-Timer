---
title: "Compound Engineering lite readiness"
date: "2026-09-14"
category: "process"
tags: ["compound-lite", "gate", "docs-solutions"]
status: active
source_pr: "feat/compound-engineering-lite"
---

# Compound Engineering lite readiness

## Problem

Random Timer already ran Superpowers (plan/TDD checkpoints) and OpenGSD (phase checkpoints), but corrections often died in chat. The same agent mistakes recurred because nothing wrote the lesson into a file the next session loads.

## What worked

Adopted the Compound Engineering **fourth step only**: after non-trivial work, write a solution note under `docs/solutions/` from `templates/compound/SOLUTION.md`, then verify with `python3 scripts/compound_gate.py --json`.

Did **not** install the full EveryInc plugin (33 skills + parallel reviewer farm) — token cost and overlap with Superpowers / Spec Kit / BMAD-lite.

## Prevention

- After a non-trivial PR merge (or when the same correction appears twice), add `docs/solutions/<slug>.md`.
- Gate: `python3 scripts/compound_gate.py --json --slug <slug>` must report `ready=true` before claiming the compound step is done.
- Prefer encoding Prevention as a gate, skill, or AGENTS.md / CLAUDE.md bullet.

## Evidence

- Command: `pytest scripts/tests/test_compound_gate.py -q`
- Gate: `python3 scripts/compound_gate.py --json --slug 003`
- Article: https://theaiengineer.substack.com/p/superpowers-vs-gsd-vs-compound-engineering
- Upstream doctrine: https://every.to/guides/compound-engineering
