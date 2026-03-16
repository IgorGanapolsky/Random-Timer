<!-- tech-stack: frontend -->
# TypeScript

## Compiler Configuration

Key `tsconfig.json` settings for this project:

| Setting | Value | Notes |
|---------|-------|-------|
| `strict` | `true` | All strict checks enabled |
| `target` | `ES2020` | — |

## Strict Rules

- **Strict mode** is enabled — respect all strict checks.
- Prefer `interface` for object shapes; use `type` for unions, intersections, and mapped types.
- **Minimize `any`** — use `unknown` and narrow with type guards.
- Always type function parameters and return types for exported functions.
- Use `as const` for literal tuples and fixed arrays.
- No `// @ts-ignore` — use `// @ts-expect-error` with an explanation comment if absolutely necessary.

## Interface vs Type

| Use Case | Keyword |
|----------|---------|
| Object shapes, component props | `interface` |
| Union types, mapped types, primitives | `type` |

## `any` Strategy

- **New code**: Never use `any`. Use `unknown`, generics, or specific types.
- **Legacy code**: Tolerate existing `any` but do not expand its scope.
- **Never** add new `any` just to silence errors — fix the type instead.
