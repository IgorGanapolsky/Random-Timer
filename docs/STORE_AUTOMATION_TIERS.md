# Store automation tiers (Play + Apple + GitHub)

Canonical reliability rules: `docs/OPERATIONAL_RELIABILITY.md`.

## Tier A — CI and CLIs (durable)

Run on GitHub Actions or locally with service accounts / PATs. No interactive browser.

| Capability | How in this repo |
|------------|------------------|
| **GitHub** PRs, checks, secrets, workflows | `gh` CLI; `.github/workflows/*` |
| **PostHog / executive metrics** | `scripts/executive_metrics_snapshot.py`, `scripts/wqtu_dashboard.py`, workflows |
| **Play: Data Safety (Safety labels)** | `scripts/play_data_safety_upload.py` → `applications.dataSafety` API; workflow **Play Data Safety upload** |
| **Play: listings / releases** | `scripts/sync_android_metadata.py`, `scripts/play_publish.py`, Fastlane under `native-android/fastlane/` |
| **Play: reviews / tracks (API-covered)** | `scripts/real_store_downloads.py`, `scripts/verify_release.py` |
| **App Store Connect (API-covered)** | `scripts/asc/*`, Fastlane iOS |

**Data Safety CSV**

1. Export or build the CSV per [Google Help — Data safety](https://support.google.com/googleplay/android-developer/answer/10787469).
2. Either commit `marketing/compliance/play_data_safety.csv` or store the full file in GitHub secret **`PLAY_DATA_SAFETY_CSV`** (watch GitHub secret size limits).
3. Ensure **`GOOGLE_PLAY_JSON_KEY`** is set in Actions (same as other Play jobs).
4. Run workflow **Play Data Safety upload** (manual dispatch).

## Tier B — CEO machine or trusted profile (interactive once)

No official API for these today; complete in the vendor web console while logged in as the account owner.

| Task | Where |
|------|--------|
| **Play: Health apps declaration** (App content) | [Play Console](https://play.google.com/console) → app → **App content** → Health |
| **Apple: screens with no ASC API** | [App Store Connect](https://appstoreconnect.apple.com) web UI |

## Tier C — Semi-agent (your Chrome session)

Uses **Playwright + Chrome DevTools Protocol** attached to **your** already-signed-in Chrome (`localhost:9222`). The agent drives UI with **your** cookies; not usable from a headless cloud agent without your session.

| Script | Purpose |
|--------|---------|
| `scripts/play_fill_declarations.py` | Default: **reconnaissance** on App content. **`--health`**: open **Health** declaration, select **No** radios where visible, **Save** / **Submit**, screenshots under `.artifacts/play_console/`. |
| `scripts/play_console_declarations.py` | Broader App content walk (multiple sections). |

**Start Chrome with remote debugging (macOS example):**

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
```

Then:

```bash
uv run python scripts/play_fill_declarations.py --health
# or full recon (default):
uv run python scripts/play_fill_declarations.py
```

Play Console DOM changes over time; if a step fails, use screenshots in `.artifacts/play_console/` and finish manually.
