---
name: rlhf-feedback
description: Autonomous RLHF feedback capture - Claude self-captures mistakes and successes
triggers:
  - thumbs down
  - thumbs up
  - mistake
  - good job
  - wrong
  - correct
  - that worked
  - that failed
---

# RLHF Feedback Capture Skill

**AUTONOMOUS** - Feedback is captured automatically via hooks. Memory cells are self-organizing.

## How It Works

1. `user-prompt-submit.sh` hook detects feedback signals (thumbs up/down, implicit)
2. Records to `.claude/memory/feedback/feedback-log.jsonl`
3. Ingests into self-organizing memory system (`memory_manager.py`)
4. On session start, recalls high-salience scene-relevant memories

## Memory Cell Types

- **risk** - Things that caused user frustration (lying, false claims)
- **pattern** - Repeated behaviors (good or bad)
- **decision** - Architecture/approach choices made
- **preference** - User preferences and mandates
- **fact** - Verified facts about the codebase

## Scene Categories

Memories are auto-classified into scenes:
`store-publishing`, `code-editing`, `git-operations`, `testing`,
`debugging`, `automation`, `animation-parity`, `credentials`, `general`

## Manual Feedback Capture

When Claude detects a mistake or success mid-session:

```bash
# Capture negative feedback
echo '{"feedback":"negative","context":"What went wrong","id":"manual_1"}' | \
  python3 .claude/scripts/memory/memory_manager.py --ingest

# Capture positive feedback
echo '{"feedback":"positive","context":"What went right","id":"manual_2"}' | \
  python3 .claude/scripts/memory/memory_manager.py --ingest
```

## Memory Operations

```bash
# Recall all high-salience memories
python3 .claude/scripts/memory/memory_manager.py --recall

# Recall for a specific scene
python3 .claude/scripts/memory/memory_manager.py --recall --scene store-publishing

# Run maintenance (decay stale + consolidate duplicates)
python3 .claude/scripts/memory/memory_manager.py --maintain

# View stats
python3 .claude/scripts/memory/memory_manager.py --stats
```

## Data Storage

All feedback is LOCAL ONLY:
- `.claude/memory/feedback/feedback-log.jsonl` (raw feedback)
- `.claude/memory/memory_cells.jsonl` (self-organized memory cells)

## Learning Loop

Mistake -> Hook captures -> Memory cell created/consolidated ->
Session start recalls -> Claude avoids repeat -> Salience decays if fixed
