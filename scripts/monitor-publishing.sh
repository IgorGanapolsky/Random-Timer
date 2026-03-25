#!/bin/bash
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}📱 Random Timer Publishing Monitor${NC}"
echo "=================================="

# Check if gh CLI is available
if ! command -v gh &> /dev/null; then
    echo -e "${RED}❌ GitHub CLI (gh) is required but not installed.${NC}"
    echo "   Install from: https://cli.github.com/"
    exit 1
fi

# Get current version info
if [ -f "native-android/app/build.gradle.kts" ]; then
    VERSION_CODE=$(sed -n 's/.*versionCode *= *//p' native-android/app/build.gradle.kts | head -1)
    VERSION_NAME=$(sed -n 's/.*versionName *= *"//p' native-android/app/build.gradle.kts | head -1 | sed 's/"//')
    echo -e "${GREEN}📋 Current Android Version: $VERSION_NAME (code: $VERSION_CODE)${NC}"
fi

if [ -f "native-ios/RandomTimer.xcodeproj/project.pbxproj" ]; then
    IOS_VERSION=$(grep -m1 'MARKETING_VERSION' native-ios/RandomTimer.xcodeproj/project.pbxproj | grep -oP '[\d.]+' || echo "")
    echo -e "${GREEN}📋 Current iOS Version: $IOS_VERSION${NC}"
fi

echo ""
echo -e "${BLUE}🔍 Recent Publishing Activity:${NC}"

# Show recent workflow runs
echo -e "${YELLOW}Workflow Runs (last 10):${NC}"
gh run list --workflow=native-release.yml --limit 10 --json databaseId,status,conclusion,createdAt,event,displayTitle | jq -r '.[] | "\(.createdAt[0:10]) \(.createdAt[11:16]) \(.status) \(.conclusion // "N/A") \(.displayTitle)"' | head -10

echo ""
echo -e "${YELLOW}Auto-publish Workflow Runs (last 5):${NC}"
gh run list --workflow=auto-publish.yml --limit 5 --json databaseId,status,conclusion,createdAt,event,displayTitle | jq -r '.[] | "\(.createdAt[0:10]) \(.createdAt[11:16]) \(.status) \(.conclusion // "N/A") \(.displayTitle)"' | head -5

echo ""
echo -e "${BLUE}📊 Publishing Status Check:${NC}"

# Check if we have the required secrets configured
echo -e "${YELLOW}Secret Configuration:${NC}"
SECRETS=("GOOGLE_PLAY_JSON_KEY" "ANDROID_KEYSTORE_BASE64" "KEYSTORE_PASSWORD" "KEY_ALIAS" "KEY_PASSWORD")
MISSING_SECRETS=0

for secret in "${SECRETS[@]}"; do
    if gh secret list | grep -q "^$secret$"; then
        echo -e "  ✅ $secret"
    else
        echo -e "  ❌ $secret"
        ((MISSING_SECRETS++))
    fi
done

if [ $MISSING_SECRETS -gt 0 ]; then
    echo -e "${RED}⚠️  $MISSING_SECRETS required secrets are missing!${NC}"
    echo "   Run: gh secret set <SECRET_NAME> to add them"
fi

echo ""
echo -e "${BLUE}💡 Quick Actions:${NC}"
echo "  Publish to internal track: ./scripts/publish-android.sh"
echo "  Publish to alpha track:    ./scripts/publish-android.sh --track alpha"
echo "  Force republish:           ./scripts/publish-android.sh --force"
echo "  Check version status:      cd native-android && fastlane check_published"
echo ""
echo -e "${BLUE}📈 Monitor publishing:${NC}"
echo "  View workflow runs:        gh run list --workflow=native-release.yml"
echo "  Watch live progress:       gh run watch --exit-status \$(gh run list --workflow=native-release.yml --limit 1 --json databaseId --jq '.[0].databaseId')"
