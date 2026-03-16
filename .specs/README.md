# Project Specs

本目录管理项目产物的全生命周期：规划 → 执行 → 归档 → 版本快照。

## 目录结构

```
.specs/
├── prd/                    # 产品需求文档
│   ├── _planning/          # 规划中
│   ├── _active/            # 执行中
│   ├── _versions/          # 版本快照
│   ├── _archive/           # 已归档
│   └── _template.md        # PRD 模板
├── designs/                # 设计规格
│   ├── _planning/          # 规划中
│   ├── _active/            # 执行中
│   ├── _versions/          # 版本快照
│   ├── _archive/           # 已归档
│   └── _template/          # 设计包模板
├── epics/                  # Epic 定义（大功能）
├── stories/                # 用户故事（进行中）
├── tasks/
│   └── draft/              # 草稿任务
├── completed/              # 已完成归档（按季度）
│   └── YYYY-QN/
├── _versions/              # 跨产物版本快照元数据
└── README.md
```

## 产物流向

```
_planning/  →  _active/  →  _archive/
                  ↓
              _versions/<ver>/   （快照）
```

## 生命周期

| 阶段 | 位置 | 说明 |
|------|------|------|
| Planning | `_planning/` | 规划中，可自由修改 |
| Active | `_active/` | 已确认执行，作为开发依据 |
| Archived | `_archive/` | 已完成或废弃，加日期前缀 |
| Versioned | `_versions/<ver>/` | 任意时点的快照副本 |

## 命名规范

| 类型 | 格式 | 示例 |
|------|------|------|
| PRD | `prd-NNN-描述.md` | `prd-001-user-auth.md` |
| 设计 | `design-NNN-描述/` | `design-001-login-page/` |
| Epic | `epic-NNN-description.md` | `epic-001-user-dashboard-v2.md` |
| Story | `story-NNN-description.md` | `story-001-add-export-button.md` |
| Task | `task-NNN-description.md` | `task-001-implement-export-api.md` |

## 归档约定

Story 或 Task 完成时：
1. 移动到 `completed/YYYY-QN/`
2. 文件名加日期前缀：`YYYY-MM-DD_原名.md`
3. 添加 `## Completion Notes` 章节

## 典型工作流

### 场景一：从零开始规划一个新功能

```
1. /spec new prd 用户认证        → 创建 PRD 到 prd/_planning/
2. （和 AI 对话完善 PRD 内容）
3. /spec new design 登录页       → 创建设计包到 designs/_planning/
4. /spec link prd-001 design-001 → 建立双向关联
5. /spec promote prd-001         → PRD 确认，移到 _active/
6. /spec promote design-001      → 设计确认，移到 _active/
7. （拆分 Epic / Story，开始开发）
8. /spec snapshot v1.0           → 里程碑快照
```

### 场景二：版本迭代

```
1. /spec snapshot v1.0           → 保存当前版本快照
2. /spec switch v2.0 frontend    → 创建版本分支，更新上下文锚定
3. /spec new prd 搜索增强        → 在新版本下规划
4. （开发完成后）
5. /spec snapshot v2.0           → 保存新版本快照
6. /spec diff v1.0 v2.0          → 查看版本间差异
```

### 场景三：查看和追踪

```
/spec status                     → 查看当前所有产物状态
/spec trace                      → 生成追踪矩阵，发现孤儿产物
```

### 场景四：功能完成，归档清理

```
1. /spec archive prd-001         → 归档已完成的 PRD
2. /spec archive design-001      → 归档关联设计
3. （Story/Task 由 /wrap-up 归档到 completed/）
```

## 管理原则

- **人只管说话，AI 管文件** — 通过 `/spec` 命令或自然语言对话管理产物，不要手动移动/重命名文件
- **先 Planning 再 Active** — 产物必须在 `_planning/` 中完善后再 promote 到 `_active/`
- **里程碑打快照** — 每个版本发布前用 `snapshot` 保存当前状态，方便回溯
- **双向链接** — 创建关联时用 `/spec link`，确保双方 frontmatter 同步更新
- **定期追踪** — 用 `/spec trace` 检查产物覆盖率，发现没有关联的孤儿产物
