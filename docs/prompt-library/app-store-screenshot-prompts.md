# App Store Screenshot Prompts

## Purpose

Generate screenshot concepts and caption copy that match the real app screens and improve product-page clarity.

## When To Use

Use before App Store Connect or Play listing refreshes, screenshot reshoots, or localization work.

## Inputs

- platform and device class
- current screenshot set or UI captures
- live product truth
- primary objection to overcome
- target audience segment

## Prompt

```text
Design a screenshot set for Random Tactical Timer using only real shipped UI states.

Target platform:
{{platform}}

Device class:
{{device_class}}

Goal:
- Improve product-page understanding in under 3 screens.

Audience:
- fighters, coaches, tactical athletes, HIIT users

Required truths to communicate:
- random trigger within a chosen range
- fast setup
- stress-focused training utility
- lock-screen/background reliability if supported on the platform

For each screenshot:
1. screen name
2. headline
3. subheadline
4. visual focus
5. why this screen belongs in the sequence

Keep captions:
- under 7 words for headlines
- under 14 words for subheads
- hard and readable, not poetic
```

## Guardrails

- Do not invent screens or controls that are not in the app.
- Keep caption hierarchy readable at store screenshot scale.
- Do not overuse jargon like `operator`, `elite`, or `AI`.
- Avoid showing premium-locked states as the first screenshot unless the value proposition requires it.

## Output

- ordered screenshot plan
- caption set
- one suggested A/B test angle
