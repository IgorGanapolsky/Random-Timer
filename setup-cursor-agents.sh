#!/bin/bash

echo "🚀 Setting up Cursor configurations for SuperPassword..."

# Main repository cursor config
mkdir -p .cursor
cat > .cursor/config.json << 'CONFIG'
{
  "version": "2025.3",
  "project": "SuperPassword",
  "architecture": "React Native + Expo + AI Backend",
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

You are specialized in implementing new features for SuperPassword.

## Current Task: AI Intelligence Features
- Implement Eko AI backend integration
- Add vault security audit endpoint
- Create phishing detection service
- Build password rotation planner

## Architecture Context
- Eko Framework 3.0.2 for agentic workflows
- Claude 3.5 Sonnet for AI analysis
- Node.js + Fastify backend
- Firebase for auth and data storage

## Branch: feature/ai-intelligence
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
- AES-256 encryption implementation
- Biometric authentication
- Zero-knowledge architecture
- Secure key management

## Branch: security/encryption
PROMPT

# Testing Agent Setup
echo "Setting up Testing Agent..."
mkdir -p ../worktrees/testing-agent/.cursor
cat > ../worktrees/testing-agent/.cursor/agent.md << 'PROMPT'
# Testing & QA Agent

You are specialized in writing comprehensive tests.

## Coverage Goals
- Unit tests: 90%+ coverage
- Integration tests for AI features
- E2E tests with Detox
- Security vulnerability tests

## Branch: test/coverage
PROMPT

echo "✅ Cursor configurations created successfully!"
echo ""
echo "=== Worktree Status ==="
git worktree list
