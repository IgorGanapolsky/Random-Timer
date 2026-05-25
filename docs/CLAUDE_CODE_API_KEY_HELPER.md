# Claude Code `apiKeyHelper` (Random Timer)

How to supply an **Anthropic API key** to Claude Code on the CEO machine without storing secrets in this repo. For API-billed Claude Code sessions (Console / direct API), not Claude.ai subscription login.

**Patterns:** Level 1 (local env file) and Level 2 (1Password `op read`), aligned with [Using 1Password to Manage Claude Code API Keys](https://blog.anchorline.io/p/using-1password-to-manage-claude) and [Claude Code authentication](https://code.claude.com/docs/en/authentication).

**Repo template (example only):** `.claude/scripts/get-anthropic-api-key.sh.example`  
**Live script (CEO machine, not committed):** `~/.claude/get-anthropic-api-key.sh`

---

## What this is / is not

| In scope | Out of scope |
|----------|----------------|
| Anthropic API key for Claude Code CLI (`apiKeyHelper`) | GitHub — still **`gh auth login`** / keyring; CI uses Actions secrets |
| Long local sessions (GSD, Ralph — `.claude/scripts/ralph-loop.sh`) | Storing keys in `settings.json`, `.env` in repo, or this doc |
| Refresh via `CLAUDE_CODE_API_KEY_HELPER_TTL_MS` | Replacing `ANTHROPIC_API_KEY` in GitHub Actions (`claude-review.yml`, etc.) |

---

## Credential priority (must unset env when using helper)

Claude Code picks auth in a fixed order. Relevant entries:

1. OAuth / subscription (if logged in)
2. **`ANTHROPIC_API_KEY` environment variable** — wins over `apiKeyHelper` when set (after any one-time approval in interactive mode)
3. **`apiKeyHelper` script stdout** — used when no env API key is active

**Rule:** If `apiKeyHelper` should be the source of truth, **unset** `ANTHROPIC_API_KEY` (and `ANTHROPIC_AUTH_TOKEN` if set) in the shell profile, direnv, and IDE-integrated terminals before starting Claude Code.

```bash
unset ANTHROPIC_API_KEY
unset ANTHROPIC_AUTH_TOKEN
```

Verify with **`/status`** inside Claude Code ([env var guidance](https://support.claude.com/en/articles/12304248-manage-api-key-environment-variables-in-claude-code)).

---

## Level 1 — Local env file (simple)

1. Copy the template and install on the CEO machine:

   ```bash
   cp .claude/scripts/get-anthropic-api-key.sh.example ~/.claude/get-anthropic-api-key.sh
   chmod +x ~/.claude/get-anthropic-api-key.sh
   ```

2. Create a **gitignored** env file (example path):

   ```bash
   mkdir -p ~/.config/random-timer
   # ~/.config/random-timer/anthropic.env — mode 600, never commit
   # ANTHROPIC_API_KEY=sk-ant-...
   ```

3. Point the script at that file (default in template: `CLAUDE_ANTHROPIC_ENV_FILE` or `~/.config/random-timer/anthropic.env`).

4. Wire `apiKeyHelper` in user settings (see [CEO `settings.json` snippet](#ceo-settingsjson-snippet) below).

---

## Level 2 — 1Password CLI (`op read`)

Requires [1Password CLI](https://developer.1password.com/docs/cli/) and `op signin` (or service account for automation).

1. Store the Anthropic API key in 1Password (item + field names are yours; use a private vault).

2. In `~/.claude/get-anthropic-api-key.sh`, set `ANTHROPIC_OP_REF` to your reference, e.g.:

   ```bash
   ANTHROPIC_OP_REF='op://Private/Anthropic API Key/credential'
   ```

   The template uses a **placeholder** `op://REPLACE/Vault/Item/credential` — replace before use.

3. Ensure the script is executable and `apiKeyHelper` points at it.

4. First Claude Code launch may prompt 1Password to unlock the vault (expected).

**Note:** Native `op://` in `settings.json` `env` is a separate upstream feature ([anthropics/claude-code#23642](https://github.com/anthropics/claude-code/issues/23642)); this repo standardizes on **`apiKeyHelper` + shell script** for portability today.

---

## Long Ralph / GSD loops — refresh TTL

By default, `apiKeyHelper` output is cached (~5 minutes) and refreshed on HTTP 401. For multi-hour Ralph loops (`.claude/scripts/ralph-loop.sh`, `.claude/skills/ralph-mode.md`), extend TTL in the **same shell** that launches Claude Code:

```bash
export CLAUDE_CODE_API_KEY_HELPER_TTL_MS=3600000   # 1 hour; adjust as needed
```

Optional: add to `~/.claude/settings.json` `env` block (no secret values):

```json
"env": {
  "CLAUDE_CODE_API_KEY_HELPER_TTL_MS": "3600000"
}
```

---

## CEO `settings.json` snippet

Observed on CEO machine: `~/.claude/settings.json` exists (hooks, statusLine, theme). **Merge** `apiKeyHelper`; do not remove existing keys.

Add (paths are examples — use your home directory):

```json
{
  "apiKeyHelper": "/Users/igorganapolsky/.claude/get-anthropic-api-key.sh",
  "env": {
    "CLAUDE_CODE_API_KEY_HELPER_TTL_MS": "3600000"
  }
}
```

If you already have `"env": { ... }`, merge keys into that object instead of duplicating `"env"`.

Claude Code reloads `apiKeyHelper` when settings change; restart the CLI if `/status` still shows the wrong method.

---

## Activation checklist (paths only)

| Step | Path / action |
|------|----------------|
| 1 | `cp` repo `.claude/scripts/get-anthropic-api-key.sh.example` → `~/.claude/get-anthropic-api-key.sh` |
| 2 | `chmod +x ~/.claude/get-anthropic-api-key.sh` |
| 3 | Configure Level 1 file **or** Level 2 `ANTHROPIC_OP_REF` inside that script |
| 4 | `unset ANTHROPIC_API_KEY` (and `ANTHROPIC_AUTH_TOKEN`) in profile / terminal |
| 5 | Add `"apiKeyHelper"` to `~/.claude/settings.json` (snippet above) |
| 6 | Run `claude`, then `/status` — expect API key via helper, not stray env |
| 7 | For Ralph: `CLAUDE_CODE_API_KEY_HELPER_TTL_MS` + `.claude/scripts/ralph-loop.sh` as today |

---

## Complements GSD / Ralph / CI

- **GSD / autonomous ops:** `docs/AUTONOMOUS_OPERATIONS.md` — scheduled work stays on GitHub Actions; local Claude Code uses this helper.
- **Ralph:** `ralph-loop.sh` does not read the API key; it only runs tests/checks. Claude Code sessions **driving** Ralph should use the helper + TTL above.
- **CI:** Workflows keep `secrets.ANTHROPIC_API_KEY`; no `apiKeyHelper` in CI.

---

## References

- [Claude Code authentication](https://code.claude.com/docs/en/authentication) — `apiKeyHelper`, `CLAUDE_CODE_API_KEY_HELPER_TTL_MS`
- [Manage API key environment variables](https://support.claude.com/en/articles/12304248-manage-api-key-environment-variables-in-claude-code)
- [1Password + Claude Code (Anchorline)](https://blog.anchorline.io/p/using-1password-to-manage-claude)
- Repo: `.claude/scripts/ralph-loop.sh`, `.claude/GSD.md`, `CLAUDE.md` (Claude Code line)
