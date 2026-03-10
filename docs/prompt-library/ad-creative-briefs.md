# Ad Creative Briefs

## Purpose

Generate creative briefs that focus on qualified users likely to complete timers, not low-intent traffic.

## When To Use

Use for Apple Ads themes, paid social hooks, referral experiments, and lightweight creative rotation under the budget cap.

## Inputs

- channel: `Apple Ads`, `Reddit`, `Meta`, or `Organic referral`
- audience segment
- current offer and paywall truth
- current performance baseline
- approved screenshots or product stills
- budget ceiling

## Prompt

```text
Create 3 ad creative briefs for Random Tactical Timer.

Business objective:
- Improve WQTU and qualified completions.

Budget:
- Respect a hard external spend cap of $10/month.
- Favor low-cost, high-intent experiments only.

Audience:
{{audience}}

Channel:
{{channel}}

Product truth:
- random reaction timer for combat sports, HIIT, tactical conditioning, and focus drills
- no fake sensors, no coaching marketplace, no subscription if it is not live

For each creative brief, include:
1. Hook
2. Visual direction
3. On-screen copy
4. CTA
5. Why this should attract qualified users instead of curiosity clicks
6. One failure mode to watch

Tone:
- direct
- tactical
- no cringe operator cosplay
- no fake masculinity nonsense
```

## Guardrails

- Do not use fear tactics, weapon imagery, or claims that violate ad-platform policy.
- Do not imply military affiliation.
- Do not frame the product as meditation, therapy, or medical treatment.
- Keep copy grounded in the real app UI and live offer.

## Output

- three briefs
- one recommended first test
- one metric watchlist for the channel
