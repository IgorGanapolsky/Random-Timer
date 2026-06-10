# Google Play testing tracks (Random Timer)

**Policy (effective 2026-06-09):** Random Timer ships on the **production** track. CEO and internal QA install the **public Play Store listing** — not Open testing (beta). Beta/Open testing uploads require **explicit CEO opt-in** per dispatch.

## Account context

Random Timer uses a **Google Play business (LLC) account**. Business accounts can publish directly to production without Open testing. Open testing is optional and is **not** required for production releases.

**License testing (mandatory for CEO IAP QA):** A retail Play account **not** listed under **Settings → License testing** is charged real money for production IAP — add `iganapolsky@gmail.com` before any paywall purchase test.

## Track definitions

| Track | Play Console name | Who gets the build | Automation default |
|-------|-------------------|--------------------|--------------------|
| **Production** | Production | All Play Store users (public listing) | **Yes** — `native-release.yml` `android_track` default |
| **Closed testing** | Internal / Closed | Invite-only testers (email list) | Only via explicit dispatch; use for pre-prod smoke if needed |
| **Open testing** | Open testing (beta) | Anyone who opts in via Play Store beta link | **No** — do not dispatch unless CEO requests |
| **Internal testing** | Internal testing | Fastest, up to 100 testers | Firebase internal + `internal-distribution.yml` before production |

## Disable / stop Open testing (CEO steps)

Use a logged-in Safari, Comet, or normal Chrome tab on Play Console (not incognito).

1. Open **Play Console** → **Random Tactical Timer** → **Testing** → **Open testing**.
2. If a release is **Active**, open it → **Halt rollout** or **Deactivate** (wording varies by release state).
3. On the device (e.g. Samsung S25):
   - Open Play Store → profile → **Manage apps & device** → **Beta programs** (or **Settings** → **Beta programs**).
   - Find **Random Tactical Timer** → **Leave** the beta program.
4. Uninstall the beta build if the launcher title shows **(Beta)** or version lags production.
5. Reinstall from the **public store listing** (no Beta badge): search "Random Tactical Timer" and install without joining any test program.

Optional: remove stale testers under **Open testing** → **Testers** if you want zero beta enrollment surface.

## CEO device QA (production only)

After `native-release` with `android_track=production` and green `verify-releases`:

1. Confirm Play Publisher API: `versionName` + `versionCode` on **production** track, status `completed` (Tier 0 — blocks ship).
2. On device: install/update from **production** Play Store (not beta).
3. If USB debugging enabled: `adb shell dumpsys package com.iganapolsky.randomtimer | grep version` — expect `versionName=1.3.55` (or current ship version).

Public storefront HTML may lag the Publisher API by hours; Tier 0 API read-back is ground truth per `docs/OPERATIONAL_RELIABILITY.md`.

## Automation rules

### `native-release.yml`

- Default `android_track`: **`production`** (workflow input default).
- Always pass explicitly when dispatching:  
  `gh workflow run native-release.yml --ref release/vX.Y.Z -f platform=android -f android_track=production`
- **Never** pass `android_track=beta` unless the CEO explicitly requests Open testing.
- `verify-releases` must show `Android production … ✅ completed` before claiming shipped.

### Internal pre-prod proof

Use `internal-distribution.yml` (Firebase APK) + signoffs, then production `native-release`. Do **not** substitute Open testing for CEO device validation.

### Closed testing (invite-only)

If pre-production device checks are needed without public rollout, use **Closed testing** (invite CEO email only) — still not Open testing. Document the dispatch in the release PR; default remains production.

## Evidence checklist (ship claim)

- [ ] `verify-releases` job: `Android production <versionCode> (<versionName>) ✅ completed`
- [ ] Git tag `vX.Y.Z` on release SHA
- [ ] CEO device on production listing (no beta enrollment)
- [ ] PostHog `properties.$app_version` matches ship version on retail cohort
