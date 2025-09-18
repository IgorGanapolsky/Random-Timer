# GitButler + Claude Agents Workflow Guide

This guide explains how to use GitButler with Claude Code agents for the SuperPassword project's multi-agent development workflow.

## 🏗️ Architecture Overview

Our setup combines:
- **GitButler Virtual Branches**: Isolated development streams
- **Physical Worktrees**: Dedicated workspaces per agent  
- **Claude AI Agents**: Specialized development roles
- **MCP Integration**: Real-time communication between Claude and GitButler

## 🚀 Quick Start

### 1. Install GitButler CLI

```bash
brew install gitbutler-cli
```

### 2. Run Setup Script

```bash
./setup-cursor-agents.sh
```

### 3. Enable Experimental Features

In GitButler UI:
1. Go to **Settings > Experimental**
2. Enable **GitButler Actions**
3. Enable **MCP Integration**

### 4. Restart Claude Code/Cursor

Restart your IDE to load the MCP servers.

## 🤖 Agent Workflow

### Security Agent Example

1. **Switch to Security Worktree**
   ```bash
   cd worktrees/security
   ```

2. **Create Virtual Branch**
   ```bash
   gitbutler branch create security/biometric-auth
   ```

3. **Start Claude Code**
   - Claude automatically connects to GitButler MCP server
   - Real-time branch context and project state available
   - AI-powered commit messages and conflict resolution

4. **Develop with AI Assistance**
   - Claude sees current branch state via MCP
   - Automatic commit management
   - Smart merge conflict resolution
   - Context-aware code suggestions

5. **Auto-PR Creation**
   ```bash
   gitbutler pr create --auto
   ```

## 🔧 GitButler Commands

### Branch Management
```bash
# Create new virtual branch
gitbutler branch create feat/new-feature

# List branches by agent
gitbutler branch list --agent security

# Switch branch context
gitbutler branch switch security/encryption

# Merge virtual branch
gitbutler branch merge feat/ai-recommendations
```

### Agent Operations
```bash
# Assign issue to agent
gitbutler agent assign security feat/biometric-auth

# Check agent status
gitbutler agent status --all

# Sync agent worktree
gitbutler agent sync security
```

### Automation
```bash
# Enable auto-PR creation
gitbutler hooks enable auto-pr

# Enable conflict resolution
gitbutler hooks enable conflict-resolution

# Run security audit workflow
gitbutler workflow run security-audit
```

## 📋 MCP Server Features

### Real-time Context
- Current branch state
- Uncommitted changes
- Merge conflicts
- Project structure

### AI-Powered Features
- **Smart Commits**: AI-generated commit messages
- **Conflict Resolution**: Automated merge conflict handling
- **Code Review**: AI analysis of changes
- **Branch Suggestions**: Optimal branching strategies

### Agent Coordination
- **Cross-agent Communication**: Agents can see each other's work
- **Dependency Tracking**: Automatic detection of inter-agent dependencies
- **Merge Orchestration**: Intelligent merge order optimization

## 🔄 Development Workflow

### 1. Issue Assignment
```bash
# GitHub issue automatically labeled by agent type
gitbutler issue assign 154 security
```

### 2. Branch Creation
```bash
# Agent creates virtual branch
cd worktrees/security
gitbutler branch create security/ai-recommendations
```

### 3. AI Development
- Claude Code connects via MCP
- Real-time GitButler integration
- Context-aware development
- Automatic commit management

### 4. Continuous Integration
```bash
# Auto-commit with AI messages
gitbutler commit --auto

# Push to virtual branch
gitbutler push

# Create PR automatically
gitbutler pr create --template security
```

### 5. Review & Merge
- Automated PR creation
- Agent-specific review templates
- CI/CD integration
- Squash merge to main

## 🛠️ Configuration Files

### Main Project MCP Config
```json
// .cursor/mcp.json
{
  "mcpServers": {
    "gitbutler": {
      "command": "gitbutler",
      "args": ["mcp", "server"],
      "env": {
        "GITBUTLER_PROJECT_PATH": "."
      }
    }
  }
}
```

### Agent-Specific MCP Config
```json
// worktrees/security/.cursor/mcp.json
{
  "mcpServers": {
    "gitbutler": {
      "command": "gitbutler",
      "args": ["mcp", "server"],
      "env": {
        "GITBUTLER_PROJECT_PATH": "../../",
        "GITBUTLER_AGENT": "security-agent"
      }
    }
  }
}
```

### GitButler Config
```toml
# .gitbutler/config.toml
[experimental]
gitbutler_actions = true
mcp_integration = true
auto_commit = true
virtual_branches = true

[ai]
provider = "claude"
model = "claude-3-5-sonnet"
auto_commit_messages = true
conflict_resolution = true
```

## 🔍 Troubleshooting

### MCP Server Not Starting
```bash
# Check GitButler CLI installation
which gitbutler

# Restart MCP server
gitbutler mcp restart

# Check server logs
gitbutler mcp logs
```

### Agent Context Issues
```bash
# Refresh agent context
gitbutler agent refresh security

# Sync worktree state
gitbutler sync --force

# Reset agent configuration
gitbutler agent reset security
```

### Virtual Branch Conflicts
```bash
# List conflicted branches
gitbutler branch list --conflicts

# Resolve with AI assistance
gitbutler resolve --ai

# Manual conflict resolution
gitbutler resolve --manual
```

## 📊 Benefits

### For Development
- **Parallel Development**: Multiple agents work simultaneously
- **Context Awareness**: AI sees full project state
- **Automated Workflows**: Reduced manual git operations
- **Smart Conflict Resolution**: AI-powered merge strategies

### For Project Management
- **Clear Separation**: Each agent has dedicated workspace
- **Automated PRs**: Consistent review process
- **Linear History**: Clean git history with squash merges
- **Audit Trail**: Complete development history

### For Code Quality
- **Specialized Reviews**: Agent-specific expertise
- **Consistent Standards**: Automated formatting and linting
- **Security Focus**: Dedicated security agent oversight
- **Test Coverage**: Dedicated testing agent ensures quality

## 🚀 Advanced Features

### Custom Workflows
```bash
# Create custom workflow
gitbutler workflow create security-audit \
  --trigger "security/*" \
  --actions "test,scan,review"

# Run workflow
gitbutler workflow run security-audit
```

### Agent Coordination
```bash
# Cross-agent dependencies
gitbutler dependency add security/auth testing/auth-tests

# Coordinated merges
gitbutler merge --coordinate security testing
```

### Integration Hooks
```bash
# Custom commit hooks
gitbutler hook add pre-commit ./scripts/security-check.sh

# PR automation
gitbutler hook add post-pr ./scripts/notify-team.sh
```

## 📚 Resources

- [GitButler Documentation](https://docs.gitbutler.com/)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [Claude Code Integration](https://docs.anthropic.com/claude/docs)
- [Project Branch Strategy](./BRANCH_STRATEGY.md)

---

**Next Steps**: Run `./setup-cursor-agents.sh` to get started with GitButler + Claude integration!