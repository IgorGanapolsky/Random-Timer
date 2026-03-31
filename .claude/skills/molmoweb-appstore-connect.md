---
name: molmoweb-appstore-connect
description: Use MolmoWeb for visual App Store Connect inspection and evidence, then use the ASC API skill for real publishing mutations.
user_invocable: true
---

# MolmoWeb App Store Connect

Use this when Claude needs browser-native inspection of App Store Connect state before or after a release operation.

## When To Use

- Inspect submission status visually
- Confirm missing metadata or screenshots in the browser UI
- Capture trajectory evidence for ASC review blockers
- Verify post-submit UI state after API-driven actions

## Execution Pattern

1. Use `molmoweb-browser-verify` with a focused read-only query about the visible ASC workflow.
2. Save the HTML trajectory under `evidence/molmoweb/`.
3. Use `appstore-connect` for actual submission or metadata mutations.
4. Re-run MolmoWeb verification for visual confirmation if needed.

## Example Prompts

- `Use molmoweb-appstore-connect to inspect the current App Store Connect submission status and save evidence.`
- `Use molmoweb-appstore-connect to verify whether the current build shows any review blockers in the browser UI.`

## Rule

- Prefer the ASC API skill for the final state-changing step; use MolmoWeb as the visual co-pilot and evidence layer.
