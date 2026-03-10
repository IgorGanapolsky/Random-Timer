# ASO Copy

## Purpose

Generate App Store and Play Store copy that improves conversion without inventing features or traffic claims.

## When To Use

Use for title, subtitle, short description, full description, keyword themes, and metadata refreshes before a release or ASO rotation.

## Inputs

- current platform: `iOS`, `Android`, or `Both`
- target audience and use case
- current product truth: supported features only
- latest North Star snapshot and activation metrics
- current store metadata to improve or replace
- top competitor positioning if available

## Prompt

```text
You are writing store metadata for Random Tactical Timer.

Goal:
- Increase qualified installs and improve open_to_completed_rate.

Truth constraints:
- Use only features that actually exist in the shipped app.
- Do not mention subscriptions, AI features, or integrations that are not live.
- Do not claim military, law-enforcement, or medical endorsement.

Audience:
- fighters, coaches, tactical athletes, HIIT users, and reaction-training users

Product truth:
- native iOS + Android random interval timer
- countdown, hidden mode, loop mode, alarm sound, optional voice countdowns and command cues
- built for reaction drills and stress conditioning

Task:
1. Write one App Store subtitle.
2. Write one Play short description.
3. Write one App Store / Play long description.
4. Provide a keyword theme list.
5. Explain why this copy should improve qualified conversion rather than vanity installs.

Tone:
- hard, precise, performance-oriented
- no hype slang
- no fake urgency

Metrics to optimize:
- open_to_completed_rate
- WQTU quality, not raw download volume

Current metrics and constraints:
{{metrics_and_constraints}}
```

## Guardrails

- Never say `AI` unless the shipped feature explicitly says `AI` in the product and copy review approves it.
- Never mention `monthly` or `annual` subscriptions if the app is one-time unlock.
- Never promise `scientifically proven`, `combat-tested`, or similar unsupported claims.
- Prefer concrete training outcomes over generic productivity language.

## Output

- one metadata block for `iOS`
- one metadata block for `Android`
- one keyword theme list
- one short rationale tied to activation quality
