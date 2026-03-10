# Sentry Incident Sync

This repository uses GitHub Issues as the durable incident queue for Sentry-driven operational alerts.

## What It Does

- Polls Sentry for unresolved issues within a configurable lookback window
- Filters out obvious test and QA-only crashes
- Promotes high-signal issues into GitHub incident issues
- Updates existing incidents when Sentry evidence changes
- Closes GitHub incidents when the Sentry issue no longer matches the sync criteria

## High-Signal Rules

- Always promote monetization failures such as billing, paywall, subscription, and Pro unlock issues
- Always promote alarm, notification, timer, audio, and voice callout regressions
- Always promote fatal and crash-class stability failures
- Ignore known test noise such as QA menu crash triggers
- Promote generic issues only when they exceed both event and affected-user thresholds

## Runtime Inputs

- `SENTRY_AUTH_TOKEN`
- `SENTRY_ORG`
- `SENTRY_PROJECT` (optional but recommended)
- `GITHUB_TOKEN`
- `GITHUB_REPOSITORY`

Optional tuning:

- `SENTRY_INCIDENT_LOOKBACK_DAYS`
- `SENTRY_INCIDENT_MIN_EVENTS`
- `SENTRY_INCIDENT_MIN_USERS`
- `SENTRY_INCIDENT_MAX_ISSUES`

## Workflow

- Workflow file: `.github/workflows/sentry-incident-sync.yml`
- Script: `scripts/sentry_incident_sync.py`
- Artifact: `sentry-incident-sync-report`

## Current Constraint

The repository currently does not contain a verified native Sentry SDK integration for Random Timer, so this sync path is ready for a real project configuration but may no-op until a repo-specific Sentry project is emitting events.
