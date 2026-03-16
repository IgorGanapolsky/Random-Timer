# AgentKit 用户手册

> 由 `agentkit init` 自动生成。运行 `agentkit update` 可更新本文件。
> **请勿手动编辑** — 每次 update 都会重新生成。

## 1. 当前项目配置

| 配置项 | 值 |
|--------|-----|
| 项目名称 | Random-Timer |
| 框架 | custom |
| 语言 | JavaScript |
| 包管理器 | npm |
| 构建工具 | — |
| 平台 | claude, codex |
| Brownfield 策略 | 吸收（Absorb） |
| 校准状态 | 待校准 — 建议运行 /agentkit-calibrate |

## 2. 目录结构速查

| 路径 | 用途 | 维护者 |
|------|------|--------|
| `.ai/rules/` | 规则文件（AI 编码指导） | AgentKit 生成 + 用户定制 |
| `.ai/skills/` | 可移植技能定义 | AgentKit 生成 + 用户自定义 |
| `.ai/decisions/` | 架构决策记录 (ADR) | 用户 |
| `.ai/changelog/` | 月度变更日志 | 用户 |
| `.ai/memory/` | 调试模式 / 已知问题 | 用户 |
| `.ai/scripts/` | 辅助脚本（如 sync-skills） | AgentKit |
| `.ai/design-system/` | 设计系统规范 | 用户 |
| `.ai/agentkit.json` | AgentKit 配置文件 | AgentKit |
| `.ai/CONTEXT.md` | 项目上下文快照（AI 入口） | wrap-up 自动刷新 |
| `.ai/QUICK-START.md` | 快速开始指南 | AgentKit |
| `.ai/USER-GUIDE.md` | 本手册 | AgentKit（自动生成） |
| `.specs/` | PRD、设计、Epic、Story — 通过 /spec 管理 | 用户 + /spec |

## 3. Brownfield 模式与规则校准

本项目在初始化时检测到已有 AI 配置文件，使用了 **absorb** 策略。

> 提取现有 AI 配置内容到 `.ai/rules/20-absorbed-rules.md`，重新生成平台文件

### 吸收的规则文件

原有配置内容已提取到 `.ai/rules/20-absorbed-rules.md`，请审查并整理：
- 有价值的规则内容可以合并到对应的规则文件中
- 审查完成后可删除 `20-absorbed-rules.md`
### 规则校准（/agentkit-calibrate）

`init` 生成的规则文件是模板默认值，可能与项目实际技术栈不完全匹配。建议运行 AI 辅助校准：

```
在 AI 编码助手中运行：/agentkit-calibrate
```

**校准流程：**

| 阶段 | 说明 |
|------|------|
| Discovery | 扫描项目依赖、目录结构、代码风格、Git 约定 |
| Audit | 逐条对比规则与项目实际状态，生成审计报告 |
| 用户确认 | 展示报告，等待确认修改项 |
| Calibrate | 按确认方案逐文件修正规则 |

**适用场景：**
- Brownfield 项目初始化后（模板规则需适配实际技术栈）
- 项目技术栈变更后（如从 CSS Modules 迁移到 Tailwind）
- AI 生成代码不符合项目风格时
- 定期维护，保持规则与代码一致

> 注意：校准只修改 AI 配置文件，**不会修改项目源码和依赖**。

## 4. 规则文件一览

| 文件名 | 标题 | 来源层 |
|--------|------|--------|
| 01-project-overview.md | Project Overview | base |
| 02-architecture.md | Architecture | base |
| 03-coding-conventions.md | Coding Conventions | base |
| 04-directory-structure.md | Directory Structure | base |
| 05-environment.md | Environment & Commands | base |
| 06-typescript.md | TypeScript | base |
| 07-react.md | React | base |
| 08-styling.md | Styling | base |
| 09-naming.md | Naming Conventions | base |
| 10-git-workflow.md | Git Workflow | base |
| 11-testing.md | Testing | base |
| 12-forbidden-patterns.md | Forbidden Patterns | base |
| 13-ai-agent.md | AI Agent Instructions | base |
| 14-performance.md | Performance | base |
| 15-accessibility.md | Accessibility (WCAG 2.1 AA) | base |
| 16-security.md | Frontend Security | base |
| 17-api-patterns.md | API Patterns | base |
| 18-specs-workflow.md | Specs 产物管理工作流 | base |
| 20-absorbed-rules.md | Absorbed Rules | 用户自定义 |

## 5. 规则分层系统

规则文件按 **5 层覆盖机制** 依次叠加，后面的层会覆盖前面的同名文件：

```
┌─────────────────────────────────────────────┐
│  Layer 5: 用户自定义（编号 20+）              │  ← 你的定制
├─────────────────────────────────────────────┤
│  Layer 4: CSS 框架覆盖（08-styling.md）       │  ← 未启用
├─────────────────────────────────────────────┤
│  Layer 3: UI 库覆盖（17-*, 18-*, 08-*）      │  ← 未启用
├─────────────────────────────────────────────┤
│  Layer 2: 框架覆盖（01-*, 02-*, 07-* 等）    │  ← 未启用
├─────────────────────────────────────────────┤
│  Layer 1: 基础规则（01 ~ 13）                 │  ← base（所有项目共享）
└─────────────────────────────────────────────┘
```

**当前项目实际使用的各层：**

| 层级 | 选择 | 说明 |
|------|------|------|
| Layer 1 — 基础 | base | 13 个通用规则文件 |
| Layer 2 — 框架 | — | 未使用框架覆盖 |
| Layer 3 — UI 库 | — | 未使用 UI 库覆盖 |
| Layer 4 — CSS | — | 未使用 CSS 框架覆盖 |
| Layer 5 — 用户 | 自定义 | 编号建议 20+，避免与模板文件冲突 |

## 6. 样式与 UI 设计模板系统

### 可选 UI 模板

| UI 模板 | 安装的规则文件 | 说明 |
|---------|---------------|------|
| `antd` | 08-styling, 17-antd, 18-pro-components | Ant Design 5 + SCSS Modules |
| `tailwind` | 08-styling, 17-shadcn, 18-dashboard-shadcn | Tailwind CSS 4 + shadcn/ui |
| `antd-tailwind` | 17-antd, 18-pro-components + Tailwind 08-styling | 混合模式 |
| `none` | （使用 base 08-styling） | 无 UI 库 |

### 可选 CSS 框架

| CSS 框架 | 覆盖文件 | 说明 |
|----------|---------|------|
| `tailwind` | 08-styling.md (Tailwind 版) | 适用于 custom 框架模式 |
| `scss` | 08-styling.md (SCSS 版) | 适用于 custom 框架模式 |
| `none` | — | 保持 base 默认样式规则 |

### design-system 目录

如需定制设计规范，在 `.ai/design-system/` 下创建：

| 文件 | 用途 |
|------|------|
| `tokens.json` | 设计令牌（颜色、间距、字体大小） |
| `brand.md` | 品牌指南（Logo 使用、语气语调） |
| `components.md` | 组件规范（交互模式、状态） |
| `pages.md` | 页面模板规范 |

> **更多 UI / 样式模板持续扩充中。** 欢迎提交 PR 贡献新模板。

## 7. 定制方法

### 7.1 编辑现有规则

- **查看差异**：`agentkit diff` 对比本地规则与模板的差异
- **更新模板**：`agentkit update` 补充新增的模板文件（不覆盖已有文件）
- **强制更新**：`agentkit update --force` 用最新模板覆盖所有文件

### 7.2 添加自定义规则

在 `.ai/rules/` 中创建新文件，**编号建议 20 起**（避免与模板文件冲突）：

```
.ai/rules/20-api-conventions.md
.ai/rules/21-database-patterns.md
```

格式要求：文件以 `# 标题` 开头，使用 Markdown。

### 7.3 创建自定义技能

```bash
npx @siliconoid/agentkit add-skill <skill-name>    # 创建技能骨架
npx @siliconoid/agentkit sync                       # 同步到各平台
```

技能文件位于 `.ai/skills/<name>/`，包含 `manifest.yaml` 和 `prompt.md`。

### 7.4 定制设计规范

编辑 `.ai/design-system/` 下的文件即可。AI 编码助手会在生成 UI 代码时参考这些规范。

## 8. 常用命令速查

| 命令 | 功能 |
|------|------|
| `npx @siliconoid/agentkit init` | 初始化项目（生成规则 + 配置） |
| `npx @siliconoid/agentkit init --smart` | 零交互全自动初始化（brownfield 自动吸收） |
| `npx @siliconoid/agentkit init --minimal` | 最小化初始化（brownfield 自动共存） |
| `npx @siliconoid/agentkit update` | 补充缺失的模板文件 |
| `npx @siliconoid/agentkit update --force` | 强制用最新模板覆盖 |
| `npx @siliconoid/agentkit list` | 查看当前配置 |
| `npx @siliconoid/agentkit list --rules` | 查看规则文件详情 |
| `npx @siliconoid/agentkit diff` | 对比本地规则与模板差异 |
| `npx @siliconoid/agentkit doctor` | 检查配置健康状态 |
| `npx @siliconoid/agentkit sync` | 同步技能到各平台 |
| `npx @siliconoid/agentkit add-skill <name>` | 创建新技能 |
| `npx @siliconoid/agentkit add-platform <id>` | 添加新平台支持 |
| `npx @siliconoid/agentkit add-pack <id>` | 安装技能包 |

### AI 辅助技能

| 技能命令 | 功能 | 使用场景 |
|----------|------|----------|
| `/agentkit-calibrate` | 扫描项目实际状态，校准规则文件 | 初始化后、技术栈变更后、规则与代码不匹配时 |

---
*由 AgentKit 自动生成*

