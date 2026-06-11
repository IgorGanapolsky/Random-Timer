# Competition Warmup Experiment

Date: 2026-05-12

## Signal

Local evidence source:

```bash
pdftotext -layout smoothcomp.pdf -
```

The Smoothcomp event-weekend email tells athletes to plan the day, control weight, warm up twice, and use small reactive movements to stay sharp before match time. This is a high-intent context for Random Tactical Timer because the athlete already needs unpredictable cues but Smoothcomp owns only event logistics.

## Action

Add a zero-spend Competition Warmup preset:

- Range: 20-90 seconds
- Alarm: 5 seconds
- Repeat loop: on
- Vibration: on
- Sound: intense free-tier alarm

Store metadata now names the preset for BJJ, judo, wrestling, and event-day prep.

## Measurement

Primary success signal remains Weekly Qualified Training Users:

```sql
SELECT count(*)
FROM (
  SELECT person_id
  FROM events
  WHERE event = 'timer_completed'
    AND timestamp > now() - interval 7 day
  GROUP BY person_id
  HAVING count() >= 3
)
```

Supporting signal:

- `training_preset_applied` with `preset_id = 'competition_warmup'` on iOS and Android.
- Settings-change events showing 20-90 second ranges as a fallback sanity check.

Budget impact: `$0.00`.
