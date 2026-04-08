# Repository root layout

Canonical map for **top-level** folders and files. Prefer putting new work under `docs/`, `marketing/`, `native-ios/`, `native-android/`, or `scripts/` instead of inventing new root buckets.

## Native apps & automation (primary)

| Path | Role |
|------|------|
| `native-ios/` | SwiftUI iOS app, Xcode project, Fastlane metadata & **store screenshots** |
| `native-android/` | Kotlin/Compose app, Gradle, Fastlane Play metadata & images |
| `scripts/` | Python tooling, CI helpers, growth ops |
| `.github/` | Workflows, templates, bot config |
| `Makefile` | Day-to-day verify / platform tasks |
| `pyproject.toml`, `uv.lock` | Python env for `scripts/` |

## Product & policy docs

| Path | Role |
|------|------|
| `docs/` | Engineering docs, playbooks, ADR-style notes, **blog sources** under `docs/blog/` |
| `PRIVACY_POLICY.md`, `SECURITY.md`, `CONTRIBUTING.md`, … | Repo-standard files |
| `CLAUDE.md`, `AGENTS.md`, `GEMINI.md` | Operator / agent instructions |

## GitHub Pages (live site)

These paths back **https://igorganapolsky.github.io/Random-Timer/** (Jekyll-style layout). Do not delete casually without updating Pages config.

| Path | Role |
|------|------|
| `index.html`, `styles.css`, `robots.txt`, `sitemap.xml` | Site shell |
| `blog/`, `posts/` | Published posts + HTML |
| `wiki/` | Wiki-style markdown pages served on Pages |
| `support/`, `public/` | Static HTML helpers |
| `diagrams/` | Root SVGs referenced by some posts |
| `assets/` | e.g. social preview image |

**Note:** `docs/blog/posts/` may overlap thematically with `blog/`; Pages uses **`blog/`** at root, not `docs/blog/`.

## Marketing & growth

| Path | Role |
|------|------|
| `marketing/` | ASO, campaigns, referral copy, `marketing/site/` (generated site output from pipelines) |
| `content/` | Large assets (e.g. pro audio packs), not the app binary tree |
| `amp.json` | AMP / discovery config |

## Legacy / removed from git

| Path | Status |
|------|--------|
| `screenshots/` (root) | **Removed** — duplicate of Fastlane assets; use `native-ios/fastlane/screenshots/` and Android `phoneScreenshots/` only |
| Root `md/` | **Removed** — orphan copies; published markdown for the site lives under `marketing/site/` when generated |

## Local-only (must not be committed)

Typical machine state (see `.gitignore`): `.env`, `*.pem`, `.venv*`, `node_modules/`, `digest_errors.log`, `.coverage`, `AppStore*.mobileprovision` (profiles belong in Keychain / CI secrets, not git), Maestro output under `evidence/`.

## Dot-directories

Tooling: `.cursor/`, `.claude/`, `.codex/`, `.maestro/`, `.gemini/`, etc. Most are editor/agent config; some are partially gitignored (see `.gitignore`).
