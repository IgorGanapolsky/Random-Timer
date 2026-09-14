---
title: "[short problem name]"
date: "YYYY-MM-DD"
category: "bugfix|process|store|ci|product|ops"
tags: []
status: active
source_pr: ""
---

# [short problem name]

## Problem

What failed, for whom, and what wrong assumption agents/humans made. 2–5 sentences.

## What worked

The fix or workflow that actually resolved it (commands, files, gates). Prefer reproducible steps over narrative.

## Prevention

How the next agent avoids repeating this. Prefer a **gate**, skill rule, or CLAUDE.md / AGENTS.md bullet over “be careful.”

## Evidence

- Command / query / PR check that proves the fix:
- Merge SHA or CI URL (when shipped):
- Related artifacts (`marketing/data/*.json`, PostHog, store read-back):

## Non-goals

What this write-up does **not** claim (optional but preferred).
