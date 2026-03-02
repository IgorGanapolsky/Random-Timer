# Crashlytics Check Skill

Trigger: `/crashlytics` or when user asks about crashes, stability, crash-free rate

## Description

Query Firebase Crashlytics crash data via BigQuery streaming export. Reports crash-free rate, top crashes, and affected users.

## Prerequisites

- `gcloud` CLI authenticated (`gcloud auth list`)
- Firebase Crashlytics BigQuery streaming export enabled
- BigQuery dataset: `firebase_crashlytics` in project `random-timer-486213`

## Workflow

1. **Run the check script**

   ```bash
   python3 scripts/check_crashlytics.py --hours 24 --threshold 99.0
   ```

2. **For longer lookback (7 days)**

   ```bash
   python3 scripts/check_crashlytics.py --hours 168 --threshold 95.0
   ```

3. **If no BigQuery tables exist yet**

   Tables auto-create when the first crash event streams. This means either:
   - Streaming export was just enabled (wait for next crash event)
   - Zero crashes (good!)

4. **To query raw crash data directly**

   ```bash
   bq query --use_legacy_sql=false \
     "SELECT exception_type, exception_message, COUNT(*) as count
      FROM \`random-timer-486213.firebase_crashlytics.com_iganapolsky_randomtimer\`
      WHERE event_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
        AND error_type = 'FATAL'
      GROUP BY exception_type, exception_message
      ORDER BY count DESC
      LIMIT 10"
   ```

## Key Info

- Project: `random-timer-486213`
- Android App ID: `1:624873778337:android:4503588605a3273edc14e0`
- Package: `com.iganapolsky.randomtimer`
- BQ Dataset: `firebase_crashlytics`
- BQ Table: `com_iganapolsky_randomtimer`
