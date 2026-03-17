# SwiftUI-Agent-Skill

This repo supports an optional SwiftUI-only agent skill workflow based on Paul Hudson's open-source [`twostraws/SwiftUI-Agent-Skill`](https://github.com/twostraws/SwiftUI-Agent-Skill).

## Why This Exists

The highest-ROI use is iOS UI work:
- SwiftUI screen refactors
- paywall and setup screen cleanup
- iPhone/iPad layout polish
- accessibility and state-binding review before App Store screenshot capture

This integration is intentionally narrow. Do not use this skill for release, store publishing, CI repair, Android work, or production operations.

## Cost

The upstream skill is open source, so the repo-side adoption cost is `$0`.

## Install

Use the canonical task entrypoint:

```bash
make swiftui-skill-install
```

That installs the upstream `swiftui-pro` skill into `${CODEX_HOME:-~/.codex}/skills/swiftui-pro`.

## Verify

```bash
make swiftui-skill-verify
```

The verifier checks for:
- `SKILL.md`
- `agents/`
- `references/`

## Scope Rule

Use this skill only for:
- SwiftUI implementation
- SwiftUI review
- iOS visual polish

Keep release automation, store operations, analytics, and Android delivery in the repo's existing scripts and workflows.
