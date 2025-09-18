# 🔒 Security Hooks Documentation

## Overview

This repository implements **bulletproof security hooks** that prevent sensitive data from ever reaching the repository. No more dealing with GitGuardian alerts after the fact!

## Security Measures

### Pre-Commit Hooks (`.husky/pre-commit`)

**Runs on every commit attempt:**

1. **🛡️ GitGuardian Secret Scan**
   - Scans staged files for secrets, credentials, and sensitive data
   - Uses GitGuardian's advanced ML detection
   - **Blocks commit if secrets found**

2. **🔍 Hardcoded Secret Detection**
   - Scans for patterns: `password`, `secret`, `key`, `token`, `api_key`, `private_key`
   - Excludes legitimate code (passwordGenerator, PasswordOptions)
   - **Blocks commit if secrets found**

3. **📁 Large File Detection**
   - Prevents files >1MB from being committed
   - Excludes build artifacts and dependencies
   - **Blocks commit if large files found**

4. **🐛 Debug Statement Detection**
   - Scans for `console.log`, `debugger`, `alert()`, `confirm()`
   - Prevents debug code from reaching production
   - **Blocks commit if debug statements found**

5. **🎨 Code Quality (lint-staged)**
   - Runs ESLint, Prettier, and other quality checks
   - **Blocks commit if quality issues found**

### Pre-Push Hooks (`.husky/pre-push`)

**Runs before every push:**

1. **🛡️ GitGuardian Full Repository Scan**
   - Scans entire repository for secrets
   - **Blocks push if secrets found**

2. **🔎 TypeScript Type Checking**
   - Ensures all code compiles without errors
   - **Blocks push if type errors found**

3. **🧪 Test Suite Execution**
   - Runs full test suite with coverage
   - **Blocks push if tests fail**

4. **📊 Coverage Requirements**
   - Enforces minimum 80% coverage
   - **Blocks push if coverage below threshold**

5. **🔒 Security Audit**
   - Runs `yarn audit` for high-severity vulnerabilities
   - **Blocks push if vulnerabilities found**

6. **📁 Sensitive File Detection**
   - Scans for `.key`, `.pem`, `.env`, etc.
   - **Blocks push if sensitive files found**

## Installation

### 1. Install GitGuardian CLI
```bash
pipx install ggshield
```

### 2. Configure GitGuardian (Optional)
```bash
ggshield auth login
```

### 3. Test the Hooks
```bash
# Test pre-commit hook
git add .
git commit -m "test commit"

# Test pre-push hook
git push origin develop
```

## Configuration Files

- **`.husky/pre-commit`** - Pre-commit security checks
- **`.husky/pre-push`** - Pre-push security checks
- **`.gitguardian.yml`** - GitGuardian configuration
- **`.pre-commit-config.yaml`** - Pre-commit framework config

## Bypassing Hooks (Emergency Only)

⚠️ **Only use in genuine emergencies!**

```bash
# Skip pre-commit hook
git commit --no-verify -m "emergency fix"

# Skip pre-push hook
git push --no-verify origin develop
```

## Troubleshooting

### GitGuardian Not Found
```bash
pipx install ggshield
```

### Hook Permission Issues
```bash
chmod +x .husky/pre-commit
chmod +x .husky/pre-push
```

### False Positives
Edit `.gitguardian.yml` to add patterns to ignore.

## Benefits

✅ **Prevents secrets from ever reaching the repository**
✅ **Catches issues before they become problems**
✅ **Enforces code quality standards**
✅ **Maintains high test coverage**
✅ **Blocks sensitive files**
✅ **No more GitGuardian alerts after the fact**

## Zero Tolerance Policy

**These hooks are NON-NEGOTIABLE.**
- No exceptions for "quick fixes"
- No bypassing for "urgent" commits
- Security comes first, always

---

*As your CTO, I've implemented these hooks to ensure we never deal with security issues after the fact. Prevention is always better than detection.*
