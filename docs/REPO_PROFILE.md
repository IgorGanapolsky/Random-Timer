# GitHub repository profile (About section)

Keep the **GitHub repo About** field aligned with **store listings** (canonical copy under Fastlane).

## Suggested short description (≤350 characters)

> Random Tactical Timer — random-interval training for combat sports & HIIT. iOS & Android. Same story as App Store / Play (en-US).

Tighter option:

> Train reaction, not rhythm. Native iOS + Android random timer for combat sports, BJJ, boxing, and HIIT.

## Website

Use the **marketing URL** from store metadata:

- `native-ios/fastlane/metadata/en-US/marketing_url.txt` (source of truth)

## Suggested topics

`swift` `swiftui` `kotlin` `jetpack-compose` `timer` `hiit` `martial-arts` `mobile` `ios` `android` `storekit` `play-billing`

## Store copy source of truth

| Store | en-US copy | Screenshots (same files README uses) |
|-------|------------|--------------------------------------|
| Apple | `native-ios/fastlane/metadata/en-US/` | `native-ios/fastlane/screenshots/en-US/` (`1_setup` … `4_running`, iPad `5_*`–`7_*`) |
| Google Play | `native-android/fastlane/metadata/android/en-US/` | `native-android/fastlane/metadata/android/en-US/images/phoneScreenshots/` |

When listings change, update **those paths first**; README only links to them.
