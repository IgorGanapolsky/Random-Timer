# GitHub repository profile (About section)

Keep the **GitHub repo About** field aligned with **store listings** (canonical copy under Fastlane).

## Suggested short description (≤350 characters)

> Random Tactical Timer — random-interval training for MMA, BJJ, boxing, muay thai, kickboxing, HIIT, CrossFit, sparring, and tactical drills. iOS & Android. Same story as App Store / Play (en-US).

Tighter option:

> Train reaction, not rhythm. Random interval timer for MMA, BJJ, boxing, muay thai, kickboxing, HIIT, CrossFit, sparring, and tactical drills. Native iOS + Android.

**Keep this in sync with:**
- `native-ios/fastlane/metadata/en-US/subtitle.txt` (App Store subtitle)
- `native-android/fastlane/metadata/android/en-US/short_description.txt` (Play short description)
- `README.md` intro paragraph
- `marketing/keywords/strategy.json` `audience` field
- `marketing/site/agents.md` Intent.Audience
- `marketing/site/amp.json` + `marketing/product-pages/amp.json` `description` + `agentic_merchant_protocol.target_audiences`

## Website

Use the **marketing URL** from store metadata:

- `native-ios/fastlane/metadata/en-US/marketing_url.txt` (source of truth)

## Topics (GitHub limit: 20)

The repo is usually **at the 20-topic cap**. Swap topics with `gh api` / Settings rather than blindly `--add-topic`. Current set is visible via:

`gh api repos/IgorGanapolsky/Random-Timer/topics -H "Accept: application/vnd.github+json"`

## Store copy source of truth

| Store | en-US copy | Screenshots (same files README uses) |
|-------|------------|--------------------------------------|
| Apple | `native-ios/fastlane/metadata/en-US/` | `native-ios/fastlane/screenshots/en-US/` (`1_setup` … `4_running`, iPad `5_*`–`7_*`) |
| Google Play | `native-android/fastlane/metadata/android/en-US/` | `native-android/fastlane/metadata/android/en-US/images/phoneScreenshots/` |

When listings change, update **those paths first**; README only links to them.
