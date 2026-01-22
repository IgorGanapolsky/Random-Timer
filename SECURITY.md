# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x     | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in Random Timer, please report it responsibly:

1. **Do NOT** create a public GitHub issue for security vulnerabilities
2. Use GitHub's private vulnerability reporting feature (Security tab → "Report a vulnerability")
3. Or email the maintainer directly

### What to include in your report

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested fixes (optional)

### Response timeline

- **Initial response**: Within 48 hours
- **Status update**: Within 7 days
- **Resolution**: Depends on severity and complexity

### What happens next

1. We'll acknowledge receipt of your report
2. We'll investigate and determine the impact
3. We'll work on a fix and coordinate disclosure
4. We'll credit you in the release notes (unless you prefer to remain anonymous)

## Security Measures

This project implements several security measures:

- **Pre-commit hooks**: Gitleaks scans for secrets before commits
- **CI/CD security**: GitHub's secret scanning and code scanning enabled
- **Dependency scanning**: Dependabot alerts for vulnerable dependencies
- **No secrets in code**: All sensitive configuration uses environment variables

## Scope

This security policy applies to:
- The Random Timer mobile application
- Associated build scripts and configuration

Out of scope:
- Third-party dependencies (report to their maintainers)
- Issues in development/testing environments only
