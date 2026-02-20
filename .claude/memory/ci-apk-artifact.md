# CI APK Artifact — How to Get It

## Key Facts

- The **CI workflow** (`.github/workflows/ci.yml`) builds a debug APK on every PR and push to `develop`/`main`
- Artifact name: `app-debug` (contains `app-debug.apk`, ~15 MB)
- The APK is available **as soon as the android job completes** — no merge required, just opening a PR triggers it
- Artifact is uploaded via `actions/upload-artifact@v4`

## How to Retrieve the APK Link

Use GitHub API with the PAT:

```python
import requests, time

TOKEN = '<PAT>'
REPO = 'IgorGanapolsky/Random-Timer'
headers = {'Authorization': f'token {TOKEN}', 'Accept': 'application/vnd.github+json'}

# 1. Find the CI run for the branch
runs = requests.get(
    f'https://api.github.com/repos/{REPO}/actions/runs?branch={BRANCH}&per_page=5',
    headers=headers
).json()['workflow_runs']
ci_run = next(r for r in runs if r['name'] == 'CI')

# 2. Poll for artifact (CI takes ~2 min for android job)
for _ in range(20):
    artifacts = requests.get(
        f'https://api.github.com/repos/{REPO}/actions/runs/{ci_run["id"]}/artifacts',
        headers=headers
    ).json()['artifacts']
    apk = next((a for a in artifacts if a['name'] == 'app-debug'), None)
    if apk:
        link = f'https://github.com/{REPO}/actions/runs/{ci_run["id"]}/artifacts/{apk["id"]}'
        print(f'APK: {link}')
        break
    time.sleep(30)
```

## Direct Link Format

```
https://github.com/IgorGanapolsky/Random-Timer/actions/runs/<RUN_ID>/artifacts/<ARTIFACT_ID>
```

## MANDATORY Rule

**ALWAYS provide the user with the direct APK download link after creating a PR or pushing to develop/main.** Never tell the user to find it themselves.

## Lessons Learned

- 2026-02-20: Failed to provide APK link initially, told user to run commands. Violated "Act, Don't Instruct" rule. Fix: always poll CI via API and return the artifact link directly.
- `gh` CLI may not be available in cloud environments. Always fall back to `requests` + GitHub API.
- The git proxy in cloud env doesn't support GitHub API calls — use direct HTTPS to api.github.com with PAT.
