# Release 1.3.36 checklist (not published)

**Evidence (repo, 2026-05-21):** `native-android/app/build.gradle.kts` and iOS `MARKETING_VERSION` = **1.3.36** on `develop`. Public stores still serve **1.3.35** until this release ships.

## CEO sign-off required

- [ ] TestFlight internal distribution (`testflight-signoff` environment)
- [ ] Google Play / App Store production submit (no automation without explicit CEO approval)

## Pre-cut `release/v1.3.36`

- [ ] Cut `release/v1.3.36` from `develop`
- [ ] Changelogs: `native-android/fastlane/metadata/android/en-US/changelogs/*.txt`, `native-ios/fastlane/metadata/en-US/release_notes.txt`
- [ ] Store listing metadata present (title, descriptions, screenshots) per `CLAUDE.md`
- [ ] `workflow_dispatch` **native-release.yml** on release branch; verify build `processingState` / Play upload read-back

## Monetization verification (store ops + build)

- [ ] **Google Play:** products `pro_base`, `elite_tactical`, `elite_tactical_monthly` active and cleared for sale (PostHog shows high `billing_product_not_found` for monthly when missing)
- [ ] **App Store Connect:** `com.iganapolsky.randomtimer.pro`, `.elite`, `.pro.monthly` available; paywall CTA must not fire before StoreKit returns products (1.3.36 iOS fix)

## Post-release metrics

- [ ] Re-run `python3 scripts/wqtu_dashboard.py` and `python3 scripts/paywall_conversion_report.py` (live PostHog)
- [ ] `paywall_purchase_success` > 0 in trailing 7d after real purchases (proxy; not ledger revenue)
