# InsForge Runtime Config

This project uses InsForge as an optional runtime-config backend.

The app does not require InsForge to run. If the backend is unreachable, the
mobile clients fall back to bundled defaults and no experiments are assigned.

## Contract

- Project URL: `https://9gz9qqaz.us-east.insforge.app`
- Storage bucket: `training_assets`
- Object path: `runtime/mobile-runtime-config.json`

## Payload shape

The mobile apps expect the storage object to contain JSON like:

```json
{
  "configVersion": "2026-03-16",
  "defaultTimerConfig": {
    "minSeconds": 0,
    "maxSeconds": 300,
    "alarmDuration": 10,
    "hiddenMode": false,
    "repeatEnabled": false,
    "soundType": "intense",
    "volume": 0.5,
    "vibrationEnabled": false
  },
  "experiments": [
    {
      "key": "paywall_copy",
      "variants": [
        { "key": "control", "rolloutPercent": 50 },
        { "key": "drill_sergeant", "rolloutPercent": 50 }
      ]
    }
  ]
}
```

The app performs deterministic local assignment from the PostHog distinct ID, so
the backend only needs to ship experiment definitions and default values.
