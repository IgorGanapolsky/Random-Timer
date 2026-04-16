# Firebase Operations Skill

Trigger: `/firebase` or when user asks about Firebase, Analytics, Performance, Cloud Messaging

## Description

Manage Firebase project operations: Crashlytics, Analytics, Performance Monitoring, and project settings.

## Prerequisites

- `firebase` CLI: `npm install -g firebase-tools` (v15.4.0+)
- `gcloud` CLI authenticated
- Project: `random-timer-486213`

## Operations

### Project Info

```bash
firebase projects:list
# Project: random-timer-486213 (Random Timer)
# Project Number: 624873778337
```

### List Apps

```bash
gcloud firebase android apps:list --project=random-timer-486213
# App ID: 1:624873778337:android:4503588605a3273edc14e0 (com.iganapolsky.randomtimer)
# Debug: 1:624873778337:android:183a3725e3471a10dc14e0 (com.iganapolsky.randomtimer.debug)
```

### Upload Crashlytics Symbols

```bash
# After release build
firebase crashlytics:symbols:upload \
  --app=1:624873778337:android:4503588605a3273edc14e0 \
  native-android/app/build/outputs/mapping/release/mapping.txt
```

### Crashlytics BigQuery Query

```bash
# Top crashes last 7 days
bq query --use_legacy_sql=false \
  "SELECT exception_type, exception_message, COUNT(*) as count,
   COUNT(DISTINCT installation_uuid) as users
   FROM \`random-timer-486213.firebase_crashlytics.com_iganapolsky_randomtimer\`
   WHERE event_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
     AND error_type = 'FATAL'
   GROUP BY exception_type, exception_message
   ORDER BY count DESC LIMIT 10"
```

### App Distribution (internal-distribution workflow)

- **groups**: Use Firebase Console group alias (e.g. `internal-testers`). Set `vars.FIREBASE_INTERNAL_GROUPS`.
- **testers**: Comma-separated emails. Set `vars.FIREBASE_INTERNAL_TESTERS`.
- At least one required. Prefer **groups** (avoids 404 from unmatched tester emails).
- App ID format: `1:PROJECT_NUMBER:android:APP_ID` (e.g. `1:624873778337:android:4503588605a3273edc14e0`).
- To see group alias: Firebase Console → App Distribution → Testers & groups → select group.

### App Testing agent (Android, preview)

AI-guided tests via App Distribution + Test Lab devices. Canonical doc: `docs/FIREBASE_ANDROID_INFRASTRUCTURE.md` (App Testing agent section + troubleshooting). In-repo YAML: `firebase-apptesting/tests/`. Manual CI: `.github/workflows/firebase-app-testing-agent.yml`. Runner: `scripts/ci_firebase_apptesting_execute.sh` (uses `firebase --non-interactive -P <project_id from SA>`). If upload succeeds but **`createReleaseTest`** returns **403** on **`firebaseappdistribution.googleapis.com`**, grant **`roles/firebaseappdistro.admin`** to the CI SA (not a upload-only custom role). If the failure is on **Test Lab**, enable **Cloud Testing** + **Tool Results** APIs and grant **`roles/cloudtestservice.testAdmin`** (see doc).

### Automated Crash Check (CI)

```bash
python3 scripts/check_crashlytics.py --hours 24 --threshold 99.0
```

### Firebase REST API (with quota project header)

```python
import urllib.request, subprocess

token = subprocess.run(['gcloud', 'auth', 'print-access-token'],
                       capture_output=True, text=True).stdout.strip()

req = urllib.request.Request(url, headers={
    'Authorization': f'Bearer {token}',
    'x-goog-user-project': 'random-timer-486213',
})
```

## BigQuery Integration

- Dataset: `firebase_crashlytics` (US region)
- Streaming export: ENABLED (3 apps)
- Tables auto-create on first crash event
- Table name format: `com_iganapolsky_randomtimer` (dots replaced with underscores)

## Key Info

- Project ID: `random-timer-486213`
- Project Number: `624873778337`
- Android App ID: `1:624873778337:android:4503588605a3273edc14e0`
- Debug App ID: `1:624873778337:android:183a3725e3471a10dc14e0`
- Service Account: `random-timer-publisher@random-timer-486213.iam.gserviceaccount.com`
- gcloud accounts: `$GCP_USER_EMAIL`, `fastlane-deploy@...`
