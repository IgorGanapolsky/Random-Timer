# App Store Version Automation

## Problem solved

Metadata/screenshot uploads can appear successful when aimed at a non-editable live
App Store version, but storefront media may not update.

This repo now resolves an **editable target App Store version** before metadata sync.

## Resolver script

Use `scripts/asc/asc_resolve_version.py`:

```bash
python scripts/asc/asc_resolve_version.py \
  --preferred-version 1.1.1 \
  --create-if-needed \
  --auto-next-patch \
  --json-out .artifacts/asc_version.json
```

Behavior:

1. If preferred version exists and is editable, use it.
2. If preferred exists but is not editable:
   1. With `--auto-next-patch`, walk patch versions (`X.Y.Z+1`) until an editable
      existing version is found or create the next missing patch (if `--create-if-needed`).
   2. Without `--auto-next-patch`, fail fast.
3. If preferred does not exist:
   1. With `--create-if-needed`, create it.
   2. Otherwise fail.

## Workflow integration

- `.github/workflows/ios-metadata-sync.yml`
  - Resolves editable version before `asc_strict_screenshot_sync.py` (which calls `fastlane metadata` for that version).
  - **Does not** use `fastlane deliver` `use_live_version:true`. When ASC has zero editable IOS versions (e.g. preferred `1.3.48` is `WAITING_FOR_REVIEW` and create-next-patch returns HTTP 409), the job fails fast with `asc_list_versions.py` inventory instead of retrying deliver for ~20 minutes.
  - `metadata_only=true` only skips the VALID build gate (`--skip-build-check`); it does not bypass the editable-version requirement.
  - `use_live_version` input is deprecated/ignored.
  - Uploads `asc-version-resolution` artifact.

- `.github/workflows/ios-submit-review.yml`
  - Resolves editable version before metadata + submit flow.
  - Uploads `asc-version-resolution` artifact.

- `.github/workflows/native-release.yml` (`ios-submit-review` job)
  - Resolves editable version before metadata/upload/submit.
  - Uploads `asc-version-resolution` artifact.

- `scripts/release_ops.py sync_listing`
  - Resolves editable version before calling `fastlane metadata`.
  - Persists resolver output JSON (default: `.artifacts/asc-version-resolution.json`).

## Readiness verifier mode

`scripts/asc/asc_verify_ready.py` now supports:

```bash
--skip-build-check
```

Use only for metadata-only workflows that intentionally do not gate on build attach/VALID.

## Test coverage

- `scripts/tests/test_asc_resolve_version.py`
  - Semver parsing/patch bump.
  - Editable state selection.
  - Preferred/live fallback to next patch.
  - Create-missing behavior.
- `scripts/tests/test_asc_verify_ready.py`
  - Screenshot delivery-state gating.
  - Metadata-only build skip mode.
