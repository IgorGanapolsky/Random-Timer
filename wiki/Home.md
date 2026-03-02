# Random Tactical Timer — Wiki

Welcome to the Random Timer project wiki. These pages are **auto-updated daily** by GitHub Actions from live PostHog analytics and marketing pipeline data.

## Project Architecture

```mermaid
graph TD
    subgraph Apps
        A[Android<br/>Kotlin/Compose] -->|PostHog SDK| P[PostHog Analytics]
        I[iOS<br/>Swift/SwiftUI] -->|PostHog SDK| P
    end

    subgraph CI/CD
        GH[GitHub Actions] -->|assembleDebug| APK[Debug APK Artifact]
        GH -->|xcodebuild| IPA[iOS Build Check]
        GH -->|wiki-sync| W[GitHub Wiki]
    end

    subgraph Growth Automation
        GP[Content Pipeline] -->|daily| BLOG[Blog + Pages]
        ASO[ASO Rotation] -->|weekly| KW[App Store Keywords]
        ATT[Attribution Feedback] -->|weekly| UTM[UTM Reports]
        CRO[CRO Experiments] -->|weekly| AB[Store A/B Tests]
    end

    P -->|HogQL| ATT
    ATT -->|keyword feedback| ASO
    ATT -->|content feedback| GP
    GP -->|DEV.to + X| PUB[Cross-Platform Publishing]
```

## Budget Allocation

```mermaid
pie title Daily Ad Budget - $10/day
    "Apple Search Ads" : 6
    "Google UAC" : 4
```

## Navigation

### Analytics & Measurement
- [[Analytics Events Reference]] — Every PostHog event tracked across Android & iOS
- [[Attribution & UTM Pipeline]] — How marketing spend maps to installs and activation
- [[Onboarding Funnel]] — First Open → First Configure → First Complete conversion rates

### Growth Systems
- [[Growth Systems Overview]] — All automated growth pipelines and their schedules
- [[ASO Keyword Rotation]] — Weekly keyword performance and rotation history
- [[Review Velocity]] — App store review rates and prompt tuning
- [[CRO Experiments]] — A/B test proposals and results for store listings

### Campaign Performance
- [[Paid Acquisition]] — Apple Search Ads & Google UAC campaign configs and spend
- [[Referral & Content]] — Reddit, Product Hunt, blog outreach campaign status
- [[Content Pipeline]] — Daily blog publishing metrics and engagement

### Daily Dashboard
- [[Daily Metrics Dashboard]] — Auto-generated summary with live data from PostHog + marketing JSON

## Recent Cleanup (2026-02-23)

| Action | Branch | Result |
|--------|--------|--------|
| Merged | `fix/metadata-gaps` via PR #439 | Metadata sync rewrite + localized descriptions + A/B pilot |
| Deleted | `claude/power-button-silence-alarm-TxDrs` | Feature already on develop; overloaded branch removed |
| Deleted | `auto/growth-publishing-20260222-1331` | Auto-generated content with broken links |

**Repo health:** 2 core branches (`main`, `develop`), both CI green.

---

_Last synced by [`wiki-sync.yml`](https://github.com/IgorGanapolsky/Random-Timer/actions/workflows/wiki-sync.yml) workflow._
