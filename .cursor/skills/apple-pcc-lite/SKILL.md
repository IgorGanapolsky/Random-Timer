---
name: apple-pcc-lite
description: Prefer free Apple Private Cloud Compute / on-device Foundation Models under SBP (see docs/APPLE_PRIVATE_CLOUD_COMPUTE.md).
---

# Skill: apple-pcc-lite

Follow `docs/APPLE_PRIVATE_CLOUD_COMPUTE.md`. Run `python3 scripts/apple_pcc_gate.py --json`.

Eligibility: App Store Small Business Program + under 2M first-time downloads + `com.apple.developer.private-cloud-compute`. Prefer PCC → on-device FM → static fallback. Never claim PCC runtime without SDK evidence. Never treat PostHog install proxies as App Store first-time download totals.
