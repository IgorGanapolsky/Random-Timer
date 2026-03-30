# Android Firebase Infrastructure

This document is the canonical reference for Android Firebase wiring in Random Tactical Timer.

## Current Split

Android Firebase is intentionally split across two projects:

| Purpose | Project ID | Project Number | App ID |
|---|---|---:|---|
| Runtime services (`google-services.json`, Crashlytics BigQuery export) | `random-timer-486213` | `624873778337` | Runtime app ID is supplied by `GOOGLE_SERVICES_JSON` |
| Firebase App Distribution | `random-timer-dist-20260323` | `712918404489` | `1:712918404489:android:5fb1dfde1d712f53e7a558` |

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

- `https://console.firebase.google.com/project/random-timer-dist-20260323/appdistribution/app/android:com.iganapolsky.randomtimer`

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

for url in [
    "https://firebaseappdistribution.googleapis.com/v1/projects/712918404489/groups",
    "https://firebaseappdistribution.googleapis.com/v1/projects/712918404489/testers",
    "https://firebaseappdistribution.googleapis.com/v1/projects/712918404489/apps/1:712918404489:android:5fb1dfde1d712f53e7a558/releases",
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

First healthy Android Firebase release on the new backend:

- GitHub Actions run: `23440692946`
- Version: `1.3.9`
- Build version: `1773900000`
- Firebase release resource:
  - `projects/712918404489/apps/1:712918404489:android:5fb1dfde1d712f53e7a558/releases/28u136g4k64ag`

## Change Rules

When touching Android Firebase infrastructure:

1. Verify whether the change is for runtime Firebase or App Distribution.
2. Do not assume both paths share the same Firebase project.
3. Before claiming success, prove:
   - the GitHub distribution run is green
   - the App Distribution release exists via API read-back or Firebase console URL
   - the target group or testers exist in the active App Distribution project
