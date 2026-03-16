# ADR Workflow — Architecture Decision Record

Record important technical decisions with full context so that future developers and AI agents understand **why** a decision was made.

## When to Use

- A technology or library was chosen over alternatives
- An architectural pattern was adopted or changed
- A significant trade-off was made (performance vs. maintainability, etc.)
- A constraint or limitation was accepted
- A previous decision was revisited or reversed

## Workflow Steps

### Step 1: Gather Context

If the user provided a description, use it as the starting point. Otherwise, ask:

1. **What decision was made?** (one sentence)
2. **What alternatives were considered?** (if any)
3. **Why was this option chosen?**

Also review the current conversation context — if a decision was just made during development, extract the relevant details automatically without asking redundant questions.

### Step 2: Determine Next ADR Number

Read `.ai/decisions/README.md` to find the last ADR number in the index table. The new ADR gets the next sequential number (e.g., if last is 003, new is 004).

### Step 3: Write the ADR

Create `.ai/decisions/NNN-short-description.md` using the template at `.ai/decisions/_template.md`:

- **Status**: `accepted` (default) or `proposed` if still under discussion
- **Date**: Today's date
- **Context**: The forces at play, what motivated the decision
- **Decision**: What was decided
- **Consequences**: Positive, negative, and risks
- **Related**: Links to relevant files, ADRs, or commits

Keep the language concise and factual. Focus on **why**, not just **what**.

### Step 4: Update the Index

Append a new row to the index table in `.ai/decisions/README.md`:

```markdown
| NNN | [Title](NNN-short-description.md) | accepted | YYYY-MM-DD |
```

### Step 5: Confirm

Output a brief summary:
- ADR number and title
- One-line summary of the decision
- File path created

## Style Guidelines

- Write in English
- Use imperative mood for the title ("Use X for Y", "Stay on X", "Adopt X pattern")
- Keep Context section under 10 lines
- Keep Decision section under 5 lines
- List 2-4 consequences per category (positive/negative/risks)
- Link to actual source files, not just descriptions
