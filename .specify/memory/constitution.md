# Random Timer Constitution

Governing principles for Spec-Driven Development via
[GitHub Spec Kit](https://github.com/github/spec-kit) (`specify-cli` 1.0.6+).
This file is the project-level constitution for `/speckit-constitution` refreshes.

## Core Principles

### I. Evidence Before Claims (NON-NEGOTIABLE)

Never claim done, uploaded, ready, shipped, or fixed without read-back evidence:
command or API call, path, and sanitized output. Proxies are labeled (see
`docs/OPERATIONAL_RELIABILITY.md`). Absence of a counterexample is not proof.

### II. Spec Before Code

Non-trivial product or harness work follows Spec Kit:
`constitution` → `specify` → `plan` → `tasks` → `implement` → `converge`.
Do not jump to implementation from a vibe. Ambiguity is resolved with
`/speckit-clarify` or `/speckit-analyze` before `/speckit-implement`.

### III. Test-First (NON-NEGOTIABLE)

TDD for production code: failing test first, then minimal implementation.
Unit-green alone is not ship-ready — device/store/CI evidence when the change
touches those surfaces. Prefer `scripts/tests/` for harness gates.

### IV. Native Product, Zero-Cost Default

Ship native Android (Kotlin/Compose) and iOS (Swift/SwiftUI). Prefer zero-cost
tooling under the hard `the repo monthly tooling budget ceiling` external tooling budget ceiling. Do not adopt paid
services that can blow the cap without explicit CEO approval with dollar impact.

### V. North Star Alignment

Product NSM is **WQTU** (Weekly Qualified Training Users: ≥3 `timer_completed`
in trailing 7d). Business goal: earn `the published daily after-tax sales target` after-tax from app sales.
Prioritize work by expected impact on WQTU or paywall attempt→success, lowest
effort first. Query live PostHog before blaming conversion.

### VI. Worktree + Artifact GSD

Code changes land via worktree branches and PRs — never commit on the CEO's
active branch. Every cycle still needs an artifact: merge SHA, green CI URL,
`marketing/data/*.json`, or store/wiki read-back. OpenGSD phase gate and Spec
Kit feature gate are necessary; artifact GSD remains sufficient for ship claims.

### VII. English Only + Named Exports

All agent replies, comments, commits, and docs use English. JS/TS: named exports
only (no default exports) where the repo already enforces that rule.

## Additional Constraints

- **Secrets:** never commit credentials; verify `.env` key names and
  `gh secret list` before claiming access blockers.
- **Stores:** complete listing metadata before publish; production Play track
  unless CEO asks otherwise.
- **Bug path:** use Spec Kit bug extension (`assess` → `fix` → `test`) for
  scoped defect work; keep reports under `.specify/bugs/<slug>/`.
- **OpenGSD bridge:** phase planning lives in `.planning/`; feature specs live
  in `specs/`. Run both gates when a change spans phase + feature.

## Development Workflow

1. Read `.specify/memory/constitution.md` and `.planning/STATE.md`.
2. Feature work: `/speckit-specify` → `/speckit-plan` → `/speckit-tasks` →
   `/speckit-implement` → `/speckit-converge` until Converged.
3. Phase work: OpenGSD Discuss → Plan → Execute → Verify → Ship.
4. `python3 scripts/speckit_gate.py --json` must report `implement_ready` (or
   `converged` when claiming full Spec Kit completion) before "done".
5. Ship PR; update `.planning/STATE.md` when phases move; leave marketing/CI
   evidence.

## Governance

This constitution supersedes ad-hoc agent habits for Spec Kit flows. Amendments
require a PR that updates this file, `docs/SPEC_KIT.md`, and gate tests.
PRs that add Spec Kit skills must keep Cursor hooks (rose-lite / OpenGSD /
shunt) intact.

**Version**: 1.0.0 | **Ratified**: 2026-09-14 | **Last Amended**: 2026-09-14
