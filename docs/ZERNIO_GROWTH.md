# Zernio growth orchestration

[Zernio](https://zernio.com) is a unified social API used here to **fan out** the same short message + blog link as the daily growth pipeline, without maintaining separate OAuth for each network in this repo.

## Local `.env`

Use either name (both are read):

- `ZERNIO_API_KEY=sk_...` (matches Zernio docs), or  
- `ZERNIO_TOKEN=sk_...` (alias only in this repo)

Optional for **live** posts (otherwise `sync-latest` logs `dry_run`):

- `ZERNIO_AUTO_PUBLISH=1`
- `ZERNIO_PUBLISH_ACCOUNTS` — JSON array of Zernio account targets, e.g.  
  `[{"platform":"twitter","accountId":"acc_xxx"},{"platform":"linkedin","accountId":"acc_yyy"}]`  
  Get `accountId` values from Zernio after connecting profiles (API: `GET /api/v1/accounts`).

## Commands

```bash
# Verify key and count connected accounts (no IDs printed)
uv run python scripts/zernio_orchestrate.py health --repo-root .

# Dry-run: append marketing/data/zernio_orchestration.jsonl with status dry_run
uv run python scripts/zernio_orchestrate.py sync-latest --repo-root . --output-root marketing --dry-run

# Live post (needs ZERNIO_AUTO_PUBLISH=1 and ZERNIO_PUBLISH_ACCOUNTS)
uv run python scripts/zernio_orchestrate.py sync-latest --repo-root . --output-root marketing
```

`--repo-root` must follow the subcommand (`health` / `sync-latest`).

## GitHub Actions

| Workflow | Role |
|----------|------|
| `zernio-growth-orchestration.yml` | Every **6 hours**: **health** check. **Run workflow** manually to run `sync-latest`. |
| `daily-growth-publishing.yml` | After `run-daily`, runs `sync-latest` (optional; `continue-on-error`). |

Repository secrets (Settings → Secrets):

- `ZERNIO_API_KEY` — same as local key  
- `ZERNIO_PUBLISH_ACCOUNTS` — JSON array (see above)  
- `ZERNIO_AUTO_PUBLISH` — set to `1` only when you want CI to call Zernio with `publishNow` (omit or leave empty for dry-run logging only)

Idempotency: the same `slug` is not published again within **36 hours** according to `marketing/data/zernio_orchestration.jsonl` on the checked-out branch (committed by the daily growth PR when present).

## Budget

Zernio is a **paid** vendor. Stay within the CTO operating budget in `CLAUDE.md` / `AGENTS.md` when enabling automation.
