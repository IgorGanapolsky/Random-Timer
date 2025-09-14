#!/bin/bash

# Master script to set up AI-augmented development infrastructure
# Requires GitHub CLI and appropriate permissions

echo "🚀 Setting up SuperPassword AI Infrastructure..."

# 1. Create Claude agent directories
echo "📂 Creating Claude agent directories..."
mkdir -p ../claude-agents

# Function to create agent workspace
create_agent_workspace() {
    agent="$1"
    agent_dir="../claude-agents/$agent"
    
    # Skip if directory exists
    if [ -d "$agent_dir" ]; then
        echo "✓ Agent workspace already exists: $agent"
        return
    }
    
    # Create worktree
    git worktree add "$agent_dir" develop -b "claude/$agent" || true
    
    # Create docs directory
    mkdir -p "$agent_dir/docs"
    
    # Convert agent name to title case
    title="$(echo "$agent" | sed -e 's/-/ /g' -e 's/\([a-z]\)\([a-zA-Z0-9]\)/\1 \2/g' | awk '{for(i=1;i<=NF;i++)sub(/./,toupper(substr($i,1,1)),$i)}1')"
    
    # Create agent documentation
    cat > "$agent_dir/docs/AGENT_README.md" << EOF
# Claude $title Agent

## Role
Specialized $title agent for SuperPassword development.

## Responsibilities
- See main PROJECT_MANAGEMENT.md
- Maintain context in this workspace
- Update status in issues
- Generate metrics

## Workspace
- Branch: claude/$agent
- Directory: $(pwd)/$agent_dir
- Documentation: ./docs/

## Integration
- Project Board: $title column
- Labels: claude/$agent
- Metrics: Daily reporting
EOF
    
    echo "✓ Created workspace for $agent"
}

# Create workspaces for each agent
for agent in refactoring testing security-audit api-docs ui-enhancements architect; do
    create_agent_workspace "$agent"
done

# 2. Create required directories
echo "📁 Creating infrastructure directories..."
mkdir -p .github/{metrics,agent-automation,monitoring,quality-gates}

# 3. Set up metrics collection
echo "📈 Setting up metrics collection..."
cat > .github/metrics/config.yml << 'EOF'
# Metrics Collection Configuration
collection:
  interval: 10m
  retention: 90d
  
agents:
  metrics:
    - completion_rate
    - response_time
    - code_quality_impact
    - test_coverage_delta
    
  dashboards:
    - agent_performance
    - project_velocity
    - quality_metrics
EOF

# 4. Set up agent automation
echo "⚙️ Setting up agent automation..."
cat > .github/agent-automation/config.yml << 'EOF'
# Agent Automation Configuration
agents:
  architect:
    priority: 1
    capabilities:
      - system_design
      - task_breakdown
    files:
      - "**/*.arch.md"
      - "**/architecture/**"
      
  refactor:
    priority: 2
    capabilities:
      - code_quality
      - performance
    files:
      - "**/*.{ts,js,go,swift}"
      
  testing:
    priority: 2
    capabilities:
      - test_coverage
      - quality_assurance
    files:
      - "**/*.test.{ts,js,go,swift}"
      - "**/__tests__/**"
      
  security:
    priority: 1
    capabilities:
      - security_audit
      - vulnerability_assessment
    files:
      - "**/security/**"
      - "**/auth/**"
      
  docs:
    priority: 3
    capabilities:
      - documentation
      - api_specs
    files:
      - "**/*.md"
      - "**/docs/**"
      - "**/api/**"
      
  design:
    priority: 2
    capabilities:
      - ui_ux
      - accessibility
    files:
      - "**/*.{css,scss}"
      - "**/components/**"
      
workload:
  max_per_agent: 5
  rebalance_interval: 4h
  priority_boost: 24h
EOF

# 5. Set up monitoring
echo "👀 Setting up monitoring..."
cat > .github/monitoring/config.yml << 'EOF'
# AI System Monitoring
metrics:
  collection:
    interval: 1m
    retention: 30d
    
  alerts:
    - name: agent_overload
      condition: "tasks > 5"
      channels: ["github"]
      
    - name: stale_tasks
      condition: "age > 48h"
      channels: ["github"]
      
    - name: quality_gate_failure
      condition: "checks.failed > 0"
      channels: ["github"]
      
dashboards:
  - name: agent_performance
    refresh: 5m
    panels:
      - tasks_per_agent
      - completion_rate
      - quality_metrics
      
  - name: system_health
    refresh: 1m
    panels:
      - agent_status
      - queue_length
      - response_time
EOF

# 6. Set up quality gates
echo "🔍 Setting up quality gates..."
cat > .github/quality-gates/config.yml << 'EOF'
# Quality Gate Configuration
gates:
  - name: code_quality
    checks:
      - type: test_coverage
        threshold: 80
      - type: code_duplication
        threshold: 3
      - type: complexity
        threshold: 15
        
  - name: security
    checks:
      - type: vulnerability_scan
        threshold: 0
      - type: dependency_check
        threshold: 0
        
  - name: performance
    checks:
      - type: response_time
        threshold: 200ms
      - type: memory_usage
        threshold: 100mb
        
auto_merge:
  enabled: true
  conditions:
    - all_checks_pass
    - approved_by_agent
    - no_conflicts
EOF

# 7. Set up git hooks
echo "🎯 Setting up git hooks..."
mkdir -p .husky
cat > .husky/pre-commit << 'EOF'
#!/bin/sh
. "$(dirname "$0")/_/husky.sh"

# Run quality checks
npm run lint || exit 1
npm run test || exit 1
EOF

chmod +x .husky/pre-commit

# 8. Set up dev container
echo "🐳 Setting up dev container..."
mkdir -p .devcontainer
cat > .devcontainer/devcontainer.json << 'EOF'
{
  "name": "SuperPassword AI Development",
  "image": "mcr.microsoft.com/devcontainers/typescript-node:20",
  "features": {
    "ghcr.io/devcontainers/features/github-cli:1": {},
    "ghcr.io/devcontainers/features/docker-in-docker:2": {}
  },
  "customizations": {
    "vscode": {
      "extensions": [
        "github.copilot",
        "github.vscode-github-actions",
        "ms-azuretools.vscode-docker"
      ]
    }
  },
  "postCreateCommand": "npm install"
}
EOF

echo "✨ AI infrastructure setup complete!"
echo ""
echo "Next steps:"
echo "1. Review project board: https://github.com/IgorGanapolsky/projects/3"
echo "2. Check agent workspaces in ../claude-agents/"
echo "3. Monitor metrics dashboards"
echo "4. Review automation rules"
echo ""
echo "🤖 System is ready for AI-augmented development!"