<!-- tech-stack: frontend -->
# Frontend Security

## XSS Prevention

- Never use `dangerouslySetInnerHTML` unless content is sanitized with `DOMPurify` or equivalent
- Never construct HTML strings from user input
- Sanitize all user-generated content before rendering
- Use Content Security Policy (CSP) headers to restrict inline scripts

## Input Validation

- Validate on both client and server — client validation is UX, not security
- Sanitize file uploads: validate MIME type, file extension, and file size
- Use allowlists, not denylists, for accepted input patterns
- Escape special characters in URLs, HTML attributes, and SQL queries at the boundary

## Sensitive Data Handling

| Data Type | Storage | Transmission |
|-----------|---------|-------------|
| Access tokens | Memory (variable) or `httpOnly` cookie | HTTPS only |
| Refresh tokens | `httpOnly` + `Secure` + `SameSite=Strict` cookie | HTTPS only |
| User PII | Never in `localStorage` | Encrypted, HTTPS only |
| API keys | Server-side only (env vars) | Never exposed to client |

- Never log sensitive data to console, analytics, or error trackers
- Clear sensitive data from memory when no longer needed

## Authentication & Authorization

- Use `httpOnly` cookies for session tokens — never store in `localStorage`
- Implement CSRF protection via `SameSite` cookie attribute or CSRF tokens
- Validate JWT expiration client-side; refresh proactively before expiry
- Redirect to login on 401; redirect to error page on 403

## API Security

- Always use HTTPS — never make requests over HTTP
- Include `Authorization` header only for authenticated endpoints
- Do not embed API keys or secrets in client-side code or bundles
- Implement request rate limiting awareness (handle 429 gracefully)

## Dependency Security

- Run `npm audit` / `pnpm audit` regularly in CI
- Pin exact versions for critical security-sensitive packages
- Review changelogs before upgrading authentication or crypto libraries
- Never use packages with known critical vulnerabilities

## Content Security Policy (CSP)

Recommended baseline headers:

```
Content-Security-Policy:
  default-src 'self';
  script-src 'self';
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: https:;
  connect-src 'self' https://api.your-domain.com;
  font-src 'self';
  frame-ancestors 'none';
```

## Forbidden Security Patterns

| Pattern | Reason |
|---------|--------|
| `dangerouslySetInnerHTML` with unsanitized input | XSS vulnerability |
| Storing tokens in `localStorage` | Accessible to XSS attacks |
| Hardcoded API keys in source code | Exposed in client bundles |
| `eval()` or `new Function()` with user input | Code injection |
| HTTP requests for sensitive operations | Man-in-the-middle attacks |
| Disabled CORS with `Access-Control-Allow-Origin: *` for authenticated APIs | Credential leakage |
| `target="_blank"` without `rel="noopener noreferrer"` | Reverse tabnapping |
