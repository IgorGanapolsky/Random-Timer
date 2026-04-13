# Store automation tiers (Play + Apple + GitHub)

Canonical reliability rules: `docs/OPERATIONAL_RELIABILITY.md`.

## Tier A — CI and CLIs (durable)

Run on GitHub Actions or locally with service accounts / PATs. No interactive browser.

| Capability | How in this repo |
|------------|------------------|
| **GitHub** PRs, checks, secrets, workflows | `gh` CLI; `.github/workflows/*` |
| **PostHog / executive metrics** | `scripts/executive_metrics_snapshot.py`, `scripts/wqtu_dashboard.py`, workflows |
| **Play: Data Safety (Safety labels)** | `scripts/generate_play_data_safety_csv.py` + `scripts/play_data_safety_upload.py` -> `applications.dataSafety` API; workflow **Play Data Safety upload** |
| **Store growth personas** | `scripts/store_growth_automation.py` builds Play custom listing copy, Apple Custom Product Page copy, UTM links, and SEO audience pages |
| **Play: listings / releases** | `scripts/sync_android_metadata.py`, `scripts/play_publish.py`, Fastlane under `native-android/fastlane/` |
| **Play: reviews / tracks (API-covered)** | `scripts/real_store_downloads.py`, `scripts/verify_release.py` |
| **App Store Connect (API-covered)** | `scripts/asc/*`, Fastlane iOS |

**Data Safety CSV**

1. Maintain `marketing/compliance/play_data_safety_source.json` from code/privacy evidence.
2. The workflow uses **`PLAY_DATA_SAFETY_CSV`**, committed `marketing/compliance/play_data_safety.csv`, or generated CSV from the source JSON.
3. Ensure **`GOOGLE_PLAY_JSON_KEY`** is set in Actions (same as other Play jobs).
4. Run workflow **Play Data Safety upload**. The workflow uploads sanitized CSV/evidence artifacts for read-back proof.

**Persona store growth**

- Google Play custom store listings are planned for fitness conditioning, combat sports, tactical/public-safety training, and developer/open-source traffic.
- Apple Custom Product Pages use the same persona split with campaign tokens and audience-specific copy.
- Daily growth publishing selects one persona topic per day, writes audience landing pages, and tracks UTM rows by persona campaign.

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
