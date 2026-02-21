# Paid Acquisition

Campaign configurations for Apple Search Ads and Google Universal App Campaigns.

## Budget Allocation

| Platform | Daily Budget | Share |
|----------|:-----------:|:-----:|
| Apple Search Ads | $6.00 | 60% |
| Google UAC | $4.00 | 40% |
| **Total** | **$10.00/day** | 100% |

**Target CPA:** $3.00 | **Max CPT (Apple):** $1.50

## Apple Search Ads — 3 Ad Groups

### Exact Match (High-Intent)
Top 15 keywords with BID ≥ 60. Examples:
- `reaction timer app`, `random interval timer`, `tactical timer`, `hiit random timer`

### Search Match (Discovery)
Top 20 keywords with BID 40–60. Broad match for keyword discovery.

### Competitor/Brand
Top 10 commercial + tool intent keywords targeting competitor searches.

**Negative keywords:** `egg timer`, `kitchen timer`, `countdown timer free`, `clock`, `stopwatch`

## Google UAC

**Headlines:**
- Random Tactical Timer
- Unpredictable HIIT & Reaction Drills
- Train with Random Intervals

**Descriptions:**
- Set a random countdown. Train reaction time, run boxing drills, or play party games.
- The timer app that keeps you on edge. Random intervals for HIIT, martial arts, and more.

**Targeting:** US, GB, CA, AU, DE | **Optimization goal:** Installs

## Campaign Status

All campaigns currently in **draft** status. Activation requires:
1. Apple Search Ads account setup
2. Google Ads UAC account setup
3. Budget approval
4. App published to both stores

## Source Files

- `scripts/paid_acquisition_seed.py` — Campaign config generation
- `marketing/data/paid_campaigns.json` — Campaign data
- `.github/workflows/weekly-paid-acquisition.yml` — Thursday 12:00 UTC
