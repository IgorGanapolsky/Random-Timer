# Feature Specification: Spec Kit Harness Gate

**Feature Branch**: `001-speckit-harness-gate`

**Created**: 2026-09-14

**Status**: Implemented (harness)

**Input**: Adopt GitHub Spec Kit high-ROI pieces into Random Timer agent harness.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Agents cannot claim done without SDD artifacts (Priority: P1)

As CTO automation, I must refuse "feature done" unless constitution + spec + plan + tasks exist.

**Why this priority**: Prevents vibe-coding and false completion claims.

**Independent Test**: `python3 scripts/speckit_gate.py --json` returns `implement_ready=true` for this feature dir.

**Acceptance Scenarios**:

1. **Given** placeholders in constitution, **When** gate runs, **Then** `implement_ready=false` and `next_step=constitution`
2. **Given** full SDD trio without CONVERGENCE, **When** gate runs, **Then** `implement_ready=true` and `converged=false`
3. **Given** `--require-converge` without CONVERGENCE, **When** gate runs, **Then** `claim_done_allowed=false`

### User Story 2 - Bug triage loop available (Priority: P2)

As an agent fixing a defect, I can run assess → fix → test skills without inventing a process.

**Independent Test**: `.cursor/skills/speckit-bug-assess/SKILL.md` exists and `.specify/extensions.yml` lists `bug`.

## Requirements

- R1: Tracked `.specify/` infrastructure + Random Timer constitution
- R2: Cursor + Claude `speckit-*` skills
- R3: `scripts/speckit_gate.py` + unit tests
- R4: Install script pinned to specify-cli 1.0.6
- R5: Docs bridge to OpenGSD

## Success Criteria

- Gate unit tests pass
- Live gate on this fixture: `implement_ready=true`, `converged=true` with `--require-converge`
- `create-new-feature.sh --dry-run` exits 0
