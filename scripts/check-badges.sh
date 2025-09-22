#!/bin/bash

# Badge Health Check Script
# This script tests all badges in the README to identify which ones are working

echo "🔍 Checking badge health for SuperPassword..."
echo "================================================"

# GitHub repository info
REPO="IgorGanapolsky/SuperPassword"
GITHUB_URL="https://github.com/$REPO"

# Function to test badge URL
test_badge() {
    local name="$1"
    local url="$2"
    
    echo -n "Testing $name... "
    
    # Use curl to test the badge URL
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    
    if [ "$response" = "200" ]; then
        echo "✅ Working"
    else
        echo "❌ Failed (HTTP $response)"
        echo "   URL: $url"
    fi
}

# Test each badge
echo ""
test_badge "GitHub Actions" "https://github.com/$REPO/actions/workflows/ci-cd.yml/badge.svg"
test_badge "Codecov" "https://codecov.io/gh/$REPO/branch/main/graph/badge.svg"
test_badge "SonarCloud Quality Gate" "https://sonarcloud.io/api/project_badges/measure?project=IgorGanapolsky_SuperPassword&metric=alert_status"
test_badge "SonarCloud Security" "https://sonarcloud.io/api/project_badges/measure?project=IgorGanapolsky_SuperPassword&metric=security_rating"
test_badge "SonarCloud Maintainability" "https://sonarcloud.io/api/project_badges/measure?project=IgorGanapolsky_SuperPassword&metric=sqale_rating"
test_badge "Snyk Vulnerabilities" "https://snyk.io/test/github/$REPO/badge.svg?targetFile=package.json"

echo ""
echo "🔧 Troubleshooting tips:"
echo "========================"
echo "• GitHub Actions: Check if workflows exist and have run successfully"
echo "• Codecov: Ensure CODECOV_TOKEN is set in repository secrets"
echo "• SonarCloud: Verify project exists at sonarcloud.io and is public"
echo "• Snyk: Check if repository is connected to Snyk account"
echo ""
echo "🔗 Useful links:"
echo "• GitHub Actions: $GITHUB_URL/actions"
echo "• Repository Settings: $GITHUB_URL/settings"
echo "• SonarCloud Project: https://sonarcloud.io/project/overview?id=IgorGanapolsky_SuperPassword"
echo "• Codecov Dashboard: https://codecov.io/gh/$REPO"
