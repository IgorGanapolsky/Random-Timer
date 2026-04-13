# Pro Monthly Audio Strategy

## Objective

Turn ElevenLabs into a recurring Pro content engine instead of a one-off asset generator.

## Ground Rules

- One canonical Marine-style drill-instructor voice.
- Rotate scripts monthly, not cloned identities.
- Elapsed cues must explicitly say `elapsed`.
- Avoid profanity, insults, and parody-sergeant language.
- Keep alarm sound types stable in the UI while allowing monthly asset overrides under the same `SoundType`.

## Current Pack Model

- Canonical source: `content/pro_audio/monthly_pro_audio_packs.json`
- Generated runtime files:
  - `content/pro_audio/runtime/latest.json`
  - `content/pro_audio/runtime/packs/<pack_id>/voice/*.mp3`
  - `content/pro_audio/runtime/packs/<pack_id>/sounds/*.mp3`
  - `native-ios/RandomTimer/Resources/Audio/voice_callouts.json`
  - `native-ios/RandomTimer/Resources/Audio/sound_arsenal.json`
  - `native-android/app/src/main/assets/voice_callouts.json`
  - `native-android/app/src/main/assets/sound_arsenal.json`

## Runtime Delivery

- iOS and Android now point to the same hosted runtime manifest:
  - `https://raw.githubusercontent.com/IgorGanapolsky/Random-Timer/develop/content/pro_audio/runtime/latest.json`
- Pro clients refresh the hosted manifest on entitlement restore, purchase, and app foreground.
- Hosted assets are cached locally and validated with SHA-256 before activation.
- Playback services prefer verified cached assets and fall back to bundled assets immediately if the runtime pack is missing, corrupt, or unavailable.
- This gives existing Pro users monthly audio refreshes without requiring a store build.

## Platform Limitation

- iOS local-notification custom sounds still must be bundled in the app.
- Monthly hosted sounds therefore cover:
  - foreground voice callouts
  - foreground sound previews
  - in-app alarm playback while the app is running
- Scheduled iOS notification sounds still use the bundled fallback sound names.

## Generation Workflow

The authoritative monthly workflow is `.github/workflows/generate-ios-voice-callouts.yml`.
It runs on the first day of each month, rolls the canonical manifest with
`scripts/roll_monthly_pro_audio_pack.py`, renders assets with ElevenLabs, verifies
freshness with `scripts/pro_audio_freshness.py --grace-day-limit 0`, opens a PR,
and enables auto-merge. The legacy failure-masking monthly workflow was removed.

Use `scripts/generate_pro_audio_content.py` to:

- export generated platform catalogs from the canonical manifest
- export the hosted runtime manifest with hashed asset metadata
- estimate monthly ElevenLabs credit usage
- render voice callouts
- render sound-effect assets
- sync generated voice assets from iOS `Resources/Audio` into Android `res/raw`

## Marine Voice Guidance

Official Marine drill/training guidance consistently points toward:

- short and distinct command language
- loud, clear, precise delivery
- command presence that drives `snap and precision`
- professionalism and firmness rather than verbal abuse

Design implication:

- `Move with a purpose.` is in-policy
- `You worthless idiot.` is out of policy
- `Thirty seconds elapsed.` is clear
- `Thirty seconds.` is ambiguous

## Content QA Checklist

- Every elapsed cue contains the word `elapsed`
- No immediate command cue repeats when the pool has more than one cue
- Every generated cue has a bundled filename
- Android and iOS consume the same generated voice catalog
- Pro sound arsenal manifest resolves every `SoundType`
