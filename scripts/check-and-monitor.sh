#!/bin/bash
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 Running Android Lint Check and Publishing Monitor${NC}"
echo "======================================================"

# Check Android lint
echo -e "${YELLOW}Running Android Lint...${NC}"
if cd native-android && ./gradlew lint; then
    echo -e "${GREEN}✅ Android lint passed${NC}"
else
    echo -e "${RED}❌ Android lint failed${NC}"
    exit 1
fi

# Return to project root
cd ..

# Run publishing monitor
echo ""
echo -e "${YELLOW}Running Publishing Monitor...${NC}"
if ./scripts/monitor-publishing.sh; then
    echo -e "${GREEN}✅ Publishing monitor completed${NC}"
else
    echo -e "${RED}❌ Publishing monitor failed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}${BOLD}✅ All checks completed successfully!${NC}"
