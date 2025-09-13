#!/bin/bash

# Branch Management Script for Solo Development
# Maintains a simple branch structure:
# - main (production)
# - develop (development)
# - feature/* (temporary)
# - fix/* (temporary)
# - chore/* (temporary)

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

function create_branch() {
    local type=$1
    local name=$2
    
    # Validate branch type
    case $type in
        feature|fix|chore)
            ;;
        *)
            echo -e "${RED}Invalid branch type. Use: feature, fix, or chore${NC}"
            exit 1
            ;;
    esac
    
    # Create branch from develop
    git checkout develop
    git pull origin develop
    git checkout -b "$type/$name"
    
    echo -e "${GREEN}Created branch $type/$name from develop${NC}"
    echo "Push to origin with: git push -u origin $type/$name"
}

function delete_branch() {
    local branch=$1
    
    # Don't delete main or develop
    if [[ "$branch" == "main" ]] || [[ "$branch" == "develop" ]]; then
        echo -e "${RED}Cannot delete main or develop branches${NC}"
        exit 1
    fi
    
    # Check if branch exists
    if ! git show-ref --verify --quiet "refs/heads/$branch"; then
        echo -e "${RED}Branch $branch doesn't exist${NC}"
        exit 1
    fi
    
    # Delete local and remote
    git branch -D "$branch"
    git push origin --delete "$branch" 2>/dev/null || true
    
    echo -e "${GREEN}Deleted branch $branch${NC}"
}

function list_branches() {
    echo -e "${BLUE}Active Branches:${NC}"
    echo "----------------"
    git branch --sort=-committerdate | sed 's/^/  /'
    
    echo -e "\n${BLUE}Recent Commits:${NC}"
    echo "----------------"
    git log --oneline --graph --decorate -n 5
}

function cleanup_branches() {
    echo -e "${YELLOW}Cleaning up branches...${NC}"
    
    # Switch to develop
    git checkout develop
    
    # Delete merged branches
    echo -e "\n${BLUE}Deleting merged branches:${NC}"
    git branch --merged develop | grep -v "develop\|main" | xargs git branch -D 2>/dev/null || true
    
    # Prune remote branches
    echo -e "\n${BLUE}Pruning remote branches:${NC}"
    git remote prune origin
    
    # Show remaining branches
    echo -e "\n${GREEN}Remaining branches:${NC}"
    git branch --all | sed 's/^/  /'
}

# Show usage if no arguments
if [ $# -eq 0 ]; then
    echo "Usage:"
    echo "  $0 create <type> <name>    Create new branch (type: feature, fix, chore)"
    echo "  $0 delete <branch>         Delete branch locally and remotely"
    echo "  $0 list                    List all branches"
    echo "  $0 cleanup                 Clean up merged and stale branches"
    exit 0
fi

# Parse arguments
case $1 in
    create)
        if [ $# -ne 3 ]; then
            echo -e "${RED}Usage: $0 create <type> <name>${NC}"
            exit 1
        fi
        create_branch "$2" "$3"
        ;;
    delete)
        if [ $# -ne 2 ]; then
            echo -e "${RED}Usage: $0 delete <branch>${NC}"
            exit 1
        fi
        delete_branch "$2"
        ;;
    list)
        list_branches
        ;;
    cleanup)
        cleanup_branches
        ;;
    *)
        echo -e "${RED}Invalid command. Use: create, delete, list, or cleanup${NC}"
        exit 1
        ;;
esac
