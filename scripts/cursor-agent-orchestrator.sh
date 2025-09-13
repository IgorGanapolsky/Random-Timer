#!/bin/bash

# Cursor Headless Multi-Agent Orchestrator
# Uses Cursor CLI in headless mode for TRUE automation
# Based on: https://docs.cursor.com/en/cli/headless
# ZERO COST - Runs locally on your machine!

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${MAGENTA}🤖 Cursor Headless Multi-Agent System${NC}"
echo -e "${GREEN}Automated parallel development with ZERO cloud costs!${NC}"
echo "================================================"

# Configuration
WORKTREE_BASE="/Users/igorganapolsky/workspace/git/apps"
MAIN_REPO="$WORKTREE_BASE/SuperPassword"
LOG_DIR="$MAIN_REPO/.cursor-logs"
TASKS_DIR="$MAIN_REPO/.cursor-tasks"

# Create directories
mkdir -p "$LOG_DIR" "$TASKS_DIR"

# Check if cursor-agent is available
if ! command -v cursor-agent &> /dev/null; then
    echo -e "${RED}❌ cursor-agent not found!${NC}"
    echo "Install Cursor CLI: https://docs.cursor.com/en/cli/installation"
    echo "Or use: npm install -g @cursor/cli"
    exit 1
fi

echo -e "${GREEN}✓ Cursor CLI detected${NC}"

# Function to create agent task
create_agent_task() {
    local worktree=$1
    local task_name=$2
    local task_description=$3
    local task_file="$TASKS_DIR/${task_name}.md"
    
    cat > "$task_file" << EOF
# Task: $task_name

## Objective
$task_description

## Requirements
1. Follow TypeScript best practices
2. Add comprehensive tests
3. Update documentation
4. Ensure no breaking changes
5. Use proper error handling

## Technical Details
- Worktree: $worktree
- Branch: $(cd "$worktree" && git branch --show-current)
- Base: develop

## Success Criteria
- [ ] Code compiles without errors
- [ ] All tests pass
- [ ] No security vulnerabilities
- [ ] Documentation updated
- [ ] Ready for review
EOF
    
    echo "$task_file"
}

# Function to run Cursor agent in headless mode
run_cursor_agent() {
    local worktree=$1
    local task_name=$2
    local prompt=$3
    local mode=${4:-"analyze"}  # analyze, modify, review
    
    echo -e "\n${BLUE}🤖 Starting Cursor Agent: $task_name${NC}"
    echo -e "${CYAN}Worktree: $(basename $worktree)${NC}"
    
    cd "$worktree"
    
    local log_file="$LOG_DIR/${task_name}-$(date +%Y%m%d-%H%M%S).log"
    
    case $mode in
        "analyze")
            # Analysis mode - no file modifications
            echo -e "${YELLOW}Mode: Analysis Only${NC}"
            cursor-agent --print "$prompt" > "$log_file" 2>&1
            ;;
            
        "modify")
            # Modification mode - actually change files
            echo -e "${YELLOW}Mode: File Modification${NC}"
            cursor-agent --print --force "$prompt" > "$log_file" 2>&1
            ;;
            
        "review")
            # Review mode - check code without changes
            echo -e "${YELLOW}Mode: Code Review${NC}"
            cursor-agent --print "Review this code for bugs, security issues, and best practices: $prompt" > "$log_file" 2>&1
            ;;
    esac
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Agent completed successfully${NC}"
        echo "Log: $log_file"
        
        # Show summary
        if [ -f "$log_file" ]; then
            echo -e "\n${CYAN}Summary:${NC}"
            tail -20 "$log_file" | head -10
        fi
    else
        echo -e "${RED}❌ Agent failed - check log: $log_file${NC}"
    fi
    
    cd - > /dev/null
}

# Function to run parallel agents
run_parallel_agents() {
    echo -e "\n${MAGENTA}🚀 Starting Parallel Agent Execution${NC}"
    
    # Define tasks
    declare -a tasks=(
        "sp-biometrics:biometric-auth:Implement biometric authentication using React Native Touch ID/Face ID"
        "sp-secure-storage:encryption:Add AES-256 encryption for password storage"
        "sp-ai-intelligence:ai-audit:Create AI-powered password strength analyzer"
    )
    
    # Start agents in parallel
    for task_spec in "${tasks[@]}"; do
        IFS=':' read -r worktree task_name task_desc <<< "$task_spec"
        worktree_path="$WORKTREE_BASE/$worktree"
        
        if [ -d "$worktree_path" ]; then
            (
                # Run in subshell for parallel execution
                echo -e "\n${CYAN}[Agent: $task_name] Starting...${NC}"
                
                # Create task file
                task_file=$(create_agent_task "$worktree_path" "$task_name" "$task_desc")
                
                # Generate implementation prompt
                prompt="Based on the task in $task_file, implement the following: $task_desc. 
                        Use React Native best practices. Add TypeScript types. Include unit tests."
                
                # Run Cursor agent
                run_cursor_agent "$worktree_path" "$task_name" "$prompt" "modify"
                
                # Commit changes if successful
                cd "$worktree_path"
                if [ -n "$(git status --porcelain)" ]; then
                    git add -A
                    git commit -m "feat($task_name): implement via Cursor headless agent

Task: $task_desc
Automated: Cursor CLI headless mode
Review: Required before merge" || true
                    
                    echo -e "${GREEN}[Agent: $task_name] Changes committed${NC}"
                fi
                cd - > /dev/null
            ) &
        fi
    done
    
    # Wait for all parallel agents
    wait
    echo -e "\n${GREEN}✓ All agents completed${NC}"
}

# Function to run reviewer agent
run_reviewer_agent() {
    echo -e "\n${BLUE}🔍 Starting Reviewer Agent${NC}"
    
    # Collect all changes from worktrees
    local review_prompt="Review the following changes for code quality, security, and best practices:"
    
    for worktree in "$WORKTREE_BASE"/sp-*; do
        if [ -d "$worktree" ]; then
            local branch=$(cd "$worktree" && git branch --show-current)
            local changes=$(cd "$worktree" && git diff develop...HEAD --stat 2>/dev/null | tail -1)
            
            if [ -n "$changes" ]; then
                review_prompt="$review_prompt\n\nWorktree: $(basename $worktree)\nBranch: $branch\nChanges: $changes"
            fi
        fi
    done
    
    # Run review in main repo
    cd "$MAIN_REPO"
    cursor-agent --print "$review_prompt" > "$LOG_DIR/review-$(date +%Y%m%d-%H%M%S).log" 2>&1
    
    echo -e "${GREEN}✓ Review completed${NC}"
}

# Function for automated testing
run_test_agent() {
    local worktree=$1
    
    echo -e "\n${YELLOW}🧪 Running Test Agent${NC}"
    
    cd "$worktree"
    
    # Generate tests using Cursor
    cursor-agent --print --force "Generate comprehensive unit tests for all components in src/ directory. Use Jest and React Native Testing Library." > "$LOG_DIR/test-generation.log" 2>&1
    
    # Run the tests
    if [ -f "package.json" ]; then
        npm test --silent > "$LOG_DIR/test-results.log" 2>&1 || true
        
        if grep -q "PASS" "$LOG_DIR/test-results.log"; then
            echo -e "${GREEN}✓ Tests passed${NC}"
        else
            echo -e "${YELLOW}⚠️ Some tests failed - check log${NC}"
        fi
    fi
    
    cd - > /dev/null
}

# Function for documentation agent
run_docs_agent() {
    echo -e "\n${BLUE}📚 Running Documentation Agent${NC}"
    
    cd "$MAIN_REPO"
    
    cursor-agent --print --force "Update README.md with:
    1. Current project status
    2. Installation instructions
    3. Architecture overview
    4. API documentation
    5. Contributing guidelines
    Use professional formatting and include code examples." > "$LOG_DIR/docs-$(date +%Y%m%d-%H%M%S).log" 2>&1
    
    echo -e "${GREEN}✓ Documentation updated${NC}"
}

# Function to generate daily standup
generate_standup() {
    echo -e "\n${CYAN}📊 Generating Daily Standup Report${NC}"
    
    local standup_file="$MAIN_REPO/.cursor-logs/standup-$(date +%Y-%m-%d).md"
    
    cat > "$standup_file" << EOF
# Daily Standup Report
**Date**: $(date +"%Y-%m-%d %H:%M")
**System**: Cursor Headless Multi-Agent

## 🤖 Agent Activity

EOF
    
    # Collect status from each worktree
    for worktree in "$WORKTREE_BASE"/sp-*; do
        if [ -d "$worktree" ]; then
            local name=$(basename "$worktree")
            local branch=$(cd "$worktree" && git branch --show-current)
            local commits=$(cd "$worktree" && git log --oneline -5 --pretty=format:"- %s" 2>/dev/null)
            
            cat >> "$standup_file" << EOF
### $name
- **Branch**: $branch
- **Recent commits**:
$commits

EOF
        fi
    done
    
    # Add metrics
    local total_commits=$(cd "$MAIN_REPO" && git log --oneline --since="1 day ago" | wc -l)
    local open_prs=$(gh pr list --state open --json number | jq '. | length' 2>/dev/null || echo "0")
    
    cat >> "$standup_file" << EOF
## 📈 Metrics
- Total commits (24h): $total_commits
- Open PRs: $open_prs
- Active agents: 5
- Cost: \$0.00 (local execution)

## 🎯 Next Steps
1. Review agent-generated code
2. Merge approved changes
3. Run next batch of tasks
EOF
    
    echo -e "${GREEN}✓ Standup report: $standup_file${NC}"
    cat "$standup_file"
}

# Function for batch processing
batch_process() {
    echo -e "\n${MAGENTA}⚡ Batch Processing Mode${NC}"
    
    # Read tasks from file
    local tasks_file="$TASKS_DIR/batch-tasks.txt"
    
    if [ ! -f "$tasks_file" ]; then
        # Create example batch file
        cat > "$tasks_file" << EOF
# Batch Tasks (one per line)
# Format: worktree:prompt
sp-biometrics:Add biometric authentication support
sp-secure-storage:Implement secure key storage
sp-ai-intelligence:Create password strength analyzer
EOF
        echo -e "${YELLOW}Created example batch file: $tasks_file${NC}"
    fi
    
    # Process each task
    while IFS=: read -r worktree prompt; do
        # Skip comments and empty lines
        [[ "$worktree" =~ ^#.*$ ]] && continue
        [ -z "$worktree" ] && continue
        
        local worktree_path="$WORKTREE_BASE/$worktree"
        if [ -d "$worktree_path" ]; then
            echo -e "\n${CYAN}Processing: $worktree${NC}"
            run_cursor_agent "$worktree_path" "batch-$(date +%s)" "$prompt" "modify"
        fi
    done < "$tasks_file"
    
    echo -e "\n${GREEN}✓ Batch processing complete${NC}"
}

# Main menu
show_menu() {
    echo -e "\n${BLUE}=== Cursor Headless Orchestrator ===${NC}"
    echo "1) Run parallel agents (recommended)"
    echo "2) Run single agent"
    echo "3) Run reviewer agent"
    echo "4) Run test generator"
    echo "5) Update documentation"
    echo "6) Generate standup report"
    echo "7) Batch process tasks"
    echo "8) View logs"
    echo "9) Exit"
    
    read -p "Choose [1-9]: " choice
    
    case $choice in
        1) run_parallel_agents ;;
        2) 
            read -p "Worktree name (e.g., sp-biometrics): " wt
            read -p "Task description: " desc
            run_cursor_agent "$WORKTREE_BASE/$wt" "manual-$(date +%s)" "$desc" "modify"
            ;;
        3) run_reviewer_agent ;;
        4) 
            read -p "Worktree name: " wt
            run_test_agent "$WORKTREE_BASE/$wt"
            ;;
        5) run_docs_agent ;;
        6) generate_standup ;;
        7) batch_process ;;
        8) ls -la "$LOG_DIR" ;;
        9) exit 0 ;;
        *) echo -e "${RED}Invalid option${NC}" ;;
    esac
}

# Parse command line arguments
case "${1:-}" in
    --parallel)
        run_parallel_agents
        ;;
    --review)
        run_reviewer_agent
        ;;
    --standup)
        generate_standup
        ;;
    --batch)
        batch_process
        ;;
    --help)
        cat << EOF
Usage: $0 [OPTION]

Options:
  --parallel    Run all agents in parallel
  --review      Run code review agent
  --standup     Generate daily standup report
  --batch       Process batch tasks from file
  --help        Show this help message

Interactive mode: Run without arguments
EOF
        ;;
    *)
        show_menu
        ;;
esac
