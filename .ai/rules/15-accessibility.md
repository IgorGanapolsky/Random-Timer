<!-- tech-stack: frontend -->
# Accessibility (WCAG 2.1 AA)

## Semantic HTML

Use the correct HTML element for the job:

| Need | Use | Never |
|------|-----|-------|
| Clickable action | `<button>` | `<div onClick>` |
| Navigation link | `<a href>` | `<span onClick>` |
| Page landmark | `<nav>`, `<main>`, `<aside>`, `<footer>` | Generic `<div>` |
| List of items | `<ul>` / `<ol>` + `<li>` | Nested `<div>` |
| Data display | `<table>` with `<thead>` / `<tbody>` | CSS grid pretending to be a table |

## Heading Hierarchy

- Every page must have exactly one `<h1>`
- Headings must not skip levels (`h1 → h2 → h3`, never `h1 → h3`)
- Use headings for structure, not for styling

## Keyboard Navigation

- All interactive elements must be reachable via `Tab`
- `Enter` / `Space` must activate buttons and links
- `Escape` must close modals, dropdowns, and popovers
- Focus order must follow visual reading order
- Never set `tabIndex` > 0

## Focus Management

- Focus must be visible — never use `outline: none` without a visible alternative
- When a modal opens, move focus to the first focusable element inside
- When a modal closes, return focus to the trigger element
- Implement focus trap inside modals and dialogs

## Color & Contrast

| Context | Minimum Contrast Ratio |
|---------|----------------------|
| Normal text (< 18px) | 4.5:1 |
| Large text (≥ 18px or ≥ 14px bold) | 3:1 |
| UI components & icons | 3:1 |

- Never convey information by color alone — add text labels, icons, or patterns
- Test with a contrast checker tool before shipping

## Images & Media

- All meaningful images must have descriptive `alt` text
- Decorative images: use `alt=""` (empty, not omitted)
- Complex images (charts, diagrams): provide text description or `aria-describedby`
- Videos: provide captions or transcripts

## Forms

- Every `<input>` must have an associated `<label>` (via `htmlFor` or wrapping)
- Group related fields with `<fieldset>` + `<legend>`
- Error messages must be programmatically linked (`aria-describedby` or `aria-errormessage`)
- Required fields: use `aria-required="true"` and visual indicator

## ARIA Guidelines

- **First rule of ARIA**: prefer native HTML semantics over ARIA
- Use `aria-live="polite"` for dynamic content updates (toast, status messages)
- Use `aria-expanded` for disclosure widgets (accordion, dropdown)
- Use `role="dialog"` + `aria-modal="true"` for modals
- Never use `role="presentation"` or `aria-hidden="true"` on focusable elements

## Forbidden Accessibility Patterns

| Pattern | Reason |
|---------|--------|
| `outline: none` without visible focus alternative | Keyboard users lose track of focus |
| Interactive elements without accessible name | Screen readers cannot announce them |
| `tabIndex={-1}` on regularly interactive elements | Removes keyboard access |
| Auto-playing audio/video without pause control | Disruptive and disorienting |
| Time-limited actions without extension option | Users with motor disabilities need more time |
