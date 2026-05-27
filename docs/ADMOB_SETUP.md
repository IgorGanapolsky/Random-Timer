# AdMob setup (P1 rewarded ads)

## Account state (verified 2026-05-27)

| Item | Value |
|------|--------|
| Publisher ID | `pub-5173650670360699` |
| Android app | Linked to Play package `com.iganapolsky.randomtimer` (Random Tactical Timer) |
| Android App ID | `ca-app-pub-5173650670360699~4427145410` |
| Android rewarded unit | `ca-app-pub-5173650670360699/8693693481` (`rtt_pro_sound_trial_rewarded`) |
| app-ads.txt line | `google.com, pub-5173650670360699, DIRECT, f08c47fec0942fa0` |
| Hosted file | `marketing/site/app-ads.txt` → `https://igorganapolsky.github.io/Random-Timer/app-ads.txt` after site deploy |

## Verification

1. Play Console **Developer website** domain must match where `app-ads.txt` is hosted (path included if listing uses a subpath).
2. After deploy, run: `python3 scripts/verify_app_ads_txt.py`
3. In AdMob → **Verify app** → **Check for updates**.

## Payment setup

AdMob home shows **Payment setup incomplete**. Required for payouts and full ad serving; test ads can use Google test unit IDs in debug without payment info.

## Production IDs (CI / local)

Android IDs are baked into `BuildConfig` (override via env if needed):

| Env (optional) | Default (AdMob console) |
|----------------|-------------------------|
| `ADMOB_APP_ID_ANDROID` | `ca-app-pub-5173650670360699~4427145410` |
| `ADMOB_REWARDED_UNIT_ID_ANDROID` | `ca-app-pub-5173650670360699/8693693481` |

Debug builds use [Google test ad units](https://developers.google.com/admob/android/test-ads). PostHog flag `rewarded_ads_enabled` stays **off** until app-ads.txt verifies and you enable the experiment.

## iOS app in AdMob

Add iOS app (App Store link `6758355312`) and a rewarded ad unit — same publisher ID.

## Code

- Feature flag: `rewarded_ads_enabled` (default off)
- Android: `AdMobRewardedAdPort`, `RewardedAdCoordinator`, `RewardedAdConfig` (SDK wired; UI hookup + flag still required)
- Events: `rewarded_ad_requested`, `rewarded_ad_completed`, `rewarded_ad_unlock`
