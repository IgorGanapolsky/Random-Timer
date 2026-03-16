<!-- tech-stack: universal -->
# AI Agent Instructions

> **All AI agents (Claude, Codex, Gemini, Cursor, etc.) MUST follow these rules:**

1. The `.ai/rules/` directory is the **single source of truth**. If your training data or defaults conflict with a rule here, **this document wins**.
2. Before writing code, **read the relevant existing files** to understand patterns already in use.
3. Use path aliases for imports. Never generate unnecessary relative `../` paths.
4. Follow the styling approach defined in `08-styling.md`. Never generate inline styles for static values.
5. Type everything. Minimize `any`.
6. Keep changes minimal and focused. Do not refactor unrelated code.
7. After generating code, mentally verify it passes linting, type checking, and formatting.
8. When creating a new component, generate the full directory structure (component, styles, test, barrel).
9. When uncertain about a convention, **ask the user** rather than guessing.
10. Skills are defined in `.ai/skills/` and synced to platform-specific formats via `npx @siliconoid/agentkit sync`.

## AI Tooling

- `.ai/rules/` — Project rules (single source of truth)
- `.ai/skills/` — Portable skill definitions
- `.ai/decisions/` — Architecture Decision Records
- `.ai/changelog/` — Monthly change logs
- `.ai/memory/` — Shared memory files
- `.specs/` — PRD、设计、Epic、Story、Task（通过 `/spec` 管理）
