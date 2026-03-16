<!-- tech-stack: frontend -->
# React

## Component Structure

Each component lives in its own directory:

```
components/common/my-component/
├── index.tsx              # Component implementation
├── index.module.scss      # Scoped styles
└── (optional sub-files)
```

## Function Components Only

Use function components for all new code. Do not introduce new class components.

## Props Handling

Destructure props in the function signature. Use default parameter values.

## Event Handler Naming

| Type | Prefix | Example |
|------|--------|---------|
| Internal handler | `handle` | `handleClick`, `handleSubmit` |
| Prop callback | `on` | `onClick`, `onSubmit` |

## Hooks Best Practices

- **One effect per concern** — separate data fetching, event listeners, and timers
- **Always clean up** — return a cleanup function for subscriptions, timers, and listeners
- `useCallback` — wrap callbacks passed to child components
- `useMemo` — use for computationally expensive derived values
