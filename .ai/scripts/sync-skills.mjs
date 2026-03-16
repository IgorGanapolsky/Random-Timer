#!/usr/bin/env node

// Convenience wrapper: delegates to `npx @siliconoid/agentkit sync`
// For projects using AgentKit CLI, this script is optional.
// You can also run: npx @siliconoid/agentkit sync

import { execSync } from 'child_process'

try {
  execSync('npx @siliconoid/agentkit sync', { stdio: 'inherit' })
} catch {
  console.error('agentkit sync 执行失败，请确认是否已安装。')
  console.error('运行：npm install -g @siliconoid/agentkit')
  process.exit(1)
}
