# AdMob setup (P1 rewarded ads)

## Account state (verified 2026-05-27)

| Item | Value |
|------|--------|
| Publisher ID | `pub-5173650670360699` |
| Android app | Linked to Play package `com.iganapolsky.randomtimer` (Random Tactical Timer) |
| Android App ID | `ca-app-pub-5173650670360699~4427145410` |
| Android rewarded unit | `ca-app-pub-5173650670360699/8693693481` (`rtt_pro_sound_trial_rewarded`) |
| app-ads.txt line | `google.com, pub-5173650670360699, DIRECT, f08c47fec0942fa0` |
| Hosted file (project site) | `https://igorganapolsky.github.io/Random-Timer/app-ads.txt` |
| **AdMob crawler (required)** | `https://igorganapolsky.github.io/app-ads.txt` on [`IgorGanapolsky.github.io`](https://github.com/IgorGanapolsky/IgorGanapolsky.github.io) — hostname root, per [Google crawl rules](https://support.google.com/admob/answer/9363762) |

## Verification

1. Play Console **Developer website** (`contactWebsite`) is synced from iOS `support_url.txt` (`…/Random-Timer/support/`). Host `app-ads.txt` at that path **and** at site root.
2. After deploy, run:
   ```bash
   python3 scripts/admob_status.py --also-check-play-contact-path
   ```
   (`app-ads.txt` must exist at **repo root** and `support/` for Jekyll Pages on `develop`, plus under `marketing/site/` for the growth artifact deploy.)
3. In AdMob UI → **Verify app** → **Check for updates** (no API for app-ads crawl; up to ~24h).

## IDs in AdMob vs OAuth (do not confuse)

| What | Where it lives | Used for |
|------|----------------|----------|
| **Publisher ID** | AdMob → Payments / account settings (`pub-5173650670360699`) | `app-ads.txt` line, account identity |
| **App ID** | AdMob → Apps → app settings (`ca-app-pub-…~4427145410`) | **Mobile SDK** (`AndroidManifest` / `BuildConfig`) |
| **Ad unit ID** | AdMob → Ad units (`ca-app-pub-…/8693693481`) | **Mobile SDK** (rewarded load/show) |
| **OAuth access token** | **Not in AdMob UI** — temporary, from [Google Cloud OAuth](https://console.cloud.google.com/) + user consent ([OAuth Playground](https://developers.google.com/oauthplayground/) for one-off tests) | **AdMob REST API only** (optional ops scripts) |

There is **no permanent “API access token”** inside the AdMob website. Google uses **OAuth 2.0**; tokens expire (typically ~1 hour).

**This app’s shipped integration** uses the **SDK + Publisher/App/Unit IDs** above. It does **not** need an OAuth access token at runtime.

### AdMob API from CLI (preferred: Application Default Credentials)

One-time on a Mac with `gcloud` logged in as the AdMob owner:

```bash
gcloud auth application-default login \
  --scopes=https://www.googleapis.com/auth/admob.readonly,https://www.googleapis.com/auth/cloud-platform
```

Then (no `ADMOB_ACCESS_TOKEN` needed):

```bash
python3 scripts/admob_token_probe.py
python3 scripts/admob_status.py --also-check-play-contact-path --api
```

Equivalent `curl` (note **quota project** header — required for ADC):

```bash
TOKEN=$(gcloud auth application-default print-access-token)
curl -s \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Goog-User-Project: random-timer-dist-new" \
  "https://admob.googleapis.com/v1/accounts/pub-5173650670360699/apps?pageSize=20" \
  | python3 -m json.tool
```

**Why Playground `curl` returned 401:** expired or wrong token type. Use ADC above instead of pasting `access_token` into `ADMOB_ACCESS_TOKEN`.

`gcloud auth print-access-token` (user creds) does **not** include AdMob scopes. Use **application-default** as shown.

**Security:** Never paste OAuth access tokens into chat, issues, or commits. Store locally only, e.g. `export ADMOB_ACCESS_TOKEN='ya29...'` or a gitignored `.env` line.

### CEO manual OAuth (≈60s) — Cloud Console links

1. [Enable AdMob API](https://console.cloud.google.com/apis/library/admob.googleapis.com)
2. [Create OAuth client](https://console.cloud.google.com/apis/credentials/oauthclient) (Web or Desktop; name e.g. `AdMob Token Generator`)
3. [OAuth 2.0 Playground](https://developers.google.com/oauthplayground/) — **required settings:**
   - Gear icon → **Use your own OAuth credentials** (Web client ID + secret from step 2)
   - Web client must include redirect URI: `https://developers.google.com/oauthplayground`
   - Step 1 scope: `https://www.googleapis.com/auth/admob.readonly`
   - Sign in as the **same Google account** that owns AdMob `pub-5173650670360699`
   - Step 2 → copy **`access_token`** (not `refresh_token`) into `ADMOB_ACCESS_TOKEN`
4. Probe (no token printed): `python3 scripts/admob_token_probe.py`

### After you have a token (repo CLI — preferred)

```bash
export ADMOB_ACCESS_TOKEN='ya29....'   # short-lived; do not commit

# Hosted app-ads.txt (no token required)
python3 scripts/admob_status.py --also-check-play-contact-path

# Optional: list apps + Android approval state
python3 scripts/admob_status.py --also-check-play-contact-path --api
```

### Raw `curl` (same API the script calls)

```bash
export ADMOB_ACCESS_TOKEN='ya29....'
curl -s -H "Authorization: Bearer $ADMOB_ACCESS_TOKEN" \
  "https://admob.googleapis.com/v1/accounts/pub-5173650670360699/apps?pageSize=20" | python3 -m json.tool
```

The API returns `appApprovalState` (`IN_REVIEW`, `APPROVED`, etc.). It does **not** return app-ads.txt verification status.

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
