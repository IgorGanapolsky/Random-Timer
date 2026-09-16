---
name: store-rejection-auto-heal
description: >-
  Automatically diagnoses App Store or Play rejection / Metadata Rejected states,
  applies listing or binary fixes, and resubmits without CEO babysitting. Use when
  ASC shows REJECTED, METADATA_REJECTED, INVALID_BINARY, or Play console rejects
  a production release.
---

# Store rejection auto-heal

## Trigger states (iOS)

- `REJECTED`
- `METADATA_REJECTED`
- `INVALID_BINARY`
- `DEVELOPER_REJECTED` (only if we caused it and must recover)

## Loop (no CEO handoff)

1. **Read rejection** — ASC resolution center / review detail via existing ASC scripts or logged-in browser attach (never incognito).
2. **Classify** — metadata vs binary vs guideline vs account.
3. **Fix in repo** — minimal diff; TDD when code; update fastlane metadata when copy.
4. **Resubmit** — `asc_submit_for_review.py` / release workflow with **`automatic_release: true`**.
5. **Verify** — state returns to `WAITING_FOR_REVIEW`; watcher tracks **that** version.
6. **Evidence** — issue comment on `Release watch: vX.Y.Z` with sanitized ASC response.

## Play

- Read edit errors from Publisher API / Play Console logged-in tab.
- Fix listing / policy / AAB; re-commit production track via existing native-release path.
- Do not invent new paid SaaS under the $20/mo cap.

## Stop conditions (only real stops)

- Account / contract / banking hold requiring Account Holder in ASC/Play.
- Guideline dispute needing CEO product decision (pricing, age rating change).
- Hard multi-agent file lock conflict.

Otherwise: heal and resubmit in the same session.

## Related

- `store-publish-100-automation`
- `asc-after-approval-auto-release`
