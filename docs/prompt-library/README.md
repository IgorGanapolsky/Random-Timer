# Prompt Library

This is the repo-native prompt library for the highest-ROI growth and release tasks in Random Tactical Timer.

It exists to keep prompt work:

- tied to the North Star metric instead of vanity content
- versioned in the repo
- cheap enough to fit the `$10/month` operating cap
- testable so the assets do not silently rot

## Packs

- `aso_copy`
- `ad_creative_briefs`
- `app_store_screenshot_prompts`
- `incident_summary_prompts`
- `release_notes_and_review_response_prompts`

## Usage

List packs:

```bash
python3 -m scripts.prompt_library --list
```

Get machine-readable output:

```bash
python3 -m scripts.prompt_library --list --format json
```

Show one pack:

```bash
python3 -m scripts.prompt_library --show aso_copy
```

## Contract

The manifest lives in `marketing/data/prompt_library.json`.

Each prompt pack must include the following sections:

- `## Purpose`
- `## When To Use`
- `## Inputs`
- `## Prompt`
- `## Guardrails`
- `## Output`

The contract is enforced by `scripts/tests/test_prompt_library.py`.
