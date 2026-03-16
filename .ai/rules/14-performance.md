<!-- tech-stack: frontend -->
# Performance

## Core Web Vitals Targets

| Metric | Target | Red Line |
|--------|--------|----------|
| LCP (Largest Contentful Paint) | < 2.5s | < 4.0s |
| INP (Interaction to Next Paint) | < 200ms | < 500ms |
| CLS (Cumulative Layout Shift) | < 0.1 | < 0.25 |

## Bundle Size Budget

| Category | Limit (gzipped) |
|----------|-----------------|
| Initial JS (entry chunk) | < 200KB |
| Per-route chunk | < 50KB |
| Total first-load JS | < 300KB |
| CSS (total) | < 50KB |

## Image Optimization

- Use `next/image` (Next.js) or `<img loading="lazy">` for all images
- Use WebP/AVIF format with fallback; never commit uncompressed PNG/BMP
- Above-the-fold images: set `priority` / `fetchpriority="high"`, skip `loading="lazy"`
- Provide explicit `width` and `height` to prevent layout shift

## Font Loading

- Use `next/font` (Next.js) or `font-display: swap` to avoid FOIT
- Preload critical fonts via `<link rel="preload">`
- Limit to 2 font families maximum

## Code Splitting

- Route-level splitting via `React.lazy()` + `Suspense` (or framework dynamic import)
- Heavy libraries (`chart.js`, `monaco-editor`, etc.) must be dynamically imported
- Components below the fold: lazy load with intersection observer or `Suspense`

## Rendering Strategy

- Static content: prefer SSG/ISR over SSR
- Data-heavy lists (> 50 items): use virtual scrolling (`@tanstack/react-virtual`)
- Expensive computations: `useMemo` / `useCallback` only when profiler confirms benefit
- Avoid re-renders: extract stable references, use `React.memo` for pure display components

## Third-Party Scripts

- Load analytics/tracking asynchronously (`async` / `defer` / `afterInteractive`)
- Maximum 3 third-party scripts on first load
- Audit bundle impact with `@next/bundle-analyzer` or `source-map-explorer`

## Forbidden Performance Patterns

| Pattern | Reason |
|---------|--------|
| `import _ from 'lodash'` (full import) | Use `lodash-es` or per-function import |
| `import moment from 'moment'` | Use `date-fns` or `dayjs` |
| Synchronous `localStorage` in render path | Defer to `useEffect` |
| Unthrottled scroll/resize listeners | Use `requestAnimationFrame` or throttle (≥ 100ms) |
| CSS-in-JS runtime (styled-components, Emotion) | Prefer Tailwind / CSS Modules (zero-runtime) |
| Inline `<script>` blocking render | Move to `defer` or dynamic import |
| Fetching data in component body (not in effect/loader) | Use `useEffect`, `loader`, or `useSWR`/`useQuery` |
