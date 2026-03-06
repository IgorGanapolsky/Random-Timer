# High-ROI Revenue Research (Target: $100/Day After-Tax)

## Objective
The primary business objective is to achieve **$100/day after-tax revenue** (~$140/day gross, or ~$4,200/mo) from Random Tactical Timer.

## Core Financial Model
At an average subscription value of $20/year, we need 7 new subscribers a day, or roughly 210 new subscribers a month. Assuming a 5% free-to-paid conversion rate, we need 4,200 MAUs. 

## High-ROI Initiatives (GSD Sprint)

### 1. Unified Yearly Subscription (iOS & Android Parity)
- **Problem**: Android currently uses a one-time purchase (`pro_base`) and a monthly sub (`elite_tactical`), while iOS uses a yearly auto-renewing sub (`ProManager.eliteProductID`). 
- **ROI**: High. Yearly subscriptions maximize Day-0 cash flow and significantly increase LTV compared to a $5 one-time unlock. 
- **Action**: Update `PaywallSheet.kt` and `ProManager.kt` on Android to exclusively offer the Elite Yearly Subscription, matching iOS exactly. Remove `pro_base`.

### 2. Aggressive Review Prompting
- **Problem**: Organic discovery is driven by App Store / Play Store rating velocity. The current prompt threshold is too slow (3 completions).
- **ROI**: High. More 5-star ratings -> Higher ranking -> More organic DAU.
- **Action**: Lower the in-app review prompt threshold from 3 timer completions to 1. Implement this in both Android (`TimerViewModel` / `TrainingStatsService`) and iOS (`TimerManager` / `AppStoreReviewManager`).

### 3. Add Loop Mode Tooltip / Smart Defaults
- **Problem**: Users are not understanding the unique value prop (the unpredictable interval loop).
- **ROI**: High. D7 Retention increases when users activate Loop mode.
- **Action**: Change the default timer range from (0-5m) to smart defaults (10s-30s), and default the Loop mode to `true` on fresh installs, as outlined in the original North Star strategy.

### 4. Remove Dead Code
- **Problem**: Cluttered payload hinders iteration speed.
- **ROI**: Medium. Maintenance velocity.
- **Action**: Scan for and remove orphaned UI components, legacy subscription code, and unused assets.

## Execution Framework (Ralph Mode & Ultrawork)
- [ ] Task 1: Update Android Pricing Model to Yearly Sub only.
- [ ] Task 2: Lower Review Prompt to 1 completion (iOS & Android).
- [ ] Task 3: Set Smart Defaults (10-30s) & Loop=True on fresh installs.
