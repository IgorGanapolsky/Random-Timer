# App Store Version Automation

## Problem solved

Metadata/screenshot uploads can appear successful when aimed at a non-editable live
App Store version, but storefront media may not update.

This repo now resolves an **editable target App Store version** before metadata sync.

## Resolver script

Use `scripts/asc_resolve_version.py`:

```bash
python scripts/asc_resolve_version.py \
  --preferred-version 1.1.1 \
  --create-if-needed \
  --auto-next-patch \
  --json-out /tmp/asc_version.json
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
  - Resolves editable version before `fastlane metadata`.
  - Uses `asc_verify_ready.py --skip-build-check` because this workflow is listing-only.
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

`scripts/asc_verify_ready.py` now supports:

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
