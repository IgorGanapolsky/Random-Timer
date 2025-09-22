# 🏆 Badge Setup Guide

This guide helps you configure all the CI/CD badges for the SuperPassword project.

## 🚀 Quick Fix

The main issues with your badges have been resolved:

1. **GitHub Actions Badge**: Fixed workflow name reference
2. **Codecov Badge**: Updated to use `main` branch instead of `develop`
3. **Snyk Badge**: Added `targetFile=package.json` parameter

## 🔧 Badge Status & Setup

### ✅ Working Badges (No Setup Required)

These badges should work immediately:

- **License Badge**: Static badge, always works
- **PRs Welcome Badge**: Static badge, always works

### 🔄 Requires Setup

These badges need external service configuration:

#### 1. GitHub Actions Badge
- **Status**: Should work if workflows exist
- **URL**: `https://github.com/IgorGanapolsky/SuperPassword/actions/workflows/ci-cd.yml/badge.svg`
- **Setup**: Ensure your `ci-cd.yml` workflow runs successfully

#### 2. Codecov Badge
- **Status**: Requires Codecov account setup
- **URL**: `https://codecov.io/gh/IgorGanapolsky/SuperPassword/branch/main/graph/badge.svg`
- **Setup**:
  1. Sign up at [codecov.io](https://codecov.io)
  2. Connect your GitHub repository
  3. Add `CODECOV_TOKEN` to GitHub repository secrets
  4. Ensure your CI uploads coverage reports

#### 3. SonarCloud Badges
- **Status**: Requires SonarCloud project setup
- **URLs**: Multiple badges for quality metrics
- **Setup**:
  1. Sign up at [sonarcloud.io](https://sonarcloud.io)
  2. Import your GitHub repository
  3. Ensure project key matches: `IgorGanapolsky_SuperPassword`
  4. Run analysis via GitHub Actions or manually

#### 4. Snyk Badge
- **Status**: Requires Snyk account setup
- **URL**: `https://snyk.io/test/github/IgorGanapolsky/SuperPassword/badge.svg?targetFile=package.json`
- **Setup**:
  1. Sign up at [snyk.io](https://snyk.io)
  2. Connect your GitHub repository
  3. Add `SNYK_TOKEN` to GitHub repository secrets

## 🧪 Testing Your Badges

Run the badge health check script:

```bash
./scripts/check-badges.sh
```

This will test all badge URLs and show which ones are working.

## 🔄 Alternative Badge Options

If external services fail, you can use these alternatives:

### GitHub-based Badges (Always Reliable)

```markdown
[![Build](https://img.shields.io/github/actions/workflow/status/IgorGanapolsky/SuperPassword/ci-cd.yml?branch=main&label=build)](https://github.com/IgorGanapolsky/SuperPassword/actions)
[![Tests](https://img.shields.io/github/actions/workflow/status/IgorGanapolsky/SuperPassword/ci-cd.yml?branch=main&label=tests)](https://github.com/IgorGanapolsky/SuperPassword/actions)
[![CodeQL](https://github.com/IgorGanapolsky/SuperPassword/actions/workflows/codeql.yml/badge.svg)](https://github.com/IgorGanapolsky/SuperPassword/actions/workflows/codeql.yml)
[![Last Commit](https://img.shields.io/github/last-commit/IgorGanapolsky/SuperPassword)](https://github.com/IgorGanapolsky/SuperPassword/commits)
[![Issues](https://img.shields.io/github/issues/IgorGanapolsky/SuperPassword)](https://github.com/IgorGanapolsky/SuperPassword/issues)
[![Pull Requests](https://img.shields.io/github/issues-pr/IgorGanapolsky/SuperPassword)](https://github.com/IgorGanapolsky/SuperPassword/pulls)
```

### Static Badges for Project Info

```markdown
[![React Native](https://img.shields.io/badge/React%20Native-0.72-blue)](https://reactnative.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue)](https://www.typescriptlang.org/)
[![Platform](https://img.shields.io/badge/Platform-iOS%20%7C%20Android-lightgrey)](https://reactnative.dev/)
[![Node](https://img.shields.io/badge/Node-%3E%3D18-green)](https://nodejs.org/)
```

## 🛠️ Service Setup Instructions

### Codecov Setup

1. Visit [codecov.io](https://codecov.io) and sign in with GitHub
2. Add your repository
3. Copy the upload token
4. Add `CODECOV_TOKEN` to your GitHub repository secrets:
   - Go to Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `CODECOV_TOKEN`
   - Value: Your token from Codecov

### SonarCloud Setup

1. Visit [sonarcloud.io](https://sonarcloud.io) and sign in with GitHub
2. Import your repository
3. Configure the project:
   - Project key: `IgorGanapolsky_SuperPassword`
   - Organization: `igorganapol` (or create new)
4. Add analysis to your CI workflow (already configured in `ci-cd.yml`)

### Snyk Setup

1. Visit [snyk.io](https://snyk.io) and sign in with GitHub
2. Import your repository
3. Get your auth token from Account Settings
4. Add `SNYK_TOKEN` to your GitHub repository secrets

## 🔍 Troubleshooting

### Badge Shows "Unknown" or "Error"

1. **Check service status**: Visit the service website
2. **Verify configuration**: Ensure tokens are set correctly
3. **Check permissions**: Ensure the service can access your repository
4. **Review logs**: Check GitHub Actions logs for errors

### Badge Shows "Failing"

1. **GitHub Actions**: Check workflow runs in the Actions tab
2. **Codecov**: Ensure coverage reports are being uploaded
3. **SonarCloud**: Check if analysis is running successfully
4. **Snyk**: Verify the scan completed without errors

### Private Repository Issues

Some services may not work with private repositories on free plans:
- Codecov: Limited for private repos
- SonarCloud: Requires paid plan for private repos
- Snyk: Limited scans for private repos

## 📝 Badge Maintenance

The `update-badges.yml` workflow automatically updates badges every 10 minutes. If you need to modify badge behavior:

1. Edit `.github/workflows/update-badges.yml`
2. Modify the badge generation logic
3. Test with `workflow_dispatch` trigger

## 🎯 Best Practices

1. **Keep badges relevant**: Only show badges that provide value
2. **Order by importance**: Most critical badges first
3. **Use consistent styling**: Stick to one badge style/color scheme
4. **Monitor regularly**: Check badge health periodically
5. **Have fallbacks**: Keep alternative badges ready

## 🔗 Useful Links

- [Shields.io](https://shields.io/) - Custom badge generator
- [GitHub Badge Examples](https://github.com/badges/shields)
- [Badge Best Practices](https://github.com/badges/shields/blob/master/doc/TUTORIAL.md)
