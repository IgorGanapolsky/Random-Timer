# Greptile free-only

CEO rule: **never pay for Greptile**. Paid/flex credits were a mistake.

Support guidance (Muzz Khan, Greptile): free tier works if reviews are disabled on
repos that generate charges — **private repos**, and **public repos with fewer
than 50 stars**. OSI-licensed public repos with **50+ stars** get an OSS grant
(100 free review credits each).

Settings: [When Greptile Reviews](https://app.greptile.com/hermes-mobile/-/settings/review#when-reviews)

## Binding policy

| Rule | Action |
|------|--------|
| Free tier only | Never add a payment method; never enable flex/paid credits |
| Private repos | Disable Greptile reviews (billable) |
| Public &lt; 50 stars | Disable Greptile reviews |
| Public ≥ 50 stars + OSI | Allowed under OSS grant |
| Filter | Prefer label `needs-greptile-review` only on free-eligible repos |
| Auto-review on every commit | Prefer off unless free credits remain and repo is eligible |

## Fitness

```bash
python3 scripts/greptile_free_only_gate.py --json
```

## Explicitly rejected

- Updating a Greptile payment method
- Flex / paid review credits
- Autoreview on private or under-50-star public repos
- Claiming “free” while a card is on file for Greptile
