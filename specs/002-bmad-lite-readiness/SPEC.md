# SPEC.md — BMAD-lite readiness harness

**Feature**: BMAD-lite readiness gate
**Slug**: `002-bmad-lite-readiness`
**Flow**: Quick
**Status**: Implemented

## Why

Agents jump from blog posts and prompts into code without a testable contract.
BMAD-lite forces a five-element SPEC before implementation claims.

## Capabilities

1. **Capability**: Enforce Why / Capabilities / Constraints / Non-goals / Success signal
   **Success condition**: Given a SPEC missing a section, When the gate runs, Then `ready` is false

2. **Capability**: Support Quick vs Full flow
   **Success condition**: Given `--require-spec-kit` without plan/tasks, When the gate runs, Then blockers include missing plan or tasks

## Constraints

- Prefer zero-cost local tooling
- Do not install full `bmad-method` unless CEO requests the heavy framework
- Bridge Spec Kit, OpenGSD, and Superpowers — do not replace them

## Non-goals

- Enterprise PRD/UX spine for every one-line fix
- SaM Solutions commercial services

## Success signal

`python3 scripts/bmad_readiness_gate.py --json --feature 002` reports `ready=true` and
`python3 -m pytest scripts/tests/test_bmad_readiness_gate.py -q` passes.
