# SPEC.md — BMAD five-element implementation contract

**Feature**: [short name]  
**Slug**: `[###-feature-slug]`  
**Flow**: Quick | Full  
**Status**: Draft | Ready | Implemented

## Why

[Business / user problem in 2–4 sentences. Not a solution.]

## Capabilities

List each capability with an observable success condition.

1. **Capability**: …  
   **Success condition**: Given …, When …, Then …

2. **Capability**: …  
   **Success condition**: …

## Constraints

- Technical constraints (platforms, APIs, offline/online, privacy)
- Process constraints (worktree/PR, TDD, evidence gates)
- Budget / tooling constraints (prefer zero-cost paths)

## Non-goals

- Explicitly out of scope (prevent agent invention)

## Success signal

One measurable signal that proves the feature worked (command, metric, or store read-back). Example: `python3 scripts/bmad_readiness_gate.py --json --feature ###` reports `ready=true` and the feature tests pass.
