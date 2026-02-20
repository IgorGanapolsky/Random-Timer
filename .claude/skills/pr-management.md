---
description: "Full PR & branch management cycle — audit open PRs, identify orphan branches, merge green PRs, delete stale branches, verify CI, and provide APK download link."
user-invocable: true
---

# PR Management & System Hygiene

Trigger: `/pr-management` or when user asks to review/merge PRs, clean branches, or get APK links.

## Process

### Step 1: Audit Open PRs

```python
import requests
TOKEN = '<use GITHUB_PAT from env or user>'
REPO = 'IgorGanapolsky/Random-Timer'
headers = {'Authorization': f'token {TOKEN}', 'Accept': 'application/vnd.github+json'}

# List all open PRs
resp = requests.get(f'https://api.github.com/repos/{REPO}/pulls?state=open&per_page=100', headers=headers)
prs = resp.json()

# For each PR, check CI status via check-runs
for pr in prs:
    sha = pr['head']['sha']
    checks = requests.get(f'https://api.github.com/repos/{REPO}/commits/{sha}/check-runs', headers=headers).json()
    # Report: PR number, title, branch, CI pass/fail/pending
```

Output a table: `| # | Title | Branch | CI Status |`

### Step 2: Identify Orphan Branches

```python
# List all branches
branches = requests.get(f'https://api.github.com/repos/{REPO}/branches?per_page=100', headers=headers).json()
pr_branches = {pr['head']['ref'] for pr in prs}
orphans = [b['name'] for b in branches if b['name'] not in pr_branches and b['name'] not in ('develop', 'main')]
```

### Step 3: Merge Green PRs

Only merge PRs where:
- All check-runs have `conclusion: success`
- No `REQUEST_CHANGES` reviews
- No merge conflicts

```python
requests.put(
    f'https://api.github.com/repos/{REPO}/pulls/{pr_number}/merge',
    headers=headers,
    json={'merge_method': 'squash'}
)
```

### Step 4: Delete Stale Branches

After confirming with user, delete orphan branches:
```python
requests.delete(f'https://api.github.com/repos/{REPO}/git/refs/heads/{branch}', headers=headers)
```

### Step 5: Get APK Artifact Link

After any PR is opened or merged to `develop`/`main`, CI generates a debug APK.

```python
# Find the CI run for the branch/PR
runs = requests.get(
    f'https://api.github.com/repos/{REPO}/actions/runs?branch={branch}&per_page=5',
    headers=headers
).json()['workflow_runs']

# Find CI workflow run (name="CI")
ci_run = next(r for r in runs if r['name'] == 'CI')

# Poll for app-debug artifact
artifacts = requests.get(
    f'https://api.github.com/repos/{REPO}/actions/runs/{ci_run["id"]}/artifacts',
    headers=headers
).json()['artifacts']

apk = next(a for a in artifacts if a['name'] == 'app-debug')
# Direct link: https://github.com/{REPO}/actions/runs/{ci_run['id']}/artifacts/{apk['id']}
```

**ALWAYS provide the direct APK download link to the user.** Format:
```
https://github.com/IgorGanapolsky/Random-Timer/actions/runs/<RUN_ID>/artifacts/<ARTIFACT_ID>
```

### Step 6: Verify CI on develop/main

```python
for branch in ['develop', 'main']:
    runs = requests.get(
        f'https://api.github.com/repos/{REPO}/actions/runs?branch={branch}&per_page=1',
        headers=headers
    ).json()['workflow_runs']
    # Report status and conclusion
```

## CI APK Artifact Facts

- **Workflow:** `.github/workflows/ci.yml` → `android` job
- **Trigger:** PR opened/updated against `develop` or `main`, or push to those branches
- **Artifact name:** `app-debug`
- **Artifact path:** `native-android/app/build/outputs/apk/debug/app-debug.apk`
- **The APK is available as soon as the android job completes** — no merge needed
- **Download:** GitHub UI (Actions → run → Artifacts) or API

## Completion Confirmation

When finished, state:
> **"Done merging PRs. CI passing. System hygiene complete. Ready for next session."**

Include evidence: branch count before/after, merged PR list, CI status, APK link.
