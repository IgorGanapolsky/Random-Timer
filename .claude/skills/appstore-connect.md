# App Store Connect Skill

Trigger: `/asc` or when user asks about iOS IAP, App Store, TestFlight, iOS publishing

## Description

Manage App Store Connect operations: IAP products, builds, TestFlight, and app metadata via ASC API v2.

## Prerequisites

- ASC API Key: `~/.appstoreconnect/private_keys/AuthKey_$APPSTORE_KEY_ID.p8`
- Key ID: `$APPSTORE_KEY_ID` (from `.env` APPSTORE_KEY_ID)
- Issuer ID: `$APPSTORE_ISSUER_ID` (from `.env` APPSTORE_ISSUER_ID)
- App ID: `6758355312`
- Requires `PyJWT` pip package

## JWT Generation

```python
import jwt, time

KEY_ID = '$APPSTORE_KEY_ID'
ISSUER_ID = '$APPSTORE_ISSUER_ID'

with open('~/.appstoreconnect/private_keys/AuthKey_$APPSTORE_KEY_ID.p8') as f:
    private_key = f.read()

now = int(time.time())
payload = {'iss': ISSUER_ID, 'iat': now, 'exp': now + 1200, 'aud': 'appstoreconnect-v1'}
token = jwt.encode(payload, private_key, algorithm='ES256', headers={'kid': KEY_ID, 'typ': 'JWT'})
```

## Operations

### Check IAP Status

```python
# GET /v2/inAppPurchases/{id}
# IAP ID: 6759628171 (com.iganapolsky.randomtimer.pro)
url = 'https://api.appstoreconnect.apple.com/v2/inAppPurchases/6759628171'
```

### Create IAP Localization

```python
# POST /v1/inAppPurchaseLocalizations
# Relationship key: "inAppPurchaseV2" (NOT "inAppPurchase")
# Description max: 55 characters
body = {
    "data": {
        "type": "inAppPurchaseLocalizations",
        "attributes": {"locale": "en-US", "name": "Pro Upgrade", "description": "..."},
        "relationships": {
            "inAppPurchaseV2": {"data": {"type": "inAppPurchases", "id": "6759628171"}}
        }
    }
}
```

### Set IAP Price

```python
# POST /v1/inAppPurchasePriceSchedules
# $4.99 USA price point: eyJzIjoiNjc1OTYyODE3MSIsInQiOiJVU0EiLCJwIjoiMTAwNjIifQ
body = {
    "data": {
        "type": "inAppPurchasePriceSchedules",
        "relationships": {
            "inAppPurchase": {"data": {"type": "inAppPurchases", "id": "6759628171"}},
            "baseTerritory": {"data": {"type": "territories", "id": "USA"}},
            "manualPrices": {"data": [{"type": "inAppPurchasePrices", "id": "${price1}"}]}
        }
    },
    "included": [{
        "type": "inAppPurchasePrices", "id": "${price1}",
        "relationships": {
            "inAppPurchasePricePoint": {"data": {"type": "inAppPurchasePricePoints", "id": "PRICE_POINT_ID"}}
        }
    }]
}
```

### Upload Review Screenshot

1. Reserve: `POST /v1/inAppPurchaseAppStoreReviewScreenshots`
2. Upload chunks to presigned URL
3. Commit: `PATCH /v1/inAppPurchaseAppStoreReviewScreenshots/{id}` with `uploaded: true`

### Set Territory Availability

```python
# POST /v1/inAppPurchaseAvailabilities
# Set availableInNewTerritories: true + list all 175 territories
```

## API Gotchas

- Localizations use v1 endpoint with `inAppPurchaseV2` relationship key
- Price schedules use v1 `inAppPurchasePriceSchedules` (not `iapPriceSchedules`)
- Description max 55 chars for IAP localization
- JWT expires in 20 minutes — regenerate for long operations

## Key Info

- App ID: `6758355312`
- IAP ID: `6759628171` (com.iganapolsky.randomtimer.pro)
- IAP State: `READY_TO_SUBMIT`
- Price: $4.99 (175 territories)
- Team ID: `$APPSTORE_TEAM_ID`
