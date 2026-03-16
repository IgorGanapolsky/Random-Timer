<!-- tech-stack: universal -->

# Specs 产物管理工作流

## 目录结构

```
.specs/
├── prd/                    # 产品需求文档
│   ├── _planning/          # 规划中的 PRD
│   ├── _active/            # 执行中的 PRD
│   ├── _versions/          # PRD 版本快照
│   ├── _archive/           # 已归档的 PRD
│   └── _template.md        # PRD 模板
├── designs/                # 设计规格
│   ├── _planning/          # 规划中的设计
│   ├── _active/            # 执行中的设计
│   ├── _versions/          # 设计版本快照
│   ├── _archive/           # 已归档的设计
│   └── _template/          # 设计包模板
├── epics/                  # Epic 定义
├── stories/                # 用户故事
├── tasks/                  # 任务
│   └── draft/              # 草稿任务
├── completed/              # 已完成归档（按季度）
│   └── YYYY-QN/
├── _versions/              # 跨产物版本快照元数据
└── README.md
```

## 产物生命周期

所有产物（PRD、设计）遵循统一生命周期：

```
_planning/  →  _active/  →  _archive/
                  ↓
              _versions/<ver>/   （快照）
```

- **Planning**: 规划中，可自由修改
- **Active**: 已确认执行，作为开发依据
- **Archived**: 已完成或废弃，加日期前缀归档
- **Versioned**: 任意时点的快照副本，不可修改

## 自动上下文锚定

### 分支名解析规则

AI 在新会话开始时应检测当前分支名，并尝试从中提取上下文：

| 分支格式 | 含义 |
|----------|------|
| `feat/<version>-<scope>` | 版本 + 功能范围 |
| `feat/<version>-<scope>-<role>` | 版本 + 功能范围 + 角色（frontend/backend） |
| 其他 | 无版本上下文，按默认行为 |

示例：
- `feat/v2.0-search-frontend` → 版本 v2.0，范围 search，角色 frontend
- `feat/v1.5-auth` → 版本 v1.5，范围 auth，无角色限定

### 上下文对齐流程

1. 读取当前分支名
2. 解析版本/范围/角色信息
3. 读取 `.ai/CONTEXT.md` 的 Version Anchor 段落
4. 检查 `.specs/_versions/` 和 `.specs/prd/_active/` 中是否有匹配的版本产物
5. 在首次回复中附加上下文摘要：`📌 v2.0 · search · frontend`

## 命名约定

| 类型 | 格式 | 示例 |
|------|------|------|
| PRD | `prd-NNN-描述.md` | `prd-001-user-auth.md` |
| 设计 | `design-NNN-描述/` | `design-001-login-page/` |
| Epic | `epic-NNN-描述.md` | `epic-001-user-dashboard.md` |
| Story | `story-NNN-描述.md` | `story-001-add-export.md` |
| Task | `task-NNN-描述.md` | `task-001-implement-api.md` |

## 交叉引用

产物之间通过 frontmatter 维护双向链接：

- PRD → `linked-designs`, `linked-epics`
- Design → `linked-prd`, `linked-stories`
- Epic → `linked-prd`
- Story → `linked-epic`, `linked-designs`

**规则**：创建或更新链接时，必须同时更新双方的 frontmatter。

## 典型工作流

### 从想法到交付的完整流程

```
想法 → PRD(_planning/) → PRD(_active/) → 拆 Epic/Story → 开发 → 快照 → 归档
              ↓                ↓
        Design(_planning/) → Design(_active/)
```

**阶段说明：**

| 阶段 | 触发 | AI 操作 |
|------|------|---------|
| 规划 | 用户说"我想做XX功能" | `/spec new prd` 创建 PRD，引导用户完善 |
| 设计 | PRD 中涉及 UI/交互 | `/spec new design` 创建设计包，`/spec link` 关联 PRD |
| 确认 | 用户说"定了"/"可以开始" | `/spec promote` 移到 `_active/`，拆 Epic/Story |
| 开发 | Story 分配开发 | 正常开发流程，Story/Task 在 `stories/`、`tasks/` |
| 里程碑 | 版本发布或阶段完成 | `/spec snapshot` 保存快照 |
| 收尾 | 功能全部完成 | `/spec archive` 归档，`/wrap-up` 归档 Story/Task |

### AI 应主动介入的时机

- **用户讨论新功能需求时** — 建议创建 PRD：`"要不我先帮你建一个 PRD？"`
- **PRD 讨论趋于成熟时** — 建议 promote：`"PRD 内容差不多了，要 promote 到 active 吗？"`
- **开始开发前** — 建议检查状态：`"我先看下当前 /spec status"`
- **涉及 UI 变更时** — 建议创建设计规格并关联 PRD
- **功能完成时** — 建议归档并打快照
- **切换版本/分支时** — 建议使用 `/spec switch` 保持上下文同步

### 操作原则

1. **不手动移动文件** — 所有产物的创建、移动、归档都通过 `/spec` 执行，保持 frontmatter 和目录结构一致
2. **先 Planning 再 Active** — 产物必须在 `_planning/` 中完善后才能 promote
3. **双向链接** — 建立关联时必须同时更新双方的 frontmatter（使用 `/spec link`）
4. **里程碑打快照** — 每个版本发布、重大变更前用 `/spec snapshot` 保存当前状态
5. **定期追踪** — 使用 `/spec trace` 检查产物覆盖率和孤儿产物
