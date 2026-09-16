---
name: store-publish-100-automation
description: >-
  Closes Random Timer / ASC / Play store publish to near-100% hands-off automation
  after submit. Use when the CEO asks for full automation, why publish is not automatic,
  AFTER_APPROVAL vs MANUAL, PENDING_DEVELOPER_RELEASE, store-release-watcher, or
  auto-release after Apple approval (Sept 2026 playbook).
---

# Store publish 100% automation (Sept 2026)

## Honest ceiling

**True 100% end-to-end is impossible** while Apple App Review is a human gate.
Everything else in *our* critical path must be automatic.

| Stage | Automatable? | Mechanism |
|-------|--------------|-----------|
| Build + upload (iOS/Android) | Yes | `native-release.yml` |
| Preflight + submit for review | Yes | `asc_submit_for_review.py` + Fastlane |
| App Review | **No** | Apple humans |
| Post-approval → live (iOS) | Yes | `releaseType: AFTER_APPROVAL` via Fastlane `automatic_release: true` |
| Stuck MANUAL release | Yes | Watcher → `POST /v1/appStoreVersionReleaseRequests` via `asc_release_version.py` |
| Play production rollout | Yes | Publisher API `completed` / staged fraction (already in release path) |
| Rejection / Metadata Rejected | Mostly | Agent loop: diagnose → fix → resubmit (skill `store-rejection-auto-heal`) |
| Account holds / contracts / export compliance | No / rare | Human ASC account actions |

Never tell the CEO "nothing left to do" unless `releaseType=AFTER_APPROVAL` is verified on the submitted version **and** watcher watches that version (not only develop tip).

## Required repo state

1. `native-ios/fastlane/Fastfile`: `automatic_release: true` (maps to ASC `AFTER_APPROVAL`).
2. `store-release-watcher.yml`:
   - Prefer ASC versions in review/pending over develop tip.
   - On `PENDING_DEVELOPER_RELEASE`, auto-run `scripts/asc_release_version.py`.
3. `ios-release-approved-version.yml` remains a manual override only.
4. Verify after submit:
   ```bash
   # Expect releaseType AFTER_APPROVAL on the waiting version
   python3 scripts/asc/asc_poll_version_state.py --version <X.Y.Z> --json
   ```

## Agent execution checklist

```
- [ ] Confirm Fastfile automatic_release: true
- [ ] Confirm submitted ASV releaseType == AFTER_APPROVAL (PATCH if MANUAL and editable)
- [ ] Confirm watcher target == submitted version (not ahead develop tip)
- [ ] On PENDING_DEVELOPER_RELEASE: run asc_release_version.py; read back READY_FOR_SALE / PROCESSING
- [ ] Play: confirm production track completed (or intended fraction)
- [ ] Report residual: only Apple review / rejection / account hold
```

## Do not

- Claim publish is automatic while `automatic_release: false` / `releaseType: MANUAL`.
- Rely on watcher alone when it watches develop tip ahead of the in-review version.
- Ask the CEO to click "Release This Version" — agents own `appStoreVersionReleaseRequests`.
- Spend against the $20/mo cap for paid release tooling; ASC + Play APIs are free within existing keys.

## References

- Apple: Select an App Store version release option (Automatically release this version).
- Apple API: `appStoreVersionReleaseRequests` for MANUAL pending release.
- Fastlane deliver: `automatic_release: true` → `AFTER_APPROVAL` (community confirmation May 2026).
- Repo: `scripts/asc_release_version.py`, `.github/workflows/store-release-watcher.yml`.

## Related skills

- `asc-after-approval-auto-release` — iOS releaseType + PATCH + release request.
- `store-rejection-auto-heal` — rejection → fix → resubmit loop.
