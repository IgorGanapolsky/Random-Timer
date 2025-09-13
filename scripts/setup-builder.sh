#!/bin/bash

# Builder Setup Script
# Initializes Builder configuration for reliable CI/CD
# Configures caching, testing, and resource limits

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🏗️ Setting up Builder Configuration${NC}"
echo "========================================="

# 1. Create Builder directories
echo -e "\n${BLUE}Step 1: Creating Builder directories${NC}"
mkdir -p .builder/{cache,reports,logs}
echo -e "${GREEN}✓ Created Builder directories${NC}"

# 2. Set up caching
echo -e "\n${BLUE}Step 2: Setting up caching${NC}"
cat > .builder/cache/config.json << EOF
{
  "enabled": true,
  "paths": [
    "node_modules",
    ".expo",
    "ios/Pods",
    "android/.gradle"
  ],
  "key_template": "v1-{{ checksum 'package-lock.json' }}",
  "restore_keys": ["v1-"],
  "compression": true,
  "max_size": "5G",
  "max_age": "30d"
}
EOF
echo -e "${GREEN}✓ Configured caching${NC}"

# 3. Configure test environment
echo -e "\n${BLUE}Step 3: Configuring test environment${NC}"
cat > .builder/test-config.json << EOF
{
  "runner": "jest",
  "coverage": {
    "provider": "codecov",
    "threshold": 60,
    "exclude": [
      "**/*.d.ts",
      "**/*.test.ts",
      "coverage/**"
    ]
  },
  "timeout": "10m",
  "retry": {
    "count": 2,
    "only_fails": true
  }
}
EOF
echo -e "${GREEN}✓ Configured test environment${NC}"

# 4. Set up performance monitoring
echo -e "\n${BLUE}Step 4: Setting up performance monitoring${NC}"
cat > .builder/perf-config.json << EOF
{
  "metrics": {
    "build_time": true,
    "test_coverage": true,
    "error_rate": true,
    "performance_score": true
  },
  "thresholds": {
    "build_time": "5m",
    "coverage": "60%",
    "error_rate": "5%"
  },
  "alerts": {
    "github_issues": true,
    "slack": false,
    "email": false
  }
}
EOF
echo -e "${GREEN}✓ Configured performance monitoring${NC}"

# 5. Configure resource limits
echo -e "\n${BLUE}Step 5: Configuring resource limits${NC}"
cat > .builder/resource-limits.json << EOF
{
  "build": {
    "timeout": "30m",
    "memory": "4G",
    "cpu": 2
  },
  "test": {
    "timeout": "10m",
    "memory": "2G",
    "cpu": 1
  },
  "concurrent_jobs": 2,
  "queue_timeout": "1h"
}
EOF
echo -e "${GREEN}✓ Configured resource limits${NC}"

# 6. Set up cleanup rules
echo -e "\n${BLUE}Step 6: Setting up cleanup rules${NC}"
cat > .builder/cleanup-rules.json << EOF
{
  "enabled": true,
  "rules": {
    "artifacts": {
      "age": "7d",
      "size": "1G"
    },
    "cache": {
      "age": "30d",
      "size": "5G"
    },
    "logs": {
      "age": "14d",
      "size": "500M"
    }
  },
  "schedule": "0 0 * * *"
}
EOF
echo -e "${GREEN}✓ Configured cleanup rules${NC}"

# 7. Create main Builder script
echo -e "\n${BLUE}Step 7: Creating Builder script${NC}"
cat > scripts/builder.sh << 'EOF'
#!/bin/bash

# Builder Main Script
set -e

COMMAND=$1
shift

case $COMMAND in
  "build")
    # Build the project
    npm ci --legacy-peer-deps
    npm run build --if-present
    ;;
    
  "test")
    # Run tests
    npm test --if-present
    npm run type-check --if-present || npx tsc --noEmit
    ;;
    
  "lint")
    # Run linters
    npm run lint --if-present
    npm run format --if-present
    ;;
    
  "clean")
    # Clean artifacts
    rm -rf build dist .expo android/app/build ios/build
    ;;
    
  "cache")
    # Manage cache
    case $1 in
      "clear")
        rm -rf .builder/cache/*
        ;;
      "status")
        du -sh .builder/cache
        ;;
      *)
        echo "Unknown cache command"
        exit 1
        ;;
    esac
    ;;
    
  "report")
    # Generate reports
    mkdir -p .builder/reports
    if [ -f "coverage/lcov.info" ]; then
      cp coverage/lcov.info .builder/reports/
    fi
    if [ -f "lighthouse-report.json" ]; then
      cp lighthouse-report.json .builder/reports/
    fi
    ;;
    
  *)
    echo "Unknown command: $COMMAND"
    echo "Available commands: build, test, lint, clean, cache, report"
    exit 1
    ;;
esac
EOF
chmod +x scripts/builder.sh
echo -e "${GREEN}✓ Created Builder script${NC}"

# 8. Update package.json scripts
echo -e "\n${BLUE}Step 8: Updating package.json scripts${NC}"
# Note: This requires jq to be installed
if command -v jq &> /dev/null; then
  # Read existing package.json
  TEMP_FILE=$(mktemp)
  jq '.scripts += {
    "builder:build": "./scripts/builder.sh build",
    "builder:test": "./scripts/builder.sh test",
    "builder:lint": "./scripts/builder.sh lint",
    "builder:clean": "./scripts/builder.sh clean",
    "builder:cache": "./scripts/builder.sh cache",
    "builder:report": "./scripts/builder.sh report"
  }' package.json > "$TEMP_FILE"
  mv "$TEMP_FILE" package.json
  echo -e "${GREEN}✓ Updated package.json scripts${NC}"
else
  echo -e "${YELLOW}⚠️ jq not found - skipping package.json update${NC}"
  echo "Please manually add the following scripts to package.json:"
  echo "  \"builder:build\": \"./scripts/builder.sh build\""
  echo "  \"builder:test\": \"./scripts/builder.sh test\""
  echo "  \"builder:lint\": \"./scripts/builder.sh lint\""
  echo "  \"builder:clean\": \"./scripts/builder.sh clean\""
  echo "  \"builder:cache\": \"./scripts/builder.sh cache\""
  echo "  \"builder:report\": \"./scripts/builder.sh report\""
fi

# 9. Create gitignore entries
echo -e "\n${BLUE}Step 9: Updating .gitignore${NC}"
cat >> .gitignore << EOF

# Builder
.builder/cache/
.builder/logs/
.builder/reports/
!.builder/cache/config.json
!.builder/cleanup-rules.json
!.builder/resource-limits.json
!.builder/test-config.json
!.builder/perf-config.json
EOF
echo -e "${GREEN}✓ Updated .gitignore${NC}"

# 10. Generate documentation
echo -e "\n${BLUE}Step 10: Generating documentation${NC}"
mkdir -p docs
cat > docs/BUILDER.md << EOF
# Builder Configuration

## Overview
Builder is configured for optimal CI/CD performance while staying within free tier limits.

## Key Features
- Caching for faster builds
- Resource limits to prevent overruns
- Performance monitoring
- Automatic cleanup

## Commands
- \`npm run builder:build\` - Build project
- \`npm run builder:test\` - Run tests
- \`npm run builder:lint\` - Run linters
- \`npm run builder:clean\` - Clean artifacts
- \`npm run builder:cache\` - Manage cache
- \`npm run builder:report\` - Generate reports

## Resource Limits
- Build: 4G RAM, 2 CPUs, 30m timeout
- Test: 2G RAM, 1 CPU, 10m timeout
- Cache: 5G max size, 30d retention

## Cleanup Rules
- Artifacts: 7d retention, 1G max
- Cache: 30d retention, 5G max
- Logs: 14d retention, 500M max

## Monitor Usage
Check Builder status:
\`\`\`bash
# View cache status
npm run builder:cache status

# Generate reports
npm run builder:report
\`\`\`
EOF
echo -e "${GREEN}✓ Generated documentation${NC}"

echo -e "\n${GREEN}✅ Builder setup complete!${NC}"
echo ""
echo "Documentation: docs/BUILDER.md"
echo "Configuration: .builder/"
echo "Main script: scripts/builder.sh"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Review docs/BUILDER.md"
echo "2. Test the setup: npm run builder:build"
echo "3. Monitor usage: npm run builder:cache status"
