# Release Notes and Review Response Prompts

## Purpose

Generate concise release notes and store-review replies that reflect the actual shipped build and user complaint.

## When To Use

Use during release prep, App Store / Play metadata updates, or when answering user reviews after a fix lands.

## Inputs

- platform
- shipped changes only
- resolved complaints or bugs
- current version number
- review text if responding to a user

## Prompt

```text
Write release notes and, if needed, a store-review reply for Random Tactical Timer.

Version:
{{version}}

Platform:
{{platform}}

Shipped changes only:
{{shipped_changes}}

User complaint to respond to:
{{review_text}}

Requirements:
1. Release notes must be short, clear, and feature-truthful.
2. Review reply must acknowledge the issue, state what changed, and avoid overpromising.
3. If a complaint is not fixed, say so plainly and thank the user for the report.

Tone:
- calm
- direct
- respectful
- no marketing fluff
```

## Guardrails

- Never mention fixes that are not in the shipped build.
- Never promise timelines you cannot verify.
- Avoid defensive language in review responses.
- Keep release notes readable in short storefront fields.

## Output

- one short release-notes block
- one optional long release-notes block
- one review reply
