#!/bin/bash

echo "🚀 Setting up Cursor configurations for RandomTimer..."

# Main repository cursor config
mkdir -p .cursor
cat > .cursor/config.json << 'CONFIG'
{
  "version": "2025.3",
  "project": "RandomTimer",
  "architecture": "React Native CLI",
  "workflowType": "multi-agent-worktrees",
  "defaultModel": "claude-3.5-sonnet",
  "agents": {
    "feature": "../worktrees/feature-agent",
    "bugfix": "../worktrees/bugfix-agent", 
    "security": "../worktrees/security-agent",
    "testing": "../worktrees/testing-agent"
  }
}
CONFIG

# Feature Agent Setup
echo "Setting up Feature Agent..."
mkdir -p ../worktrees/feature-agent/.cursor
cat > ../worktrees/feature-agent/.cursor/agent.md << 'PROMPT'
# Feature Development Agent

You are specialized in implementing new features for RandomTimer.

## Current Task: Training Enhancements
- Add preset training ranges
- Add optional sound cues
- Add background notification triggers
- Add interval history summary

## Architecture Context
- React Native CLI
- TypeScript strict mode
- Minimal native dependencies

## Branch: feature/training-enhancements
PROMPT

# Bugfix Agent Setup
echo "Setting up Bugfix Agent..."
mkdir -p ../worktrees/bugfix-agent/.cursor
cat > ../worktrees/bugfix-agent/.cursor/agent.md << 'PROMPT'
# Bugfix & Performance Agent

You are specialized in fixing bugs and optimizing performance.

## Focus Areas
- Memory leaks in React Native
- Cross-platform compatibility issues
- Performance bottlenecks
- Security vulnerabilities

## Branch: bugfix/performance
PROMPT

# Security Agent Setup
echo "Setting up Security Agent..."
mkdir -p ../worktrees/security-agent/.cursor
cat > ../worktrees/security-agent/.cursor/agent.md << 'PROMPT'
# Security & Encryption Agent

You are specialized in implementing security features.

## Current Tasks
- Audit privacy and data minimization
- Validate background behavior permissions
- Confirm haptic usage compliance

## Branch: security/privacy
PROMPT

# Testing Agent Setup
echo "Setting up Testing Agent..."
mkdir -p ../worktrees/testing-agent/.cursor
cat > ../worktrees/testing-agent/.cursor/agent.md << 'PROMPT'
# Testing & QA Agent

You are specialized in writing comprehensive tests.

## Coverage Goals
- Unit tests: 80%+ coverage
- Integration tests for timer scheduling
- E2E tests with Detox
- Performance checks for long runs

## Branch: test/qa-coverage
PROMPT

echo "✅ Cursor configurations created successfully!"
echo ""
echo "=== Worktree Status ==="
git worktree list
