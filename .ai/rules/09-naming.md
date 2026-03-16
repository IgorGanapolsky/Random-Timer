<!-- tech-stack: universal -->
# Naming Conventions

## Files & Directories

| Item | Convention | Example |
|------|-----------|---------|
| Component directory | kebab-case | `video-card/` |
| Component entry file | `index.tsx` | `video-card/index.tsx` |
| Component styles | Per `08-styling.md` | CSS Modules: `index.module.scss`; Tailwind: styles in JSX |
| Hook file | `use-` prefix, kebab-case | `use-video-player.ts` |
| Utility file | kebab-case | `format-date.ts` |
| Constants file | kebab-case | `storage-keys.ts` |

## Exports & Symbols

| Item | Convention | Example |
|------|-----------|---------|
| React component | PascalCase | `export const VideoCard` |
| Custom hook | camelCase, `use` prefix | `export function useVideoPlayer()` |
| Utility function | camelCase | `export function formatDuration()` |
| Constant | SCREAMING_SNAKE_CASE | `export const MAX_DURATION = 600` |
| Type alias | PascalCase | `type UploadStatus = 'pending' \| 'done'` |
| Enum | PascalCase | `export enum RecStatus { ... }` |

## Variables & Functions

| Context | Convention | Example |
|---------|-----------|---------|
| Local variable | camelCase | `const videoList = []` |
| Boolean variable | `is/has/can/should` prefix | `isLoading`, `hasPermission` |
| Event handler | `handle` prefix | `handleClick` |
| Event callback (prop) | `on` prefix | `onClick` |
| Ref variable | `Ref` suffix | `containerRef` |

## Anti-Patterns

- **No Hungarian notation**: Don't prefix with type indicators
- **No obscure abbreviations**: Use `info` not `inf`
- **No single-letter variables**: Except `i`, `j`, `k` in loops
- **No numbered suffixes**: Don't use `data2`, `handleClick2`
