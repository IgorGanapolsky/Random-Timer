<!-- tech-stack: frontend -->
# Styling

## CSS Modules (Primary Method)

All component styles use CSS Modules:

```typescript
import styles from './index.module.scss'
```

### Class Name Conventions

Use **camelCase** for CSS class names:

```scss
.container { ... }
.headerWrapper { ... }
.isActive { ... }
```

## CSS Custom Properties (Theming)

Use CSS custom properties for theming values:

```scss
.button {
  color: var(--primary-color);
  background: var(--bg-color);
}
```

## Inline Styles

Only use inline styles for values computed at runtime.

## Responsive Breakpoints

Common breakpoints: `768px` (tablet), `1200px` (desktop).
