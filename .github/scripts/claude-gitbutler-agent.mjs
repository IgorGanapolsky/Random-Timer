#!/usr/bin/env node

import { promises as fs } from 'fs';
import { join } from 'path';
import TOML from '@iarna/toml';
import YAML from 'yaml';

class ClaudeGitButlerAgent {
  constructor() {
    this.config = null;
    this.gitbutlerConfig = null;
    this.worktrees = new Map();
  }

  async initialize() {
    // Load configuration
    const configPath = join('.github', 'claude-gitbutler.yml');
    const configContent = await fs.readFile(configPath, 'utf8');
    this.config = YAML.parse(configContent);

    // Load GitButler state
    const gitbutlerPath = join('.git', 'gitbutler', 'virtual_branches.toml');
    const gitbutlerContent = await fs.readFile(gitbutlerPath, 'utf8');
    this.gitbutlerConfig = TOML.parse(gitbutlerContent);

    // Initialize worktrees
    await this.initializeWorktrees();
  }

  async initializeWorktrees() {
    const worktreePath = join('.git', 'worktrees');
    for (const path of this.config.worktrees.base_paths) {
      const worktreeConfig = {
        path,
        active: false,
        virtualBranches: new Set(),
        lastCommit: null
      };
      
      try {
        const headRef = await fs.readFile(join(worktreePath, path, 'HEAD'), 'utf8');
        worktreeConfig.active = true;
        worktreeConfig.lastCommit = headRef.trim();
      } catch (e) {
        // Worktree not initialized
      }
      
      this.worktrees.set(path, worktreeConfig);
    }
  }

  async createVirtualBranch(type, name, description) {
    const template = this.config.branch_templates[type];
    if (!template) {
      throw new Error(`Unknown branch type: ${type}`);
    }

    const branchName = `${template.prefix}${name}`;
    
    // Create virtual branch config
    const virtualBranch = {
      name: branchName,
      description,
      claudePrompt: template.claude_prompt,
      created: new Date().toISOString()
    };

    // Update GitButler config
    await this.updateGitButlerConfig(virtualBranch);

    // Create worktree if needed
    await this.createWorktreeForBranch(virtualBranch);

    return virtualBranch;
  }

  async updateGitButlerConfig(virtualBranch) {
    const branchId = crypto.randomUUID();
    
    this.gitbutlerConfig.branches[branchId] = {
      id: branchId,
      name: virtualBranch.name,
      notes: virtualBranch.description,
      created_timestamp_ms: Date.now().toString(),
      updated_timestamp_ms: Date.now().toString(),
      order: Object.keys(this.gitbutlerConfig.branches).length,
      allow_rebasing: true,
      in_workspace: true,
      post_commits: this.config.gitbutler.virtual_branch_config.auto_commit
    };

    // Save updated config
    const configPath = join('.git', 'gitbutler', 'virtual_branches.toml');
    await fs.writeFile(configPath, TOML.stringify(this.gitbutlerConfig));
  }

  async createWorktreeForBranch(virtualBranch) {
    // Find available worktree
    let worktreePath = null;
    for (const [path, config] of this.worktrees.entries()) {
      if (!config.active) {
        worktreePath = path;
        break;
      }
    }

    if (!worktreePath) {
      throw new Error('No available worktrees');
    }

    // Initialize worktree
    const fullPath = join('.git', 'worktrees', worktreePath);
    await fs.mkdir(fullPath, { recursive: true });

    // Update worktree state
    const worktree = this.worktrees.get(worktreePath);
    worktree.active = true;
    worktree.virtualBranches.add(virtualBranch.name);

    return worktreePath;
  }

  async handlePullRequest(pr) {
    // Find associated virtual branch
    const virtualBranch = this.findVirtualBranchForPR(pr);
    if (!virtualBranch) {
      return;
    }

    // Update branch status
    if (pr.draft) {
      await this.updateBranchStatus(virtualBranch, 'in_progress');
    } else if (pr.state === 'closed') {
      if (pr.merged) {
        await this.updateBranchStatus(virtualBranch, 'merged');
      } else {
        await this.updateBranchStatus(virtualBranch, 'closed');
      }
    } else {
      await this.updateBranchStatus(virtualBranch, 'review');
    }

    // Cleanup if needed
    if (pr.state === 'closed' && this.config.worktrees.auto_cleanup) {
      await this.cleanupBranch(virtualBranch);
    }
  }

  findVirtualBranchForPR(pr) {
    for (const branch of Object.values(this.gitbutlerConfig.branches)) {
      if (branch.name === pr.head.ref) {
        return branch;
      }
    }
    return null;
  }

  async updateBranchStatus(branch, status) {
    branch.status = status;
    branch.updated_timestamp_ms = Date.now().toString();

    // Save updated config
    const configPath = join('.git', 'gitbutler', 'virtual_branches.toml');
    await fs.writeFile(configPath, TOML.stringify(this.gitbutlerConfig));
  }

  async cleanupBranch(branch) {
    // Find associated worktree
    for (const [path, config] of this.worktrees.entries()) {
      if (config.virtualBranches.has(branch.name)) {
        // Clean up worktree
        const worktreePath = join('.git', 'worktrees', path);
        await fs.rm(worktreePath, { recursive: true, force: true });

        // Update state
        config.active = false;
        config.virtualBranches.delete(branch.name);
        break;
      }
    }

    // Remove from GitButler config
    delete this.gitbutlerConfig.branches[branch.id];
    
    // Save updated config
    const configPath = join('.git', 'gitbutler', 'virtual_branches.toml');
    await fs.writeFile(configPath, TOML.stringify(this.gitbutlerConfig));
  }
}

// Create and export agent instance
const agent = new ClaudeGitButlerAgent();

// Initialize and handle command
if (process.argv[2] === 'handle-pr') {
  const pr = JSON.parse(process.argv[3]);
  agent.initialize()
    .then(() => agent.handlePullRequest(pr))
    .catch(err => {
      console.error('Error handling PR:', err);
      process.exit(1);
    });
}