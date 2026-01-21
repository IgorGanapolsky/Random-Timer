#!/bin/bash
# Parallel Claude Sessions - Autonomous Worktree Manager
# Inspired by Boris Cherny's workflow (Claude Code creator)
#
# Usage:
#   parallel-claude.sh spawn <task-description> [work-item-id]
#   parallel-claude.sh list
#   parallel-claude.sh cleanup
#
# LOCAL ONLY - Do not commit to repository

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

GIT_ROOT=$(git rev-parse --show-toplevel)
WORKTREE_DIR="$GIT_ROOT/.worktrees"
SESSION_LOG="$GIT_ROOT/.claude/memory/parallel-sessions.json"

# Ensure directories exist
mkdir -p "$WORKTREE_DIR" "$(dirname "$SESSION_LOG")"

# Ensure .worktrees is in .gitignore
if ! grep -q "^\.worktrees$" "$GIT_ROOT/.gitignore" 2>/dev/null; then
    echo ".worktrees" >> "$GIT_ROOT/.gitignore"
fi

# Generate branch name from description
generate_branch_name() {
    local description="$1"
    local work_item="${2:-}"

    # Convert to lowercase, replace spaces with hyphens, remove special chars
    local slug=$(echo "$description" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | sed 's/[^a-z0-9-]//g' | cut -c1-30)

    if [[ -n "$work_item" ]]; then
        echo "feature/${work_item}-${slug}"
    else
        # Use timestamp if no work item
        echo "feature/parallel-$(date +%s)-${slug}"
    fi
}

# Copy env and claude config to worktree
setup_worktree_env() {
    local worktree_path="$1"

    echo -e "${BLUE}Setting up worktree environment...${NC}"

    # Copy .env files
    for f in "$GIT_ROOT"/.env*; do
        if [[ -f "$f" && "$(basename "$f")" != ".env.example" ]]; then
            cp "$f" "$worktree_path/"
            echo -e "  ${GREEN}✓ Copied $(basename "$f")${NC}"
        fi
    done

    # Ensure .claude directory structure exists
    mkdir -p "$worktree_path/.claude/memory"

    # Symlink shared memory (so all sessions share lessons)
    if [[ -d "$GIT_ROOT/.claude/memory/feedback" ]]; then
        ln -sf "$GIT_ROOT/.claude/memory/feedback" "$worktree_path/.claude/memory/feedback" 2>/dev/null || true
        echo -e "  ${GREEN}✓ Linked shared memory${NC}"
    fi

    # Copy CLAUDE.md
    if [[ -f "$GIT_ROOT/CLAUDE.md" ]]; then
        cp "$GIT_ROOT/CLAUDE.md" "$worktree_path/"
        echo -e "  ${GREEN}✓ Copied CLAUDE.md${NC}"
    fi
}

# Spawn a new parallel Claude session
spawn_session() {
    local description="$1"
    local work_item="${2:-}"

    if [[ -z "$description" ]]; then
        echo -e "${RED}Error: Task description required${NC}"
        echo "Usage: parallel-claude.sh spawn \"implement user auth\" [work-item-id]"
        exit 1
    fi

    local branch_name=$(generate_branch_name "$description" "$work_item")
    local worktree_path="$WORKTREE_DIR/$(basename "$branch_name")"

    echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║  PARALLEL CLAUDE SESSION                                    ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}Task:${NC} $description"
    echo -e "${BLUE}Branch:${NC} $branch_name"
    echo -e "${BLUE}Path:${NC} $worktree_path"
    [[ -n "$work_item" ]] && echo -e "${BLUE}Work Item:${NC} AB#$work_item"
    echo ""

    # Check if worktree already exists
    if [[ -d "$worktree_path" ]]; then
        echo -e "${YELLOW}Worktree already exists. Opening existing session...${NC}"
    else
        # Update develop branch
        echo -e "${BLUE}Updating develop branch...${NC}"
        git fetch origin develop 2>/dev/null || true

        # Create worktree
        echo -e "${BLUE}Creating worktree...${NC}"
        git worktree add -b "$branch_name" "$worktree_path" origin/develop 2>/dev/null || \
        git worktree add -b "$branch_name" "$worktree_path" develop

        # Setup environment
        setup_worktree_env "$worktree_path"
    fi

    # Log session
    local session_id=$(date +%s)
    local session_entry="{\"id\":\"$session_id\",\"branch\":\"$branch_name\",\"path\":\"$worktree_path\",\"task\":\"$description\",\"work_item\":\"$work_item\",\"started\":\"$(date -Iseconds)\",\"status\":\"active\"}"

    if [[ -f "$SESSION_LOG" ]]; then
        # Append to existing log
        jq --argjson entry "$session_entry" '.sessions += [$entry]' "$SESSION_LOG" > "${SESSION_LOG}.tmp" && mv "${SESSION_LOG}.tmp" "$SESSION_LOG"
    else
        echo "{\"sessions\":[$session_entry]}" > "$SESSION_LOG"
    fi

    echo ""
    echo -e "${GREEN}✓ Worktree ready!${NC}"
    echo ""
    echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}Opening new terminal with Claude Code...${NC}"
    echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"

    # Create the prompt file for Claude
    local prompt_file="$worktree_path/.claude-task.md"
    cat > "$prompt_file" << EOF
# Task for this session

**Description:** $description
**Branch:** $branch_name
**Work Item:** ${work_item:-"None - create one if needed"}

## Instructions

1. Implement the task described above
2. Write tests (80% coverage required)
3. Run \`npm test\` to verify
4. Commit with proper message (AB# will be auto-added from branch name)
5. Push and create a DRAFT PR

## When Done

Run: \`parallel-claude.sh complete\` to mark this session complete
EOF

    # Open new iTerm window with Claude Code
    osascript << EOF
tell application "iTerm"
    create window with default profile
    tell current session of current window
        write text "cd '$worktree_path' && echo '📋 Task: $description' && echo '' && cat .claude-task.md && echo '' && echo '🚀 Starting Claude Code...' && claude"
    end tell
end tell
EOF

    echo ""
    echo -e "${GREEN}✓ New Claude session spawned in iTerm!${NC}"
    echo ""
    echo -e "This terminal remains on: ${BLUE}$(git rev-parse --abbrev-ref HEAD)${NC}"
    echo -e "New session is on: ${BLUE}$branch_name${NC}"
    echo ""
}

# List active parallel sessions
list_sessions() {
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║  PARALLEL CLAUDE SESSIONS                                   ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    # List from git worktrees
    echo -e "${BLUE}Active Worktrees:${NC}"
    git worktree list | while read -r line; do
        if [[ "$line" == *".worktrees"* ]]; then
            local path=$(echo "$line" | awk '{print $1}')
            local branch=$(echo "$line" | awk '{print $3}' | tr -d '[]')
            local name=$(basename "$path")
            echo -e "  ${GREEN}●${NC} $name"
            echo -e "    Branch: $branch"
            echo -e "    Path: $path"

            # Check if Claude is running in this worktree
            if pgrep -f "claude.*$path" > /dev/null 2>&1; then
                echo -e "    Status: ${GREEN}Claude running${NC}"
            else
                echo -e "    Status: ${YELLOW}Idle${NC}"
            fi
            echo ""
        fi
    done

    # Count
    local count=$(git worktree list | grep -c ".worktrees" || echo "0")
    echo -e "${BLUE}Total parallel sessions: $count${NC}"
    echo ""

    # Main repo status
    echo -e "${BLUE}Main Repository:${NC}"
    echo -e "  Branch: $(git rev-parse --abbrev-ref HEAD)"
    echo -e "  Path: $GIT_ROOT"
    echo ""
}

# Mark current session as complete
complete_session() {
    local current_path=$(pwd)

    if [[ "$current_path" != *".worktrees"* ]]; then
        echo -e "${YELLOW}Not in a parallel session worktree.${NC}"
        echo "Run this from within a worktree to mark it complete."
        return 1
    fi

    local branch=$(git rev-parse --abbrev-ref HEAD)

    echo -e "${GREEN}Marking session complete: $branch${NC}"

    # Check for uncommitted changes
    if [[ -n $(git status --porcelain) ]]; then
        echo -e "${YELLOW}Warning: You have uncommitted changes!${NC}"
        git status --short
        echo ""
        echo "Commit before completing? (y/n)"
        read -r response
        if [[ "$response" == "y" ]]; then
            git add -A
            git commit -m "Complete parallel session work"
        fi
    fi

    # Check if pushed
    if ! git log origin/$branch..HEAD --oneline 2>/dev/null | head -1 > /dev/null; then
        echo -e "${YELLOW}Branch not pushed. Push now? (y/n)${NC}"
        read -r response
        if [[ "$response" == "y" ]]; then
            git push -u origin "$branch"
        fi
    fi

    echo -e "${GREEN}✓ Session marked complete${NC}"
    echo ""
    echo "To clean up this worktree, return to main repo and run:"
    echo -e "${BLUE}parallel-claude.sh cleanup${NC}"
}

# Cleanup completed worktrees
cleanup_sessions() {
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║  CLEANUP PARALLEL SESSIONS                                  ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    if [[ ! -d "$WORKTREE_DIR" ]]; then
        echo -e "${GREEN}No worktrees to clean up.${NC}"
        return
    fi

    local count=0
    local to_remove=()

    for worktree_path in "$WORKTREE_DIR"/*; do
        if [[ -d "$worktree_path" ]]; then
            local name=$(basename "$worktree_path")
            local branch=$(git -C "$worktree_path" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")

            # Check for uncommitted changes
            local status=""
            if [[ -n $(git -C "$worktree_path" status --porcelain 2>/dev/null) ]]; then
                status="${YELLOW}(uncommitted changes)${NC}"
            else
                status="${GREEN}(clean)${NC}"
            fi

            echo -e "  ${BLUE}$name${NC} $status"
            echo -e "    Branch: $branch"

            count=$((count + 1))
            to_remove+=("$worktree_path")
        fi
    done

    if [[ $count -eq 0 ]]; then
        echo -e "${GREEN}No worktrees to clean up.${NC}"
        return
    fi

    echo ""
    echo -e "Remove $count worktree(s)? ${YELLOW}(y/n)${NC}"
    read -r response

    if [[ "$response" != "y" ]]; then
        echo -e "${YELLOW}Cleanup cancelled.${NC}"
        return
    fi

    for worktree_path in "${to_remove[@]}"; do
        local name=$(basename "$worktree_path")
        git worktree remove "$worktree_path" --force 2>/dev/null || rm -rf "$worktree_path"
        echo -e "${GREEN}✓ Removed: $name${NC}"
    done

    # Prune worktree references
    git worktree prune

    echo ""
    echo -e "${GREEN}✓ Cleanup complete!${NC}"
}

# Show help
show_help() {
    cat << EOF
${CYAN}Parallel Claude Sessions${NC}
Spawn multiple Claude Code instances on separate git worktrees.

${BLUE}Usage:${NC}
  parallel-claude.sh spawn <description> [work-item-id]
  parallel-claude.sh list
  parallel-claude.sh complete
  parallel-claude.sh cleanup
  parallel-claude.sh help

${BLUE}Commands:${NC}
  spawn <desc> [id]   Create worktree and spawn Claude in new terminal
  list                Show all active parallel sessions
  complete            Mark current session as done (run from worktree)
  cleanup             Remove completed worktrees
  help                Show this help

${BLUE}Examples:${NC}
  parallel-claude.sh spawn "implement dark mode" 1234567
  parallel-claude.sh spawn "fix login bug"
  parallel-claude.sh list
  parallel-claude.sh cleanup

${BLUE}Workflow:${NC}
  1. Spawn sessions for different tasks (each gets own terminal)
  2. Work in parallel across multiple features
  3. Each session has isolated git state (no conflicts)
  4. Cleanup when PRs are merged

EOF
}

# Main
case "${1:-help}" in
    spawn)
        spawn_session "$2" "$3"
        ;;
    list|ls)
        list_sessions
        ;;
    complete|done)
        complete_session
        ;;
    cleanup|clean)
        cleanup_sessions
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        show_help
        exit 1
        ;;
esac
