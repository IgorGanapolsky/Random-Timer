# Google UAC Campaign Configuration - Random Tactical Timer

**Campaign Status:** Ready to Launch
**Last Updated:** 2026-02-23T00:00:00Z

---

## Campaign Overview

| Field | Value |
|---|---|
| Campaign Name | `RandomTacticalTimer_UAC_Installs_v1` |
| Campaign Type | App Installs (Universal App Campaign) |
| App Platform | Android + iOS |
| Android Package | `com.iganapolsky.randomtimer` |
| Play Store URL | https://play.google.com/store/apps/details?id=com.iganapolsky.randomtimer |
| App Store URL | https://apps.apple.com/app/random-tactical-timer/id6758355312 |
| Daily Budget | $10.00 USD |
| Campaign Total (30-day test) | $300.00 USD |
| Optimization Goal | Installs |

---

## Bidding Strategy

| Field | Value |
|---|---|
| Bid Strategy | Target CPI (Cost Per Install) |
| Target CPI | $2.50 USD |
| Maximum CPI Cap | $4.00 USD |
| Kill Threshold | $5.00 USD (pause if CPI exceeds this for 3+ consecutive days) |
| Target CPA (post-install) | $3.00 USD |

**Rationale:** Starting at $2.50 target CPI aligns with Reddit Ads benchmarks for the same app. Google UAC typically delivers 10-20% lower CPI than Reddit for app installs in the fitness/utilities category. The $4.00 cap prevents runaway spend during the learning phase.

---

## Ad Creative Assets

### Headlines (max 30 characters each)

| # | Headline | Chars | Angle |
|---|---|---|---|
| 1 | `Random Timer for HIIT & Drills` | 30 | Feature/use-case |
| 2 | `Tactical Timer - Train Smart` | 28 | Identity/positioning |
| 3 | `Surprise Interval Timer App` | 28 | Curiosity hook |
| 4 | `Random Countdown Timer` | 22 | Direct search match |

### Descriptions (max 90 characters each)

| # | Description | Chars | Angle |
|---|---|---|---|
| 1 | `Set a range, press start. You never know when it fires. Perfect for HIIT.` | 74 | How-it-works |
| 2 | `Unpredictable timer for workouts, drills & party games. No ads, no tracking.` | 77 | Broad appeal + privacy |
| 3 | `Keep sharp with random intervals. Used by athletes, coaches & gamers.` | 69 | Social proof |
| 4 | `Train reaction, not rhythm. Fires at random within your time range. Free.` | 74 | Value prop + free |

### Image Assets (from existing screenshots)

| Asset | Source Path (same as store / README) | Dimensions |
|---|---|---|
| Android Active | `native-android/fastlane/metadata/android/en-US/images/phoneScreenshots/2_active.png` | 1080x1920 recommended |
| Android Loop | `native-android/fastlane/metadata/android/en-US/images/phoneScreenshots/4_loop.png` | 1080x1920 recommended |
| Android Settings | `native-android/fastlane/metadata/android/en-US/images/phoneScreenshots/3_settings.png` | 1080x1920 recommended |
| iOS Active | `native-ios/fastlane/screenshots/en-US/2_active.png` | 1080x1920 recommended |
| iOS Running | `native-ios/fastlane/screenshots/en-US/4_running.png` | 1080x1920 recommended |
| iOS Setup | `native-ios/fastlane/screenshots/en-US/1_setup.png` | 1080x1920 recommended |

**Note:** Google UAC auto-generates video ads from image assets and Play Store listing. No separate video creative required at launch. Upload all 6 screenshots as portrait image assets.

---

## Targeting

### Locations (Primary Markets)

| Country | Code | Priority | Rationale |
|---|---|---|---|
| United States | US | Primary | Largest English-speaking market, highest combat sports audience |
| Canada | CA | Primary | Similar demographics, strong CrossFit/MMA community |
| United Kingdom | GB | Primary | Boxing culture, high smartphone penetration |
| Australia | AU | Primary | Combat sports culture, high app spend per capita |
| Germany | DE | Secondary | Added for broader reach, support `de` language |

### Languages

- English (`en`) -- primary
- German (`de`) -- secondary

### Audience Signals

Google UAC uses machine learning for targeting, but audience signals help guide the algorithm:

| Signal Type | Values |
|---|---|
| In-Market Audiences | Sports & Fitness > Exercise & Fitness; Sports & Fitness > Combat Sports |
| Affinity Audiences | Health & Fitness Buffs; Sports Fans > Combat Sports Fans |
| App Category Interest | Health & Fitness; Sports |
| Custom Intent Keywords | `reaction training`, `interval timer`, `tactical timer`, `random timer`, `boxing drills`, `HIIT timer`, `combat conditioning`, `sparring prep`, `workout timer`, `CrossFit timer` |
| Demographics | Ages 18-54, All genders |
| Device | Mobile only |
| Exclude | Existing installers |

### Keyword Themes (fed into UAC algorithm)

These keyword themes are derived from `marketing/keywords/strategy.json` and the existing `paid_campaigns.json` configuration:

1. `reaction training`
2. `interval timer`
3. `tactical timer`
4. `random timer`
5. `focus drills`
6. `combat conditioning`
7. `boxing drills`
8. `home workout timer`
9. `sparring prep`
10. `HIIT timer app`

### Negative Themes (to avoid wasted spend)

- `free timer online`
- `timer website`
- `countdown website`
- `clock widget`
- `egg timer`
- `pomodoro`
- `meditation timer`
- `sleep timer`
- `cooking timer`

---

## Google Ads Console Setup Instructions

### Step 1: Create the Campaign

1. Go to [Google Ads](https://ads.google.com) and sign in
2. Click **+ New Campaign**
3. Select campaign objective: **App promotion**
4. Select campaign subtype: **App installs**
5. Select platform: **Android** first (repeat for iOS as separate campaign)
6. Search for app: `com.iganapolsky.randomtimer` (or paste Play Store URL)
7. Campaign name: `RandomTacticalTimer_UAC_Installs_v1`
8. Click **Continue**

### Step 2: Budget and Bidding

1. Set daily budget: **$10.00**
2. Bidding strategy: **Target cost per install**
3. Target CPI: **$2.50**
4. Campaign optimization: **Install volume**
5. Start date: Set to your desired launch date
6. End date: Leave open (manual monitoring with kill threshold at $5.00 CPI)

### Step 3: Campaign Settings

1. Locations: Add **United States, Canada, United Kingdom, Australia, Germany**
2. Languages: Select **English** and **German**
3. Exclude existing users: **Yes** (toggle on "Exclude people who have your app installed")

### Step 4: Ad Assets

**Headlines** (add all 4):
1. `Random Timer for HIIT & Drills`
2. `Tactical Timer - Train Smart`
3. `Surprise Interval Timer App`
4. `Random Countdown Timer`

**Descriptions** (add all 4):
1. `Set a range, press start. You never know when it fires. Perfect for HIIT.`
2. `Unpredictable timer for workouts, drills & party games. No ads, no tracking.`
3. `Keep sharp with random intervals. Used by athletes, coaches & gamers.`
4. `Train reaction, not rhythm. Fires at random within your time range. Free.`

**Images**: Upload all 6 screenshots from **Fastlane paths** in the table above (portrait orientation, 1080×1920 recommended).

**Video**: Skip -- Google UAC will auto-generate from store listing assets

### Step 5: Audience Signals

1. Go to **Audience signals** section
2. Add In-Market: `Sports & Fitness > Exercise & Fitness`, `Sports & Fitness > Combat Sports`
3. Add Affinity: `Health & Fitness Buffs`, `Sports Fans > Combat Sports Fans`
4. Add Custom Segments: Create a custom segment with the 10 keyword themes listed above
5. Demographics: Ages **18-54**, All genders
6. Devices: **Mobile** only

### Step 6: Review and Launch

1. Review all settings in the campaign summary
2. Confirm budget ($10/day), target CPI ($2.50), locations, and ad assets
3. Click **Publish Campaign**
4. Note the Campaign ID for tracking

### Step 7: iOS Campaign (Duplicate)

1. Repeat Steps 1-6 but select **iOS** as the platform
2. Search for app: `Random Tactical Timer` or paste App Store URL
3. Campaign name: `RandomTacticalTimer_UAC_iOS_Installs_v1`
4. Use identical budget, bidding, targeting, and ad assets
5. Split budget: $5/day Android, $5/day iOS (or $10/day each if total budget allows)

---

## Optimization Plan

| Phase | Timeline | Actions |
|---|---|---|
| Learning Phase | Days 1-7 | Let UAC algorithm learn. Do NOT adjust bids or budget. Monitor CPI daily. |
| First Optimization | Day 8 | If CPI > $4.00, reduce target CPI to $2.00. If CPI < $2.00, increase budget to $15/day. |
| Creative Review | Day 10 | Check asset performance report. Remove underperforming headlines/descriptions (CTR < 0.5%). |
| Scale or Kill | Day 14 | If CPI < $3.00, scale budget to $20/day. If CPI > $5.00 for 3+ consecutive days, pause campaign. |
| Steady State | Days 15-30 | Weekly optimization. Add new headlines based on top-performing themes. Test new image assets. |

## KPIs

| Metric | Target | Kill Threshold |
|---|---|---|
| Cost Per Install (CPI) | $2.50 | > $5.00 for 3+ days |
| Click-Through Rate (CTR) | > 1.0% | < 0.3% |
| Install Rate (CVR) | > 25% | < 10% |
| Day-1 Retention | > 40% | < 20% |
| Day-7 Retention | > 15% | < 5% |

---

## Tracking and Attribution

| Tool | Purpose |
|---|---|
| Firebase + Google Analytics | Install attribution, in-app events |
| Google Ads Conversion Tracking | CPI measurement, conversion value |
| PostHog | In-app engagement and retention analytics |
| UTM Parameters | `utm_source=google&utm_medium=uac&utm_campaign=installs_v1` |

---

## Cross-Channel Budget Summary

| Channel | Daily Budget | Status |
|---|---|---|
| Apple Search Ads | $10.00 | Draft |
| Google UAC | $10.00 | Ready to Launch |
| Reddit Ads | $10.00 | Ready to Launch |
| **Total** | **$30.00** | |
