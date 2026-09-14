# PROJECT.md — Random Timer

## Core Value

Ship a native Android + iOS random-interval training timer that converts to Pro and compounds **WQTU** (users with ≥3 `timer_completed` in 7d), toward **$100/day after-tax**, under a hard **$20/mo** external spend cap.

## Constraints

- Native Kotlin/Compose + Swift/SwiftUI (`com.iganapolsky.randomtimer` / `com.igorganapolsky.randomtimer`) — not React Native.
- Evidence over claims (`docs/OPERATIONAL_RELIABILITY.md`).
- Worktrees + PRs off `develop`; never commit secrets.
- Device E2E via Simulator / agent-device / vphone — never seize CEO physical phone.

## OpenGSD

Upstream: https://github.com/open-gsd/gsd-core (`@opengsd/gsd-core@1.14.0`)

Local install: `./scripts/install_opengsd_cursor.sh`

Phase loop: Discuss → Plan → Execute → Verify → Ship

## Artifact GSD (repo law)

A phase is not done until at least one of: merge SHA, green workflow URL, committed `marketing/data/*.json`, store read-back.
