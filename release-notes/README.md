# Versioned Release Notes

Each store release must have one canonical customer-facing note file:

- `release-notes/X.Y.Z.md`

Rules:

- The filename must match the app semantic version.
- The file must be committed before a `release/vX.Y.Z` or `hotfix/vX.Y.Z` branch can promote to `main`.
- Placeholder text such as `TODO` or `TBD` is rejected by CI.

This repo uses versioned release notes instead of `.changeset/` package fragments because Random Timer is a single consumer app, not a multi-package library monorepo.
