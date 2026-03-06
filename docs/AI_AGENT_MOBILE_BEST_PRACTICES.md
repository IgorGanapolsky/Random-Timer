# AI Agent Mobile Best Practices

This repository enforces a practical subset of AI-agent mobile practices focused on defects we have repeatedly hit:
- UI/UX regressions on one platform only.
- Missing or inconsistent E2E coverage.
- Drift between local hooks and CI quality gates.
- Debug/release behavior surprises.

## High-ROI Controls

1. Guardrail scripts are executable contracts, not documentation-only suggestions.
2. Cross-platform parity is required for critical interactions:
   - range controls
   - volume controls
   - timer-circle interactions
3. E2E assets must exist for Android and iOS (`.maestro` flows).
4. Pre-commit and CI must both enforce the same guardrails.
5. Release/debug behavior must be covered by explicit tests.

## Enforcement Matrix

- `scripts/ui-ux-audit.sh`:
  - Android UI/UX contract checks.
  - Enforced in pre-commit and CI.
- `scripts/ai-mobile-guardrails.sh`:
  - Cross-platform parity + agent workflow checks.
  - Enforced in pre-commit and CI.
- `.github/workflows/device-tests.yml`:
  - Maestro smoke validation on emulator.
- `native-android/.../CircularTimerTest.kt` + `native-ios/.../CircularTimerViewTests.swift`:
  - circular timer behavior parity coverage.
- `native-android/.../ProManagerDebugUnlockGuardTest.kt`:
  - debug/release monetization guard coverage.

## Operating Rule

If a guardrail fails, fix the underlying issue or update the guardrail intentionally in the same PR with clear rationale and tests. Do not bypass by removing checks.

