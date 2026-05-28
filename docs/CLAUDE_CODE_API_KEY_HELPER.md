# Claude Code `apiKeyHelper` (Anthropic API key)

How Random Timer operators wire Claude Code to fetch an Anthropic API key from a secrets manager **without** storing the key in repo files, chat, or committed `settings.json`.

## Why

- **CI** uses `ANTHROPIC_API_KEY` from GitHub Actions secrets (`claude-review.yml`, `weekly-shared.yml`).
- **Local Claude Code** sessions should use the same pattern: a shell command prints the key to stdout; Claude Code sends it as `X-Api-Key` and `Authorization: Bearer`.
- Never commit API keys. Never paste keys into issues, PRs, or agent prompts.

Official reference: [Claude Code settings — `apiKeyHelper`](https://code.claude.com/docs/en/settings).

## Setup (one-time)

1. Copy the example script and make it executable (outside the repo if you prefer):

   ```bash
   cp .claude/scripts/get-anthropic-api-key.sh.example ~/.claude/get-anthropic-api-key.sh
   chmod 700 ~/.claude/get-anthropic-api-key.sh
   ```

2. Edit `~/.claude/get-anthropic-api-key.sh` to use **your** secret backend (1Password `op`, macOS Keychain, `gh secret` is **not** for local Claude — use a personal vault).

3. Add to **`~/.claude/settings.json`** (user scope — do not commit):

   ```json
   {
     "apiKeyHelper": "$HOME/.claude/get-anthropic-api-key.sh",
     "env": {
       "CLAUDE_CODE_API_KEY_HELPER_TTL_MS": "3600000"
     }
   }
   ```

   Optional project-local override in `.claude/settings.json` (committed) may set only the **path** to a script name, never the key value:

   ```json
   {
     "apiKeyHelper": ".claude/scripts/get-anthropic-api-key.sh.example"
   }
   ```

   Prefer the user-scope path above so the real script stays in `~/.claude/`.

4. Verify (sanitized — should print `sk-ant-…` length only):

   ```bash
   ~/.claude/get-anthropic-api-key.sh | wc -c
   claude /status
   ```

## TTL and caching

- `CLAUDE_CODE_API_KEY_HELPER_TTL_MS` controls how long Claude Code caches the helper output (default ~5 minutes).
- If TTL from `settings.json` is ignored on your Node/OS build, export the variable in the shell that launches `claude` (known upstream issue on some Node 24 / Windows builds).
- For long sessions, implement **idempotent caching inside the helper script** (file or keychain with mtime check) so repeated helper invocations do not hammer 1Password/AWS.

## Alternatives (no custom script)

| Backend | `apiKeyHelper` value |
|---------|----------------------|
| 1Password CLI | `op read op://Vault/Anthropic/api-key --no-newline` |
| AWS Secrets Manager | `aws secretsmanager get-secret-value --secret-id anthropic-api-key --query SecretString --output text` |

## Security

- Script must be mode `700` and owned by the CEO user.
- Do not log stdout from the helper.
- Rotate keys in the vault if a key ever appears in chat, CI logs, or a commit.
- Agents: use GitHub Actions secrets for CI; use `apiKeyHelper` for local Claude Code only.

## Related

- `docs/AUTONOMOUS_OPERATIONS.md` — 24/7 automation and CEO gates
- `CLAUDE.md` — CTO mandate and secret hygiene
- `.github/workflows/claude-review.yml` — PR review uses `secrets.ANTHROPIC_API_KEY`
