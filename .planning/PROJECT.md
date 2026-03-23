# Monthly Content Refresh Pipeline

## What This Is

An automated pipeline that generates fresh voice callout packs and sound arsenal audio using Chatterbox TTS (open-source, MIT license), bundles them in biweekly app updates for both iOS and Android, and submits Apple Featuring Nominations with each content release. Zero monthly cost.

## Core Value

Pro subscribers receive fresh tactical voice callouts and alarm sounds every month, justifying their $29.99/yr subscription and driving retention through content variety.

## Requirements

### Validated

- ✓ Voice callout system with elapsed-time cues and command cues — existing
- ✓ Sound arsenal with 10 alarm sounds (Pro) — existing
- ✓ `voice_callouts.json` catalog format — existing
- ✓ MP3 audio bundled in both iOS and Android apps — existing
- ✓ CI/CD pipeline with TestFlight + Firebase distribution — existing
- ✓ Pro/free tier gating for voice callouts — existing

### Active

- [ ] Chatterbox TTS setup for local voice generation
- [ ] Voice pack generation script (command cues + elapsed milestones)
- [ ] Sound arsenal generation script (new alarm sounds)
- [ ] Audio validation CI step (format, duration, volume normalization)
- [ ] Catalog update automation (voice_callouts.json + Android equivalent)
- [ ] Release checklist with Apple Featuring Nomination step
- [ ] Monthly content calendar template
- [ ] Voice variety system (different drill sergeant personas)

### Out of Scope

- Remote/CDN content delivery — bundled updates provide ASO ranking benefit
- Real-time voice synthesis on device — pre-generated MP3 only
- User-generated content — curated packs only
- Paid TTS services (ElevenLabs, PlayHT) — Chatterbox is free and higher quality

## Context

- Chatterbox TTS by Resemble AI: MIT license, 350M params, beats ElevenLabs in blind tests (63.75% preference), runs locally on Mac
- Update recency is a confirmed ASO ranking signal on both stores
- Apple Featuring Nominations available via App Store Connect — each content release is a nomination opportunity
- Top 100 apps on Google Play update significantly more frequently than average
- Current audio: 41 MP3 files in `native-ios/RandomTimer/Resources/Audio/`
- Current catalog: `voice_callouts.json` with elapsedCues and commandCues

## Constraints

- **Budget**: $0/month for content generation (Chatterbox is free)
- **Timeline**: First content pack within 1 week
- **Storage**: App binary size must stay under 50MB
- **Format**: MP3, 16kHz+, mono, normalized to -14 LUFS
- **Parity**: Both iOS and Android get identical audio content
- **Quality**: Generated audio must sound professional (drill sergeant tone)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Chatterbox TTS over ElevenLabs | Free, MIT, better quality in blind tests | — Pending |
| Bundled delivery over CDN | ASO ranking benefit, offline reliability, zero infra | — Pending |
| Biweekly release cadence | Optimal for ASO, each update = featuring nomination | — Pending |
| Drill sergeant persona | Matches tactical timer brand identity | — Pending |

---
*Last updated: 2026-03-23 after initialization*
