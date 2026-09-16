---
name: asc-after-approval-auto-release
description: >-
  Forces App Store Connect releaseType AFTER_APPROVAL and releases PENDING_DEVELOPER_RELEASE
  versions via API. Use for Random Timer iOS publish automation, Fastlane automatic_release,
  appStoreVersionReleaseRequests, or when a version sits after Apple approval.
---

# ASC AFTER_APPROVAL auto-release

## Goal

Remove humans from the post-approval publish click for Random Timer iOS
(`com.igorganapolsky.randomtimer`, ASC app id `6758355312`).

## Primary path (preferred)

1. Fastlane deliver / `upload_to_app_store`: set **`automatic_release: true`**.
2. That sets ASC **`releaseType: AFTER_APPROVAL`**.
3. After App Review passes, Apple moves the version toward live (`READY_FOR_SALE` /
   `PENDING_APPLE_RELEASE` / processing) **without** a developer click.

Verify:

```bash
python3 scripts/asc/asc_poll_version_state.py --version <X.Y.Z> --json
# Prefer attributes including releaseType AFTER_APPROVAL when the poll script exposes it
```

## Safety net (MANUAL leftovers)

If state is **`PENDING_DEVELOPER_RELEASE`**:

```bash
python3 scripts/asc_release_version.py --version <X.Y.Z> --json
```

This POSTs `/v1/appStoreVersionReleaseRequests` (Apple: manually release approved version).
Idempotent if already `READY_FOR_SALE`.

Wire this into `store-release-watcher.yml` so cron fires the release — do not wait for
`workflow_dispatch` on `ios-release-approved-version.yml`.

## In-flight PATCH

If a version is already submitted with `releaseType: MANUAL` and ASC still allows edits:

```bash
python3 scripts/asc/asc_set_release_type.py --version <X.Y.Z> --release-type AFTER_APPROVAL --json
```

If PATCH is rejected while `WAITING_FOR_REVIEW` / `IN_REVIEW`, keep the safety net;
do not cancel review just to flip the flag unless CEO orders it.

## Evidence rules

- Never claim LIVE until iTunes lookup or ASC state shows the version live.
- Public listing lag (hours) ≠ not released — use ASC state as ground truth for release action.

## Hard don'ts

- Do not leave `automatic_release: false` in Fastfile for routine point releases.
- Do not ask the CEO to open ASC and click Release This Version.
- Do not watch only develop tip when an older marketing version is still in review.
