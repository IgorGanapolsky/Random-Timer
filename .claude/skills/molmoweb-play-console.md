---
name: molmoweb-play-console
description: Use MolmoWeb for visual Google Play Console inspection and evidence, then hand off real mutations to the Play Console API skill.
user_invocable: true
---

# MolmoWeb Play Console

Use this when Claude needs to inspect Google Play Console pages in a browser and capture proof before or after a publishing action.

## When To Use

- Confirm release status visually
- Inspect policy warnings, rollout state, screenshots, or blockers
- Capture HTML trajectory evidence for a console flow
- Verify what the browser UI currently shows before calling the API-backed publish tooling

## Execution Pattern

1. Use `molmoweb-browser-verify` with a concrete read-only query about the currently open Play Console flow.
2. Save the resulting HTML trajectory under `evidence/molmoweb/`.
3. Use `play-console` for actual publish-track, listing, or monetization mutations.
4. Optionally run `molmoweb-browser-verify` again for post-change visual confirmation.

## Example Prompts

- `Use molmoweb-play-console to inspect the current production rollout state and save evidence.`
- `Use molmoweb-play-console to verify whether the Random Timer listing has any visible policy blockers.`

## Rule

- Do not rely on MolmoWeb browser clicks for the final destructive publish step when an API/script path already exists in this repo.
