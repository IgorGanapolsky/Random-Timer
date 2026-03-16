<!-- tech-stack: universal -->

# Git Workflow

## Branches

### Main Branch

The primary branch is **`main`** (or `master`).

### Branch Naming

| Type     | Pattern                  | Example                 |
| -------- | ------------------------ | ----------------------- |
| Feature  | `feat/<description>`     | `feat/add-video-export` |
| Bug fix  | `fix/<description>`      | `fix/audio-sync-issue`  |
| Chore    | `chore/<description>`    | `chore/upgrade-deps`    |
| Refactor | `refactor/<description>` | `refactor/auth-module`  |
| Docs     | `docs/<description>`     | `docs/api-reference`    |
| Version  | `feat/<version>-<scope>` | `feat/v2.0-search-frontend` |

## Commit Messages

### Format

```
<type>: <description>
```

### Types

| Type       | Usage                                                   |
| ---------- | ------------------------------------------------------- |
| `feat`     | New feature or capability                               |
| `fix`      | Bug fix                                                 |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `style`    | Formatting, no code change                              |
| `docs`     | Documentation only                                      |
| `chore`    | Build process, dependencies, tooling                    |
| `perf`     | Performance improvement                                 |
| `test`     | Adding or updating tests                                |
| `build`    | Build system or external dependencies                   |
| `ci`       | CI/CD pipeline changes                                  |
| `ai`       | AI skills, commands, or rules changes                   |

### Guidelines

- Keep the first line under **72 characters**
- Use imperative mood: "add feature" not "added feature"
- No period at the end of the subject line
- **Before pushing**: Ensure linting and build pass
- **Commit message** 使用中文
## Commit 流程（AI 必须遵守）

每次执行 commit 时，按以下顺序操作：

1. **写 devlog** — 根据本次变更内容，追加一条记录到 `.ai/changelog/YYYY-MM.md`（格式见 `.ai/skills/devlog/skill.md`）
2. **Stage devlog** — 将 changelog 文件加入暂存区（`git add .ai/changelog/YYYY-MM.md`）
3. **Commit** — 将代码变更和 devlog 一起提交

这样每次 push 时，变更日志自动包含在内，无需额外操作。

### 例外情况

以下场景可以跳过 devlog：
- 纯文档/注释修改（`docs` 类型 commit）
- AI 规则文件自身的变更（`.ai/` 目录下的 commit）
- 用户明确要求跳过

### 历史检索约定

- AI 新建会话时，优先读 `.ai/CONTEXT.md` 获取项目当前状态
- 需要变更细节时，按月读取 `.ai/changelog/YYYY-MM.md`
- 需要决策背景时，读 `.ai/decisions/README.md` 索引后按需加载具体 ADR
