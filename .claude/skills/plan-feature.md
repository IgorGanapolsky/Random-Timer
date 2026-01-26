# Skill: Plan Feature

Use Plan mode for feature discovery when requirements are ambiguous. Surfaces edge cases and clarifying questions BEFORE implementation.

## Trigger
- User invokes `/plan-feature`
- User asks to add a feature with unclear or incomplete requirements
- Proactively suggest when feature scope is ambiguous

## Workflow

### 1. Enter Plan Mode
Before ANY implementation, activate Plan mode to explore:
- Existing codebase patterns
- Related components and services
- Potential edge cases

### 2. Requirements Discovery Questions

Ask clarifying questions organized by category:

**User Experience:**
- What is the primary user flow?
- How should errors/failures be communicated?
- What happens on edge cases (app backgrounded, network loss, etc.)?

**Visual Design:**
- What is the visual hierarchy?
- How does this fit with existing UI patterns?
- Are there mobile-specific considerations?

**State Management:**
- What state needs to persist?
- How does this interact with existing Redux slices?
- What happens on app restart mid-feature?

**Audio/Haptics (if applicable):**
- What feedback should the user receive?
- How should it behave when app is backgrounded?

### 3. Edge Case Checklist

For timer-related features, always consider:
- [ ] Timer expires while app is backgrounded
- [ ] User kills app during active timer
- [ ] Device goes to sleep during timer
- [ ] Low battery / battery saver mode
- [ ] Notification permissions denied
- [ ] Sound plays while other audio is active
- [ ] Range slider at boundary conditions (min = max)
- [ ] Mystery mode state consistency

### 4. Document the Plan

Create a plan summary including:
```markdown
## Feature: {Feature Name}

### Requirements
- [Clear bullet points from discovery]

### Edge Cases Identified
- [List each edge case and proposed handling]

### Implementation Steps
1. [Ordered steps]
2. [Include test requirements]

### Open Questions
- [Any remaining ambiguity]
```

### 5. Get User Approval

Present the plan and wait for explicit approval before:
- Creating any files
- Modifying existing code
- Adding dependencies

## Example Usage

**User:** "Add a pause button to the timer"

**Plan Mode Response:**
Before implementing, I need to clarify:

1. **Pause behavior:** Should the timer resume from where it paused, or restart?
2. **Mystery mode:** Should pause reveal the remaining time?
3. **Visual state:** How should the CircularTimer indicate paused state?
4. **Multiple pauses:** Is there a limit on pause/resume cycles?
5. **Edge case:** What if user pauses, backgrounds app, then returns hours later?

## Success Criteria
- All ambiguous requirements clarified before coding
- Edge cases documented and handling decided
- User has approved the implementation plan
- No surprises during implementation

## Anti-Patterns to Avoid
- Starting implementation with unclear requirements
- Assuming behavior without asking
- Skipping edge case consideration for "simple" features
