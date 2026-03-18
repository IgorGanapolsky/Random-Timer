# Agentic Browser Platform Evaluation (2026-02-16)

## Scope
Evaluate these options for autonomous publishing/store-console automation:

1. Fiverr MCP/SDK
2. Cloudflare Workers + Browser Rendering
3. `vercel-labs/agent-browser`
4. Gemini API Computer Use

## Findings

### 1) Fiverr MCP/SDK
- Official Fiverr Developers page currently promotes waitlist/join flow and no production-ready MCP/browser automation SDK path was found for this use case.
- Result: not actionable as a primary automation engine for this repository today.

Sources:
- https://developers.fiverr.com/

### 2) Cloudflare Workers + Browser Rendering
- Official docs confirm Browser Rendering supports Playwright/Puppeteer automation in Cloudflare infrastructure.
- Cloudflare Sessions API can persist state across requests (useful for authenticated flows).
- Operationally strong for remote execution, but introduces additional infra coupling (Workers, Cloudflare account/runtime config) for a workflow that already runs locally and in GitHub Actions.

Sources:
- https://developers.cloudflare.com/browser-rendering/
- https://developers.cloudflare.com/browser-rendering/platform/playwright/
- https://developers.cloudflare.com/browser-rendering/workers-bindings/reuse-sessions/

### 3) `vercel-labs/agent-browser`
- Official repository provides a CLI designed for agent workflows (`open`, `snapshot`, `click`, `fill`, `eval`, `--state`, session controls).
- Already installable and runnable in our existing environment with no extra cloud service dependency.
- Directly compatible with our existing Playwright storage-state JSON files.

Sources:
- https://github.com/vercel-labs/agent-browser

### 4) Gemini API Computer Use
- Official docs describe Computer Use as a preview capability with strong safety guidance.
- Powerful for generalized UI tasks, but introduces model/API dependency and preview-surface risk for release-critical deterministic checks.

Sources:
- https://ai.google.dev/gemini-api/docs/computer-use

## Decision
Use a dual-engine model now:

1. Keep Playwright test suite as primary deterministic engine.
2. Add `agent-browser` as secondary independent verifier for store-console checks.

Rationale:
- Immediate execution in current toolchain.
- Cross-engine validation reduces single-framework blind spots.
- No additional cloud runtime required for baseline operation.

## Executed in Repo
- Added `agent-browser` verification script:
  - `tests/playwright/scripts/verify-store-console-agent-browser.mjs`
- Added npm script:
  - `test:console:agent-browser`
- Added Make target:
  - `playwright-store-console-agent`
- Updated scheduled store verification workflow to run both engines:
  - Playwright + agent-browser
- Added install guidance:
  - `npm install -g agent-browser@0.10.0`

