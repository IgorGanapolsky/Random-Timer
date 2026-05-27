# AdMob setup (P1 rewarded ads)

## Account state (verified 2026-05-27)

| Item | Value |
|------|--------|
| Publisher ID | `pub-5173650670360699` |
| Android app | Linked to Play package `com.iganapolsky.randomtimer` (Random Tactical Timer) |
| app-ads.txt line | `google.com, pub-5173650670360699, DIRECT, f08c47fec0942fa0` |
| Hosted file | `marketing/site/app-ads.txt` → `https://igorganapolsky.github.io/Random-Timer/app-ads.txt` after site deploy |

## Verification

1. Play Console **Developer website** domain must match where `app-ads.txt` is hosted (path included if listing uses a subpath).
2. After deploy, run: `python3 scripts/verify_app_ads_txt.py`
3. In AdMob → **Verify app** → **Check for updates**.

## Payment setup

AdMob home shows **Payment setup incomplete**. Required for payouts and full ad serving; test ads can use Google test unit IDs in debug without payment info.

## Production IDs (CI / local)

Set after creating ad units in AdMob (Apps → app → Ad units → Rewarded):

| Secret / env | Purpose |
|--------------|---------|
| `ADMOB_APP_ID_ANDROID` | `ca-app-pub-…~…` from AdMob app settings |
| `ADMOB_REWARDED_UNIT_ID_ANDROID` | Rewarded ad unit ID |
| `ADMOB_APP_ID_IOS` | iOS app ID |
| `ADMOB_REWARDED_UNIT_ID_IOS` | iOS rewarded unit |

Until set, code uses [Google test IDs](https://developers.google.com/admob/android/test-ads) and PostHog flag `rewarded_ads_enabled` stays **off** in production.

## iOS app in AdMob

Add iOS app (App Store link `6758355312`) and a rewarded ad unit — same publisher ID.

## Code

- Feature flag: `rewarded_ads_enabled` (default off)
- Android: `RewardedAdConfig`, `RewardedAdCoordinator`, `StubRewardedAdPort` (SDK wiring in progress)
- Events: `rewarded_ad_requested`, `rewarded_ad_completed`, `rewarded_ad_unlock`
