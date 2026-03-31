---
name: molmoweb-browser-verify
description: Run a real MolmoWeb browser-agent check against a running local MolmoWeb server and save an HTML trajectory under evidence/molmoweb/.
user_invocable: true
---

# MolmoWeb Browser Verify

Use this when you need browser-level proof for public Random-Timer surfaces such as:
- `index.html`
- `download/index.html`
- GitHub Pages flows
- marketing landing pages
- Google Play Console screens already reachable in the browser
- App Store Connect screens already reachable in the browser

## Prerequisites

- Local MolmoWeb checkout available at `MOLMOWEB_HOME` or `~/molmoweb`
- The wrapper auto-starts the local MolmoWeb server if `http://127.0.0.1:8001` is down
- Optional override: `MOLMOWEB_ENDPOINT` if you want the browser agent to hit a different local endpoint

## Canonical Invocation

```bash
python3 scripts/molmoweb_browser_verify.py \
  --query "Go to https://example.com and tell me the page title."
```

## Random-Timer Example

```bash
python3 scripts/molmoweb_browser_verify.py \
  --query "Go to https://igorganapolsky.github.io/Random-Timer/ and tell me the primary call to action."
```

## Output Contract

- Saves an HTML trajectory under `evidence/molmoweb/`
- Prints:
  - `TRAJ_HTML=...`
  - `STEPS=...`
  - `LAST_ERROR=...`
  - `LAST_PRED=...`

## Rules

- Prefer one concrete query at a time
- Save the trajectory and cite it as evidence
- Use this for proof, not for replacing deterministic test coverage
- For publish actions, pair this with the API-backed `play-console` or `appstore-connect` skill instead of relying on browser clicks for the final mutation
