# Skill: Plan Feature

Use Plan mode for feature discovery when requirements are ambiguous. Progressive disclosure: only surface questions relevant to the current phase.

## Trigger

- User invokes `/plan-feature`
- User asks to add a feature with unclear or incomplete requirements
- Proactively activate when feature scope is ambiguous

## Phase 1: Scope (load first — 2 minutes max)

Enter Plan mode. Explore only what's needed to ask smart questions:
- Read existing navigation to understand entry points
- Check if similar patterns exist in codebase
- Identify which platforms are affected

Ask only the **top 3-5 questions** that block implementation. Organize by priority, not category.

## Phase 2: Edge Cases (load after scope confirmed)

For timer-related features, check these — but only surface ones that apply:

- [ ] Timer expires while app is backgrounded
- [ ] User kills app during active timer
- [ ] Device goes to sleep during timer
- [ ] Notification permissions denied
- [ ] Sound plays while other audio is active
- [ ] Range slider at boundary conditions (min = max)
- [ ] Mystery mode state consistency

Skip irrelevant items. Don't pad the list.

## Phase 3: Plan Document (load after edge cases discussed)

Write a concise plan:

```markdown
## Feature: {Feature Name}

### Requirements
- [3-5 bullet points max]

### Edge Cases
- [Only ones that need handling]

### Steps
1. [Ordered, with platform tags: [Android] [iOS] [Both]]

### Open Questions
- [Only if any remain]
```

Get user approval. Do NOT create files until approved.

## Anti-Patterns

- Loading all phases upfront (wastes context)
- Asking 10+ questions before doing any exploration
- Padding edge case lists with irrelevant scenarios
- Starting implementation without approval
