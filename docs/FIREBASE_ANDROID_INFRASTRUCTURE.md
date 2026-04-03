# Android Firebase Infrastructure

This document is the canonical reference for Android Firebase wiring in Random Tactical Timer.

## Current Split

Android Firebase is intentionally split across two backends:

| Purpose | Project ID | Project Number | App ID |
|---|---|---:|---|
| Runtime Android config in CI/release (`google-services.json` from secret) | Varies by secret | Varies | Supplied by `GOOGLE_SERVICES_JSON` |
| **Crashlytics → BigQuery streaming export** (automated queries / `check_crashlytics.py`) | **`random-timer-dist-new`** | Per GCP console | Same app; dataset `firebase_crashlytics` |
| Firebase App Distribution | `random-timer-dist-new` | Verify from `FIREBASE_ANDROID_APP_ID` secret or live run log | Supplied by `FIREBASE_ANDROID_APP_ID` |
| Legacy / historical project (some docs and older keys) | `random-timer-486213` | `624873778337` | Do not assume current BQ export lives here |

## Why The Split Exists

The original Firebase App Distribution backend in `random-timer-486213` became unrecoverable after project restore. The failure mode was:

```text
HTTP 400 FAILED_PRECONDITION
```

on App Distribution endpoints such as:

- `GET /v1/projects/624873778337/groups`
- `GET /v1/projects/624873778337/testers`

To restore Android internal distribution without blocking on Firebase support, App Distribution was moved to a clean Firebase project while runtime Firebase stayed on the existing production project.

## Secrets And Variables

These GitHub secrets drive Android App Distribution:

- `FIREBASE_ANDROID_APP_ID`
- `FIREBASE_SERVICE_ACCOUNT_JSON`

This GitHub secret drives runtime Crashlytics CI checks against the production
Firebase/BigQuery project:

- `CRASHLYTICS_SERVICE_ACCOUNT_JSON`

These GitHub variables drive the tester audience:

- `FIREBASE_INTERNAL_GROUPS`
- `FIREBASE_INTERNAL_TESTERS`

These secrets still drive runtime Firebase inside the Android build:

- `GOOGLE_SERVICES_JSON`

Do not rotate `GOOGLE_SERVICES_JSON` when working on App Distribution only. That
secret controls runtime Firebase services, not the App Distribution backend.

Do not reuse `FIREBASE_SERVICE_ACCOUNT_JSON` for Crashlytics stability checks.
That service account is for the separate App Distribution project. Runtime
Crashlytics CI must authenticate with `CRASHLYTICS_SERVICE_ACCOUNT_JSON`.

## What "Nothing In Firebase" Usually Means

If you look in `random-timer-486213`, you will not see current Android App Distribution releases anymore.

The current Android internal distribution console is:

- `https://console.firebase.google.com/project/random-timer-dist-new/appdistribution/app/android:com.iganapolsky.randomtimer`

If you are looking in an older Firebase App Distribution project, the console will appear empty even when GitHub Actions distribution succeeded.

## Verification Commands

### GitHub Actions Proof

```bash
gh run view 23440692946 --json status,conclusion,jobs
gh run view 23440692946 --log | rg "uploaded new release|distributed to testers/groups successfully"
```

### Service-Account API Read-Back

Use the App Distribution service account from `FIREBASE_SERVICE_ACCOUNT_JSON`, not local ADC:

```bash
python3 - <<'PY'
from google.oauth2 import service_account
from google.auth.transport.requests import Request
import os
import requests

key_path = os.environ["FIREBASE_SERVICE_ACCOUNT_JSON_PATH"]
creds = service_account.Credentials.from_service_account_file(
    key_path,
    scopes=["https://www.googleapis.com/auth/cloud-platform"],
)
creds.refresh(Request())
headers = {"Authorization": f"Bearer {creds.token}"}

project_number = os.environ["FIREBASE_PROJECT_NUMBER"]
app_id = os.environ["FIREBASE_ANDROID_APP_ID"]

for url in [
    f"https://firebaseappdistribution.googleapis.com/v1/projects/{project_number}/groups",
    f"https://firebaseappdistribution.googleapis.com/v1/projects/{project_number}/testers",
    f"https://firebaseappdistribution.googleapis.com/v1/projects/{project_number}/apps/{app_id}/releases",
]:
    resp = requests.get(url, headers=headers, timeout=30)
    print(resp.status_code, url)
    print(resp.text)
PY
```

## Current Group And Testers

- Group alias: `internal-testers`
- Testers:
  - `iganapolsky@gmail.com`
  - `ig5973700@gmail.com`

## Release Evidence

Most recent verified Android Firebase release evidence:

- GitHub Actions run: `23806206042`
- Version: `1.3.15`
- Build version: `504`
- Console project in live run log:
  - `random-timer-dist-new`
- Distribution audience in live run log:
  - tester `iganapolsky@gmail.com`

## Change Rules

When touching Android Firebase infrastructure:

1. Verify whether the change is for runtime Firebase or App Distribution.
2. Do not assume both paths share the same Firebase project.
3. Before claiming success, prove:
   - the GitHub distribution run is green
   - the App Distribution release exists via API read-back or Firebase console URL
   - the target group or testers exist in the active App Distribution project
