# Implementation Plan: Spec Kit Harness Gate

**Branch**: `001-speckit-harness-gate` | **Date**: 2026-09-14 | **Spec**: `./spec.md`

## Summary

Wire GitHub Spec Kit 1.0.6 into Random Timer with Cursor/Claude skills, Random Timer
constitution, bug extension, and an enforceable Python gate. Prefer zero-cost local tooling only.

## Technical Context

- **Language**: Python 3 (gates/tests), bash (specify scripts)
- **Dependencies**: `uv tool install specify-cli==1.0.6` (local tool, not a repo Python dep)
- **Storage**: `.specify/`, `specs/`, `.cursor/skills/speckit-*`, `.claude/skills/speckit-*`
- **Constraints**: Preserve OpenGSD + rose-lite hooks; stay within the existing monthly external spend ceiling

## Project Structure

```text
.specify/                 # Spec Kit infra + constitution + bug extension
specs/001-.../            # Feature SDD artifacts
scripts/speckit_gate.py   # Enforcer
scripts/install_speckit.sh
docs/SPEC_KIT.md
```

## Complexity Tracking

Skipped idea-assess extension and empty Hermes stub — not justified for native app ROI.
