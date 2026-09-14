# Compaction-safe artifact transparency

Source lesson: [Generating running routes with GPT-6 Astra and ChatGPT Work](https://simonwillison.net/2026/Sep/12/astra-running-routes/) (Simon Willison, 2026-09-12).

## Problem

A long agent run can produce the right deliverables (GPX, GeoJSON, share HTML) while still failing operationally:

1. Tool traces and generated code stay hidden in the chat UI.
2. Session **compaction** drops the pre-compacted transcript.
3. Asking “show me the Python you ran” returns nothing recoverable.

Willison calls that opacity an **anti-feature**.

## Policy (this fleet)

| Requirement | Why |
|---|---|
| Persist **tool traces** before compact | Prove Nominatim/Overpass/local-compute (or equivalent) actually ran |
| Persist **generated code** | Survive compaction; recall via tool |
| Persist **downloadable artifacts** | Chat text is not a deliverable |
| **Recall API** for pre-compaction text | Agents and humans can recover evidence after compact |
| Share HTML uses **allowlisted CDNs only** | Match visualize-skill CSP discipline |
| Prefer **fetch open data → local compute** | Transparent, reproducible, cheaper than opaque generation |

## CLI

```bash
python3 scripts/agent_artifact_transparency.py doctor

python3 scripts/agent_artifact_transparency.py persist \
  --vault /tmp/artifact-vault \
  --run-id astra-5k \
  --code /tmp/route.py \
  --trace-json /tmp/trace.json \
  --pre-text /tmp/transcript.txt \
  --artifact route.geojson=/tmp/route.geojson \
  --artifact share.html=/tmp/share.html

python3 scripts/agent_artifact_transparency.py recall \
  --vault /tmp/artifact-vault \
  --run-id astra-5k

python3 scripts/agent_artifact_transparency.py share-html \
  --title "El Granada harbor loop" \
  --subtitle "5.1 km" \
  --data-json /tmp/route.json \
  --out /tmp/share.html
```

## Allowlisted CDN hosts

`cdn.jsdelivr.net`, `cdnjs.cloudflare.com`, `esm.sh`, `unpkg.com`, `fonts.googleapis.com`, `fonts.gstatic.com`, `fonts.bunny.net`.

## Evidence status

Code + unit tests landed. Live Astra/ChatGPT Work integration: **not applicable** / not verified — this module encodes the transparency policy for our own agent runs.
