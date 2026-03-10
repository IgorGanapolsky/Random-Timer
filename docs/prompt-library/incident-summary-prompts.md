# Incident Summary Prompts

## Purpose

Turn raw failures into clean engineering summaries that accelerate triage and prevent vague bug reports.

## When To Use

Use for Sentry issues, Crashlytics spikes, CI failures, bad beta feedback, or release regressions that need a GitHub issue or PR comment.

## Inputs

- source system: `Sentry`, `Crashlytics`, `GitHub Actions`, or `beta feedback`
- exact error text or failing check
- affected platform and build
- reproduction evidence if known
- blast radius: users, sessions, builds, or workflows affected

## Prompt

```text
Summarize this incident for Random Tactical Timer.

Objective:
- produce an engineer-ready summary with evidence and next action

Source:
{{source}}

Evidence:
{{raw_evidence}}

Known scope:
{{scope}}

Write:
1. one-sentence title
2. impact summary
3. likely root cause
4. exact evidence list
5. reproduction notes
6. containment / next fix step
7. user-facing risk if left unresolved

Tone:
- direct
- specific
- no hedging when evidence is explicit
- clearly mark inference vs proof
```

## Guardrails

- Quote exact errors sparingly and only when useful.
- Separate confirmed facts from hypotheses.
- Do not write generic RCA filler.
- Prefer next engineering action over vague ownership language.

## Output

- one GitHub issue body or PR comment
- one short executive summary
- one verification checklist for the fix
