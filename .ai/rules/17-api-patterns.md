<!-- tech-stack: frontend -->
# API Patterns

## Request Abstraction

Centralize all API calls through a shared request client:

```typescript
// src/lib/request.ts
import axios from 'axios'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 15_000,
  headers: { 'Content-Type': 'application/json' },
})

// Request interceptor: attach auth token
request.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Response interceptor: normalize errors
request.interceptors.response.use(
  (res) => res.data,
  (error) => {
    const status = error.response?.status
    if (status === 401) redirectToLogin()
    if (status === 403) redirectToForbidden()
    return Promise.reject(normalizeError(error))
  },
)

export { request }
```

## API Function Organization

```
src/api/
├── index.ts          # Re-exports all API modules
├── user.ts           # User-related endpoints
├── product.ts        # Product-related endpoints
└── types.ts          # Shared API type definitions
```

Each API module exports typed functions:

```typescript
// src/api/user.ts
import { request } from '@/lib/request'
import type { User, UpdateUserParams } from './types'

export const userApi = {
  getProfile: () => request.get<User>('/user/profile'),
  update: (params: UpdateUserParams) => request.put<User>('/user/profile', params),
  list: (params: PageParams) => request.get<PageResult<User>>('/users', { params }),
}
```

## Error Handling

### Standardized Error Shape

```typescript
interface ApiError {
  code: string        // Machine-readable error code (e.g., 'VALIDATION_ERROR')
  message: string     // User-facing error message
  status: number      // HTTP status code
  details?: unknown   // Optional validation errors or context
}
```

### Error Handling in Components

```typescript
// Use try-catch for mutations
const handleSubmit = async () => {
  try {
    await userApi.update(formData)
    toast.success('Saved successfully')
  } catch (error) {
    toast.error(getErrorMessage(error))
  }
}
```

## Data Fetching Patterns

### With TanStack Query / SWR

```typescript
// Preferred: declarative data fetching with caching
const { data, isLoading, error } = useQuery({
  queryKey: ['user', userId],
  queryFn: () => userApi.getProfile(),
})
```

### Loading & Error States

Every data-fetching component must handle three states:

| State | UI |
|-------|-----|
| Loading | Skeleton placeholder or spinner |
| Error | Error message with retry action |
| Empty | Empty state illustration with guidance |

Never show a blank screen — always provide feedback.

## Pagination

```typescript
interface PageParams {
  page: number
  pageSize: number
  [key: string]: unknown   // Filters, sorting
}

interface PageResult<T> {
  list: T[]
  total: number
  page: number
  pageSize: number
}
```

- Default `pageSize`: 20
- Always pass pagination params explicitly
- Use cursor-based pagination for infinite scroll

## Request Cancellation

Cancel in-flight requests when the component unmounts or params change:

```typescript
useEffect(() => {
  const controller = new AbortController()
  fetchData({ signal: controller.signal })
  return () => controller.abort()
}, [params])
```

With TanStack Query, cancellation is handled automatically.

## Retry Strategy

| Scenario | Strategy |
|----------|----------|
| Network error (no response) | Retry up to 3 times with exponential backoff |
| 5xx server error | Retry up to 2 times with 1s delay |
| 4xx client error | Do not retry — surface error to user |
| 429 rate limited | Retry after `Retry-After` header value |

## Forbidden API Patterns

| Pattern | Reason |
|---------|--------|
| `fetch()` without error handling | Silent failures |
| Hardcoded API base URL in components | Use environment variables |
| Storing API response in `localStorage` for caching | Use TanStack Query / SWR cache instead |
| Chaining `.then().then().then()` | Use `async/await` for readability |
| Ignoring request cancellation on unmount | Memory leaks and race conditions |
| Mixing multiple HTTP clients (axios + fetch) | Use one client consistently |
