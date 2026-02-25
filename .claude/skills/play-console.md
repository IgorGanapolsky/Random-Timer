# Play Console Skill

Trigger: `/play-console` or when user asks about Google Play, Android IAP, Play Store publishing

## Description

Manage Google Play Console operations: IAP products, builds, tracks, and listings via the Android Publisher API v3.

## Prerequisites

- Service account: `native-android/play-service-account.json`
- Service account email: `random-timer-publisher@random-timer-486213.iam.gserviceaccount.com`
- Package: `com.iganapolsky.randomtimer`
- Requires `google-api-python-client` and `google-auth` pip packages

## Operations

### List IAP Products

```python
from googleapiclient.discovery import build
from google.oauth2 import service_account

SA_PATH = 'native-android/play-service-account.json'
SCOPES = ['https://www.googleapis.com/auth/androidpublisher']
PACKAGE = 'com.iganapolsky.randomtimer'

creds = service_account.Credentials.from_service_account_file(SA_PATH, scopes=SCOPES)
service = build('androidpublisher', 'v3', credentials=creds)

# One-time products (IAP)
products = service.monetization().onetimeproducts().list(packageName=PACKAGE).execute()

# Subscriptions
subs = service.monetization().subscriptions().list(packageName=PACKAGE).execute()
```

### Create IAP Product

```python
result = service.monetization().onetimeproducts().batchUpdate(
    packageName=PACKAGE,
    body={
        "requests": [{
            "oneTimeProduct": {
                "packageName": PACKAGE,
                "productId": "pro_upgrade",
                "listings": [{
                    "languageCode": "en-US",
                    "title": "Pro Upgrade",
                    "description": "Unlock 10 sounds, 60-min range, all Pro features."
                }],
            },
            "updateMask": "listings",
            "regionsVersion": {"version": "2022/02"},
            "allowMissing": True
        }]
    }
).execute()
```

**Note**: Requires `com.android.vending.BILLING` in the uploaded APK manifest.

### Upload AAB to Track

```python
from googleapiclient.http import MediaFileUpload

edit = service.edits().insert(packageName=PACKAGE, body={}).execute()
edit_id = edit['id']

media = MediaFileUpload('app/build/outputs/bundle/release/app-release.aab',
                        mimetype='application/octet-stream')
upload = service.edits().bundles().upload(
    packageName=PACKAGE, editId=edit_id, media_body=media
).execute()

service.edits().tracks().update(
    packageName=PACKAGE, editId=edit_id, track='internal',
    body={'releases': [{'versionCodes': [str(upload['versionCode'])], 'status': 'draft'}]}
).execute()

service.edits().commit(packageName=PACKAGE, editId=edit_id).execute()
```

**Note**: Requires signing with upload keystore (SHA1: E1:B1:81:40:86:FE:29:32...).

### Check App Details

```python
edit = service.edits().insert(packageName=PACKAGE, body={}).execute()
details = service.edits().details().get(packageName=PACKAGE, editId=edit['id']).execute()
service.edits().delete(packageName=PACKAGE, editId=edit['id']).execute()
```

## Key Info

- Developer ID: `8239620436488925047`
- Upload key SHA1: `$UPLOAD_KEY_SHA1`
- Keystore: `~/.android/random-timer-upload*.keystore` (password in GitHub secrets)
- AAB only (APKs not allowed)
- Old `inappproducts` endpoint is deprecated — use `monetization().onetimeproducts()` instead
