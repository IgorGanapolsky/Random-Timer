#!/bin/bash

# Local Multi-Claude Orchestrator (FREE - runs on your machine)
# Based on Anthropic's best practices: https://www.anthropic.com/engineering/claude-code-best-practices
# NO GITHUB ACTIONS REQUIRED - Zero cost!

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🤖 Local Multi-Claude Orchestrator${NC}"
echo -e "${GREEN}FREE parallel development using git worktrees${NC}"
echo "================================================"

# Configuration
WORKTREE_BASE="/Users/igorganapolsky/workspace/git/apps"
MAIN_REPO="$WORKTREE_BASE/SuperPassword"
ISSUES_FILE="$MAIN_REPO/.claude/active-tasks.md"
SCRATCHPAD="$MAIN_REPO/.claude/scratchpad.md"

# Check if Claude Code is available (optional - for automation)
if command -v claude &> /dev/null; then
    echo -e "${GREEN}✓ Claude Code CLI detected${NC}"
    CLAUDE_AVAILABLE=true
else
    echo -e "${YELLOW}ℹ Claude Code CLI not found - will show manual instructions${NC}"
    CLAUDE_AVAILABLE=false
fi

# Function to assign issue to worktree
assign_task() {
    local worktree=$1
    local issue_number=$2
    local task_description=$3
    
    echo -e "\n${BLUE}Assigning Issue #$issue_number to $worktree${NC}"
    
    # Create task file for Claude
    local task_file="$worktree/.claude-task.md"
    cat > "$task_file" << EOF
# Task Assignment for Claude

**Issue #$issue_number**: $task_description
**Worktree**: $(basename $worktree)
**Branch**: $(cd $worktree && git branch --show-current)

## Instructions for Claude:

1. Read this task carefully
2. Make a plan BEFORE coding (ask for confirmation)
3. Implement the solution
4. Write tests for your changes
5. Update the scratchpad at $SCRATCHPAD with your progress

## Communication:
- Write status updates to: $SCRATCHPAD
- Read feedback from: $MAIN_REPO/.claude/feedback.md
- When complete, mark task done in: $ISSUES_FILE

## Git Commands:
\`\`\`bash
# Check current status
git status

# Stage and commit changes
git add -A
git commit -m "feat: implement #$issue_number"

# Push to remote
git push origin $(cd $worktree && git branch --show-current)
\`\`\`

## Testing Commands:
\`\`\`bash
# Run tests
npm test

# Run specific test
npm test -- --testPathPattern="your-test"

# Check lint
npm run lint
\`\`\`
EOF
    
    echo -e "${GREEN}✓ Task file created: $task_file${NC}"
}

# Function to start Claude in a worktree
start_claude_session() {
    local worktree=$1
    local session_name=$(basename $worktree)
    
    echo -e "\n${BLUE}Starting Claude session: $session_name${NC}"
    
    if [ "$CLAUDE_AVAILABLE" = true ]; then
        # Start Claude Code in the worktree
        echo "cd $worktree && claude --task .claude-task.md"
    else
        # Manual instructions
        cat << EOF

${YELLOW}Manual Claude Setup:${NC}
1. Open a new terminal window
2. cd $worktree
3. Start your Claude interface (Cursor, Continue, etc.)
4. Paste the task from: .claude-task.md
5. Let Claude work on the task

${GREEN}Pro tip: Use multiple terminal tabs/windows for parallel Claudes${NC}
EOF
    fi
}

# Function to setup reviewer Claude
setup_reviewer() {
    echo -e "\n${BLUE}Setting up Reviewer Claude${NC}"
    
    local review_file="$MAIN_REPO/.claude/review-instructions.md"
    cat > "$review_file" << EOF
# Code Review Instructions for Claude

You are the REVIEWER Claude. Your job is to review code from other Claudes.

## Your Tasks:
1. Read the changes in each worktree
2. Check for bugs, security issues, and best practices
3. Write feedback to: $MAIN_REPO/.claude/feedback.md
4. Suggest improvements

## Worktrees to Review:
$(git worktree list | grep -v "SuperPassword " | awk '{print "- " $1}')

## Review Checklist:
- [ ] Code follows TypeScript best practices
- [ ] No security vulnerabilities
- [ ] Tests are included
- [ ] Documentation is updated
- [ ] No console.logs left behind
- [ ] Error handling is proper
- [ ] Performance considerations

## Commands to Review Code:
\`\`\`bash
# Check changes in a worktree
cd /path/to/worktree
git diff develop...HEAD

# Run tests
npm test

# Check for security issues
npm audit
\`\`\`
EOF
    
    echo -e "${GREEN}✓ Review instructions created: $review_file${NC}"
}

# Function to orchestrate multiple Claudes
orchestrate() {
    echo -e "\n${BLUE}🎯 Orchestration Mode${NC}"
    
    # Create Claude directories
    mkdir -p "$MAIN_REPO/.claude"
    
    # Get open issues (locally, no API calls)
    echo -e "\n${YELLOW}Available Tasks:${NC}"
    cat << EOF
1. [#100] Implement biometric authentication
2. [#101] Add end-to-end encryption
3. [#102] Create AI password audit feature
4. [#103] Fix performance issues
5. [#104] Add comprehensive test suite
EOF
    
    echo -e "\n${GREEN}Worktree Assignments:${NC}"
    
    # Example assignments (you can customize)
    assign_task "$WORKTREE_BASE/sp-biometrics" "100" "Implement biometric authentication"
    assign_task "$WORKTREE_BASE/sp-secure-storage" "101" "Add end-to-end encryption"
    assign_task "$WORKTREE_BASE/sp-ai-intelligence" "102" "Create AI password audit feature"
    
    # Setup reviewer
    setup_reviewer
    
    # Create orchestration dashboard
    cat > "$MAIN_REPO/.claude/dashboard.md" << EOF
# 📊 Multi-Claude Orchestration Dashboard
Generated: $(date)

## Active Claude Sessions

| Worktree | Task | Status | Branch |
|----------|------|--------|--------|
| sp-biometrics | #100 Biometrics | 🟡 In Progress | feature/biometrics |
| sp-secure-storage | #101 Encryption | 🟡 In Progress | feature/secure-storage |
| sp-ai-intelligence | #102 AI Audit | 🟡 In Progress | feature/ai-intelligence |
| main-repo | Code Review | 🔍 Reviewing | develop |

## Communication Channels
- **Scratchpad**: .claude/scratchpad.md (shared notes)
- **Feedback**: .claude/feedback.md (review comments)
- **Tasks**: .claude/active-tasks.md (task list)

## Quick Commands

### Start all Claudes (in separate terminals):
\`\`\`bash
# Terminal 1: Biometrics Claude
cd $WORKTREE_BASE/sp-biometrics
# Start Claude with task file

# Terminal 2: Security Claude  
cd $WORKTREE_BASE/sp-secure-storage
# Start Claude with task file

# Terminal 3: AI Claude
cd $WORKTREE_BASE/sp-ai-intelligence
# Start Claude with task file

# Terminal 4: Reviewer Claude
cd $MAIN_REPO
# Start Claude with review instructions
\`\`\`

### Check Progress:
\`\`\`bash
# See all worktree statuses
git worktree list

# Check specific worktree
cd /path/to/worktree && git status

# View scratchpad
cat $SCRATCHPAD
\`\`\`

### Merge Changes:
\`\`\`bash
# After review approval
cd $MAIN_REPO
git checkout develop
git merge feature/biometrics --no-ff
\`\`\`
EOF
    
    echo -e "${GREEN}✓ Dashboard created: $MAIN_REPO/.claude/dashboard.md${NC}"
    
    # Show next steps
    echo -e "\n${BLUE}📋 Next Steps:${NC}"
    echo "1. Open the dashboard: $MAIN_REPO/.claude/dashboard.md"
    echo "2. Start Claude sessions in separate terminals for each worktree"
    echo "3. Each Claude works independently on their task"
    echo "4. Reviewer Claude checks all work"
    echo "5. Merge approved changes back to develop"
    
    echo -e "\n${GREEN}✨ This is 100% FREE - runs locally on your machine!${NC}"
    echo -e "${YELLOW}No GitHub Actions, no cloud costs, just local parallel development${NC}"
}

# Function to check worktree status
check_status() {
    echo -e "\n${BLUE}📊 Worktree Status Check${NC}"
    
    for worktree in $(git worktree list | awk '{print $1}'); do
        if [ -d "$worktree" ]; then
            local branch=$(cd "$worktree" && git branch --show-current 2>/dev/null || echo "unknown")
            local changes=$(cd "$worktree" && git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
            
            if [ "$changes" -gt 0 ]; then
                echo -e "${YELLOW}⚠️  $(basename $worktree): $changes uncommitted changes on $branch${NC}"
            else
                echo -e "${GREEN}✓ $(basename $worktree): clean on $branch${NC}"
            fi
        fi
    done
}

# Function for headless automation (Anthropic best practice)
headless_mode() {
    echo -e "\n${BLUE}🤖 Headless Mode (for automation)${NC}"
    
    local task=$1
    local worktree=$2
    
    if [ "$CLAUDE_AVAILABLE" = true ]; then
        # Run Claude in headless mode
        cd "$worktree" && claude --headless --task "$task" --output .claude-output.md
    else
        echo -e "${YELLOW}Headless mode requires Claude Code CLI${NC}"
        echo "Install: https://github.com/anthropics/claude-code"
    fi
}

# Main menu
show_menu() {
    echo -e "\n${BLUE}Choose an option:${NC}"
    echo "1) Orchestrate multiple Claudes (recommended)"
    echo "2) Check worktree status"
    echo "3) Setup reviewer Claude"
    echo "4) View dashboard"
    echo "5) Emergency stop all"
    echo "6) Exit"
    
    read -p "Enter choice [1-6]: " choice
    
    case $choice in
        1) orchestrate ;;
        2) check_status ;;
        3) setup_reviewer ;;
        4) cat "$MAIN_REPO/.claude/dashboard.md" 2>/dev/null || echo "Dashboard not created yet" ;;
        5) echo -e "${RED}Stopping all Claude processes...${NC}" && pkill -f claude || true ;;
        6) exit 0 ;;
        *) echo -e "${RED}Invalid option${NC}" ;;
    esac
}

# Main execution
if [ "$1" = "--headless" ]; then
    headless_mode "$2" "$3"
elif [ "$1" = "--status" ]; then
    check_status
elif [ "$1" = "--orchestrate" ]; then
    orchestrate
else
    show_menu
fi
