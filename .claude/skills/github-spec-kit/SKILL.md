---
name: github-spec-kit
description: Use GitHub Spec Kit (specify-cli) Spec-Plan-Tasks-Implement-Converge loop and bug assess-fix-test; enforce scripts/speckit_gate.py before done claims.
---

# GitHub Spec Kit

Upstream: https://github.com/github/spec-kit

## When

Non-trivial feature work, harness changes, or scoped bug fixes where jumping straight to code has failed before.

## Steps

1. Confirm `./scripts/install_speckit.sh` already run (or `.specify/` present).
2. Read `.specify/memory/constitution.md`.
3. Feature: `/speckit-specify` → `/speckit-plan` → `/speckit-tasks` → `/speckit-implement` → `/speckit-converge`.
4. Bug: `/speckit-bug-assess` → `/speckit-bug-fix` → `/speckit-bug-test`.
5. Gate: `python3 scripts/speckit_gate.py --json` (add `--require-converge` for Converge claims).
6. Still produce artifact GSD (merge SHA / CI URL / marketing JSON). Bridge with OpenGSD via `scripts/gsd_phase_gate.py`.

## Do not

- Skip constitution placeholders.
- Claim done on unit-green alone.
- Add paid Spec Kit catalogs or SaaS.
