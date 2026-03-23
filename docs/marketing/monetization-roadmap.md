# Monetization Roadmap (March 2026)

## North Star And Constraints

- Business goal: `$100/day` after tax.
- Product North Star: `WQTU` (distinct users with >= 3 `timer_completed` events in trailing 7 days).
- Current live snapshot (2026-03-02): `WQTU=0`, `paid_distinct_users_30d=0`, active paid campaign present, no-scale lock active.
- Execution rule: do not scale paid spend while no-scale lock is active.

---

## Offer Architecture (Now)

One visible premium offer in paywall:
- `Pro` annual subscription (single CTA, no plan picker in paywall UI).
- All premium features included in Pro:
  - Full sound arsenal.
  - Extended training range to 60 minutes.
  - Elapsed-time voice callouts.
  - Monthly Pro audio pack refreshes.
  - Future advanced training modules.

Backward compatibility:
- Legacy SKUs can remain recognized for existing buyers.
- Only one premium SKU should be actively merchandised in paywall.

---

## Price Strategy

Anchor price for premium SKU:
- `Pro = $29.99/year` (default decision as of March 2026).

Rationale:
- Supports premium positioning with one visible offer.
- Improves chance of hitting `$100/day` without unrealistic daily unit volume.

Rough net math (assumes 15% store fee, then 30% tax):
- `$4.99` gross -> `~$2.97` net -> needs `~34 sales/day`.
- `$29.99` gross -> `~$17.84` net -> needs `~6 sales/day`.
- `$39.99` gross -> `~$23.79` net -> needs `~5 sales/day`.

Price test ladder:
1. Start at `$29.99/year`.
2. After >= 200 paywall views, if conversion is strong, test `$39.99/year`.
3. If conversion is weak, test `$19.99/year` before cutting below that.

---

## 30-Day GSD Plan

Week 1:
- Ensure store-side IAP prices match strategy (App Store Connect + Play Console).
- Verify one-offer paywall is live on both platforms.
- Confirm analytics events fire for:
  - `paywall_viewed`
  - `paywall_purchase_attempt`
  - `paywall_purchase_success`
  - `timer_completed` with entitlement level

Week 2:
- Fix attribution hygiene so paid traffic maps to users/events.
- Run no-scale lock check daily until paid attribution is non-zero.

Week 3:
- Improve activation path from open -> first completion.
- Target `open_to_completed_rate >= 25%`.

Week 4:
- Re-evaluate price using actual conversion and retained usage:
  - paywall conversion
  - `WQTU`
  - paid-attributed user quality

---

## Guardrails

- Do not increase paid budget while:
  - `paid_distinct_users_30d == 0` and
  - active campaign signal exists.
- Do not claim North Star progress from installs alone.
- Always report:
  - live `WQTU`
  - current target (`>=8` by 2026-03-31)
  - paid attribution status

---

## Anti-Patterns

- Do not run split tiers in paywall copy if product strategy is single-Pro.
- Do not keep stale pricing docs (`$4.99 one-time`) once premium subscription is live.
- Do not scale acquisition before measurement is trustworthy.
