<!-- tech-stack: universal -->
# Forbidden Patterns

The following are **not allowed** in this codebase:

| Pattern | Reason |
|---------|--------|
| Class components | Use functional components with hooks |
| `any` type | Use `unknown` + type guards |
| `var` keyword | Use `const` / `let` |
| Committed `console.log` | Use proper logging; removed in production build |
| `// @ts-ignore` | Use `// @ts-expect-error` with explanation |
| Non-null assertion `!` (except DOM) | Use proper null checks |
| Inline `style={}` for static values | Use the project's configured styling approach (see `08-styling.md`). **Exception:** `style={{ transform, opacity }}` for runtime-computed animation/layout values is allowed |
