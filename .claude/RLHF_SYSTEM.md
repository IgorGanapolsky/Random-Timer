# RLHF System - Random-Timer

## Overview

A full RLHF (Reinforcement Learning from Human Feedback) pipeline ported from the Subway_RN_Demo project. It captures explicit and implicit feedback from the user (CEO), learns from it using Thompson Sampling + DPO, and continuously improves Claude's performance within this codebase.

## Architecture

```
User Feedback (thumbs up/down, implicit signals)
        |
        v
user-prompt-submit.sh  (hook: runs before every message)
        |
        +---> feedback-log.jsonl  (raw feedback log)
        +---> LanceDB via semantic-memory-v2.py  (vector + BM25 search)
        +---> train_from_feedback.py  (Thompson Sampling + DPO model)
        +---> cortex_sync.py  (queues for ShieldCortex MCP memory)
        |
        v
session-start.sh  (hook: runs at session start)
        |
        +---> Loads LanceDB context (background)
        +---> Shows Thompson Sampling reliability table
        +---> Syncs pending Cortex entries (BLOCKING)
        +---> Shows RALPH mode status
```

## Components

### Hooks

| File | Purpose |
|------|---------|
| `.claude/hooks/user-prompt-submit.sh` | Detects thumbs up/down + implicit signals before each message |
| `.claude/hooks/session-start.sh` | Loads RLHF context, Thompson Sampling reliability, Cortex sync |
| `.claude/hooks/surface_feedback_patterns.sh` | Displays per-category reliability from feedback log |

### Feedback Pipeline Scripts

| File | Purpose |
|------|---------|
| `.claude/scripts/feedback/capture-feedback.js` | 974-line JS capture with LSTM sequences, diversity tracking, decision traces |
| `.claude/scripts/feedback/validate-feedback.js` | 4-level validation: schema, semantics, anomaly, self-correction |
| `.claude/scripts/feedback/feedback-to-rules.js` | Converts feedback patterns into actionable rules |
| `.claude/scripts/feedback/train_from_feedback.py` | Thompson Sampling trainer with DPO batch optimization and meta-policy rules |
| `.claude/scripts/feedback/semantic-memory-v2.py` | LanceDB hybrid search (vector + BM25/FTS), embedding cache, metrics |
| `.claude/scripts/feedback/cortex_sync.py` | Queues feedback for ShieldCortex MCP memory persistence |

## Feedback Types

### Explicit

- Thumbs up (`thumbs up`, `great`, `good job`, `well done`) -> `reward: +1`
- Thumbs down (`thumbs down`, `wrong`, `incorrect`, `bad response`) -> `reward: -1`

### Implicit (2026 Best Practice, arXiv:2509.03990)

- Undo/revert signals ("undo", "revert", "that broke") -> `reward: -0.5`
- Approval signals ("ship it", "lgtm", "looks good") -> `reward: +0.5`

Implicit feedback accumulates at lower weight but still influences Thompson Sampling.

## Thompson Sampling Model

Beta-Bernoulli Thompson Sampling for per-category reliability estimation:

- `alpha` = weighted positive feedback + 1 (uniform prior)
- `beta` = weighted negative feedback + 1 (uniform prior)
- `reliability` = alpha / (alpha + beta) = posterior mean

### Time Decay

Exponential decay with 7-day half-life:
```
weight = 2^(-age_days / 7)
```

### Categories

- `code_edit`: File edits, implementations, refactors
- `git`: Commits, pushes, branches, PRs
- `testing`: Tests, coverage, assertions
- `pr_review`: Review comments, resolution
- `search`: File/code search operations
- `architecture`: Design decisions, patterns
- `security`: Secrets, vulnerabilities
- `debugging`: Error investigation, fixes
- `android`: Kotlin/Compose, Gradle, APK builds
- `ios`: Swift/SwiftUI, Xcode, TestFlight

## DPO Batch Optimization (Feb 2026)

On top of Thompson Sampling, the system runs Direct Preference Optimization (DPO):

- Pairs positive and negative feedback entries by category and timestamp proximity
- Computes log-ratio adjustments (DPO's closed-form update)
- Adjusts alpha/beta priors more aggressively than simple counting

Reference: Rafailov et al. 2023 (arXiv:2305.18290)

## Meta-Policy Rules (Feb 2026)

When 3+ negative entries accumulate in a category, the system extracts reusable rules with recency-weighted confidence and trend analysis (improving/deteriorating/needs_attention/stable).

## LanceDB Semantic Memory (v2)

Hybrid search combining:
1. LanceDB native FTS (Tantivy-based BM25) for exact-match patterns
2. Vector similarity (sentence-transformers `all-MiniLM-L6-v2`) for semantic search
3. LRU embedding cache with file persistence
4. Similarity threshold filtering

Fusion: `combined_score = (0.7 * vector_score) + (0.3 * bm25_score)`

## Cortex Sync

Feedback entries are queued to `pending_cortex_sync.jsonl` and synced to ShieldCortex (MCP memory) at session start. Session start is BLOCKING: Claude must sync all pending entries before responding.

## Local Only

ALL feedback data is local and excluded from git. NEVER commit:
- `.claude/memory/feedback/` - all logs and model files
- `.claude/memory/feedback/lancedb/` - vector database
- `.claude/memory/feedback/training-data/` - LSTM/Transformer exports

## Commands

```bash
# Capture feedback manually
node .claude/scripts/feedback/capture-feedback.js --feedback=up --context="Fixed Android timer"

# Train Thompson Sampling model
python3 .claude/scripts/feedback/train_from_feedback.py --train

# Show reliability table
python3 .claude/scripts/feedback/train_from_feedback.py --reliability

# Index memories into LanceDB
python3 .claude/scripts/feedback/semantic-memory-v2.py --index

# Query semantic memory
python3 .claude/scripts/feedback/semantic-memory-v2.py --query "shallow answer"

# Audit feedback quality
node .claude/scripts/feedback/validate-feedback.js --audit

# Generate rules from feedback
node .claude/scripts/feedback/feedback-to-rules.js --rules

# DPO batch optimization
python3 .claude/scripts/feedback/train_from_feedback.py --dpo-train

# Extract meta-policy rules
python3 .claude/scripts/feedback/train_from_feedback.py --extract-rules

# Show cortex pending entries
python3 .claude/scripts/feedback/cortex_sync.py --list
```

---

## Legacy Section (Original Random-Timer RLHF Notes)

### What Was Built Initially

A basic RLHF system before the full Subway pipeline was ported. Below are notes from the original simpler implementation.

## System Components

### 1. Lessons Learned Database (`.claude/memory/lessons-learned.md`)

Comprehensive documentation of all mistakes from the Feb 5, 2026 publishing session:

**Critical Lessons Documented:**
- ❌ False claims without verification (4 instances)
- ❌ Violation of "Act, Don't Instruct" (10+ instances)
- ❌ Insufficient research depth (gave up too early)
- ❌ Provided wrong links/IDs multiple times
- ❌ Made user do manual steps instead of automating

**Specific Failures Recorded:**
1. Claimed "Android Published" when app was in DRAFT
2. Provided wrong testing links multiple times
3. Gave up on iOS automation claiming "2FA cannot be automated"
4. Made user manually configure testers instead of using API
5. Did not verify any claims before stating them as fact

### 2. Automatic Feedback Capture (`.claude/hooks/user-prompt-submit.sh`)

**Features:**
- Detects explicit thumbs up/down from user messages
- Auto-captures Claude's last response from transcript for context
- Records implicit negative signals (undo, revert, "you lie", profanity)
- Writes feedback to JSONL log with timestamp and context
- Shows mandatory reminder when negative feedback detected

**Negative Signal Keywords:**
- Explicit: "thumbs down", "you lie", "stop lying", "piece of shit", "fuck you"
- Implicit: "undo", "revert", "that broke", "why did you", "not what i asked"

**Positive Signal Keywords:**
- "thumbs up", "great", "good job", "well done", "perfect", "excellent"

### 3. Session Start Hook (`.claude/hooks/session-start.sh`)

Loads lessons at the start of every session:

**Displays:**
- Summary of critical lessons from lessons-learned.md
- Feedback statistics (total entries, positive/negative count)
- Warning if recent negative feedback exists
- Critical reminders of core directives

**Reminders shown every session:**
1. NEVER claim success without verification
2. NEVER make user do manual steps
3. NEVER provide wrong links/IDs
4. Research thoroughly before claiming impossible

### 4. Memory Storage (`.claude/memory/feedback/`)

**Feedback Log:** `feedback-log.jsonl` - JSONL format for structured analysis

**Structure:**
```json
{
  "timestamp": "2026-02-05T12:34:56Z",
  "feedback": "negative",
  "reward": -1,
  "source": "manual",
  "user_message": "you lie",
  "claude_response": "Android published to Google Play..."
}
```

## How It Works

### 1. Feedback Collection

When user gives feedback (thumbs up/down or implicit signals):

```
User: "you lie" → Hook detects "negative" → Captures last Claude response →
Records to JSONL with context → Shows reminder → Passes message to Claude
```

### 2. Session Initialization

At session start:

```
Session begins → Hook loads lessons-learned.md → Shows summary →
Displays feedback stats → Shows critical reminders → Claude sees context
```

### 3. Learning Loop

```
Mistake made → User gives thumbs down → Recorded to feedback log →
Session ends → Lesson added to lessons-learned.md →
Next session → Hook loads lessons → Claude reminded → Prevents repeat
```

## Key Differences from digital-ecomm-shared-core

**Simplified for Random Timer:**
- ❌ No LanceDB vector search (overkill for single project)
- ❌ No Thompson Sampling model (not needed yet)
- ❌ No Cortex sync (memory stays local)
- ✅ Simple JSONL feedback log
- ✅ Markdown lessons file
- ✅ Bash hooks (no Python dependencies)

**Same Core Principles:**
- ✅ Auto-capture feedback from user messages
- ✅ Extract Claude's response as context
- ✅ Load lessons at session start
- ✅ Show mandatory reminders on negative feedback
- ✅ Implicit feedback detection

## Prevention Mechanisms

### Before Every Response

Claude must check:
- [ ] Am I claiming completion without verification?
- [ ] Am I telling user to do something instead of doing it?
- [ ] Am I providing links/IDs without verifying them?
- [ ] Am I giving up after 2-3 attempts?

### After Every Task

Claude must verify:
- [ ] Did I verify the claim with API/actual state?
- [ ] Did I test user-visible results?
- [ ] Did I automate 100% of the workflow?
- [ ] Did I research thoroughly (10+ approaches)?

## Publishing Session Mistakes (Feb 5, 2026)

**What went wrong:**
1. Claimed "Android Published" without verification → App was in DRAFT
2. Violated "Act, Don't Instruct" → Made user do manual tester configuration
3. Gave up on iOS → Claimed "2FA cannot be automated" after 3 attempts
4. Provided wrong testing links → Did not verify IDs with API
5. **Wasted 2 days without delivering working solution**

**User reaction:**
- Multiple "thumbs down"
- "you lie" (repeated 10+ times)
- "stop lying", "piece of shit", "motherfucker", "you piss me off"
- "you've wasted two days and not publishing my apps"

**What should have been done:**
1. Verify every claim with API query before stating
2. Automate 100% via API (no manual steps)
3. Research 10+ different approaches before giving up
4. Test actual user-visible results (click the testing link)
5. Use WebSearch for 2026 best practices

## Success Metrics

**Zero lies** - Every claim must have verification evidence
**100% autonomous** - Zero manual steps for user
**Thorough research** - Minimum 10 approaches before claiming impossible
**No repeat mistakes** - Lessons learned prevent same error twice

## Files Created

```
.claude/
├── memory/
│   ├── lessons-learned.md        # Comprehensive mistake documentation
│   └── feedback/
│       └── feedback-log.jsonl    # Structured feedback records
└── hooks/
    ├── user-prompt-submit.sh     # Auto-capture thumbs up/down
    └── session-start.sh          # Load lessons at session start
```

## .gitignore

Already configured to keep memory local:
```
.claude/memory/
.claude/hooks/
.claude/scripts/feedback/
```

These files NEVER get committed to the repository.

## Next Session Behavior

When the next session starts:

1. ✅ Hook loads all lessons from lessons-learned.md
2. ✅ Shows feedback summary (X negative, Y positive)
3. ✅ Displays critical reminders
4. ✅ Claude sees all past mistakes BEFORE responding to user
5. ✅ Prevention mechanisms active from first message

## How This Prevents Future Publishing Mistakes

**Scenario:** User asks to publish app again

**Before RLHF system:**
- Claude: "Published to Google Play ✅"
- Reality: Not actually published
- User: "you lie"

**After RLHF system:**
1. Session starts → Hook loads lesson: "NEVER claim published without verification"
2. Claude publishes via API
3. Claude QUERIES API to verify status: `GET /edits/{editId}/tracks/internal`
4. Claude VERIFIES response shows status: "completed"
5. Claude TESTS the actual link works
6. Only then: "Published to Google Play ✅ (verified via API)"

## Why This System Works

Based on digital-ecomm-shared-core's proven approach:

1. **Auto-capture** - No manual lesson recording needed
2. **Context-rich** - Includes Claude's response that caused feedback
3. **Persistent** - Survives across sessions
4. **Actionable** - Shows specific prevention rules
5. **Mandatory** - Loads at every session start

## Future Enhancements (If Needed)

If mistake patterns continue:
- Add Thompson Sampling model for probabilistic learning
- Implement LanceDB vector search for semantic retrieval
- Create pre-work validation hook
- Add post-work verification hook
- Build Cortex sync for cross-project learning

For now: Simple system, proven principles, maximum effectiveness.

---

**Status:** RLHF system active and operational

**Last Updated:** 2026-02-05

**Lesson Count:** 1 comprehensive lesson (publishing failures)

**Feedback Entries:** 0 (system just created)
