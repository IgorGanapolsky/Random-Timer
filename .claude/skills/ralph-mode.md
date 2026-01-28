# Ralph Mode

Autonomous iteration loop for complex, well-defined coding tasks.

## When to Use

- Multi-file changes with clear acceptance criteria
- Bug fixes that require test→fix→retry cycles
- Refactoring with existing test coverage
- Any task that can be broken into checkboxes

## How It Works

```
┌─────────────────────────────────────────────────────────┐
│                    RALPH MODE LOOP                       │
│                                                          │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐           │
│  │  PLAN    │───▶│  CODE    │───▶│  TEST    │           │
│  │(checkbox)│    │(implement)│   │(quality) │           │
│  └──────────┘    └──────────┘    └────┬─────┘           │
│       ▲                               │                  │
│       │         ┌──────────┐          │                  │
│       │         │  REVIEW  │◀─────────┤                  │
│       │         │(superior │          │                  │
│       │         │  intel)  │     ┌────┴────┐            │
│       │         └────┬─────┘     │  PASS?  │            │
│       │              │           └────┬────┘            │
│       │              ▼                │                  │
│       │         ┌──────────┐     NO   │   YES           │
│       └─────────│   FIX    │◀─────────┤                  │
│                 │ (retry)  │          │                  │
│                 └──────────┘          ▼                  │
│                               ┌──────────┐              │
│                               │  COMMIT  │              │
│                               └──────────┘              │
└─────────────────────────────────────────────────────────┘
```

## Starting Ralph Mode

```bash
# Start a new Ralph session
.claude/scripts/ralph-loop.sh start "Add user authentication" AUTH-123

# Check status
.claude/scripts/ralph-loop.sh status

# Add checkpoint after completing a step
.claude/scripts/ralph-loop.sh checkpoint "Completed login form"

# Stop session
.claude/scripts/ralph-loop.sh stop
```

## ATTEMPTS.md Structure

Ralph creates `.claude/ralph/ATTEMPTS.md` with:

1. **Task Breakdown** - Checkboxes for each sub-task
2. **Attempt Log** - Each iteration with:
   - Actions taken
   - Test results
   - Learnings captured
3. **Final Summary** - Patterns learned for future

## The Loop Protocol

When in Ralph Mode, Claude MUST:

1. **Read ATTEMPTS.md** before each action
2. **Update checkboxes** as tasks complete
3. **Run quality checks** after each code change:
   ```bash
   npm run compile && npm run lint:check && npm test
   ```
4. **Log failures** with specific error messages
5. **Retry with fixes** until tests pass or max attempts reached
6. **Request superior review** before final commit

## Superior Intelligence Review

Before committing, invoke the review agent:

```
Use Task tool with subagent_type: "compound-engineering:review:code-simplicity-reviewer"
```

This ensures:
- Code is minimal and focused
- No over-engineering
- Follows project patterns
- Security considerations addressed

## Completion

When all checkboxes are complete and tests pass:

1. Update ATTEMPTS.md with final summary
2. Commit with message referencing work item
3. Create PR if on feature branch
4. Archive ATTEMPTS.md to `.claude/ralph/archive/`

## Example Session

```
User: Add dark mode toggle to settings

Claude: Starting Ralph Mode for this multi-file change.

[Runs: .claude/scripts/ralph-loop.sh start "Add dark mode toggle" #42]

Reading ATTEMPTS.md... Breaking down tasks:
- [ ] Add isDarkMode to Redux state
- [ ] Create DarkModeToggle component
- [ ] Wire toggle to Settings screen
- [ ] Update theme provider
- [ ] Add persistence

Starting with first checkbox...

[Implements Redux slice change]
[Runs quality checks]
[Checks checkbox, moves to next]

...continues until all pass...

[Requests superior intelligence review]
[Makes suggested simplifications]
[Final commit with all tests passing]
```

## Key Principles

1. **Fail Fast, Fix Fast** - Don't analyze failures forever, try fixes quickly
2. **Checkpoint Often** - Save progress after each successful step
3. **Learn from Failures** - Log what didn't work to avoid repeating
4. **Trust Tests** - If tests pass, move forward
5. **Review Before Commit** - Superior intelligence catches what tests miss
