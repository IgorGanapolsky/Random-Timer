# /spec — 产物版本管理器

通过子命令或自然语言管理 PRD、设计规格的完整生命周期。**人只管说话，AI 管文件。**

---

## 子命令速查表

| 子命令 | 说明 | 示例 |
|--------|------|------|
| `new prd <名称>` | 创建新 PRD 到 `_planning/` | `/spec new prd 用户认证` |
| `new design <名称>` | 创建新设计包到 `_planning/` | `/spec new design 登录页` |
| `promote <id>` | 将产物从 `_planning/` 提升到 `_active/` | `/spec promote prd-001` |
| `archive <id>` | 将产物从 `_active/` 归档到 `_archive/` | `/spec archive prd-001` |
| `snapshot <版本号>` | 对当前 `_active/` 创建版本快照 | `/spec snapshot v1.0` |
| `restore <版本号>` | 从快照恢复到 `_active/` | `/spec restore v1.0` |
| `diff <v1> <v2>` | 对比两个版本快照 | `/spec diff v1.0 v1.1` |
| `switch <版本> [角色]` | 创建版本分支并更新上下文锚定 | `/spec switch v2.0 frontend` |
| `status` | 显示当前上下文和产物状态 | `/spec status` |
| `link <from> <to>` | 建立产物间双向关联 | `/spec link prd-001 epic-001` |
| `trace` | 生成追踪矩阵 + 孤儿检测 | `/spec trace` |

---

## 自动上下文锚定协议

每次执行 `/spec` 时，先执行上下文锚定：

1. **读取分支名** — 执行 `git branch --show-current`
2. **解析上下文** — 从 `feat/<version>-<scope>[-role]` 中提取：
   - `version`: 版本号（如 v2.0）
   - `scope`: 功能范围（如 search）
   - `role`: 角色（如 frontend/backend，可选）
3. **匹配产物** — 在 `.specs/prd/_active/` 和 `.specs/designs/_active/` 中查找关联产物
4. **读取 CONTEXT.md** — 检查 `.ai/CONTEXT.md` 的 Version Anchor 段落
5. **回复首行** — 附加上下文摘要：`📌 v2.0 · search · frontend`

如果不在版本分支上，跳过锚定，正常执行。

---

## 初始化检查

首次使用时，检查 `.specs/` 下的目录结构是否完整。如果缺少以下任一目录，自动创建：

```
.specs/prd/_planning/
.specs/prd/_active/
.specs/prd/_versions/
.specs/prd/_archive/
.specs/designs/_planning/
.specs/designs/_active/
.specs/designs/_versions/
.specs/designs/_archive/
.specs/_versions/
```

---

## 子命令详细步骤

### `new prd <名称>`

1. 读取 `.specs/prd/_template.md`
2. 扫描 `.specs/prd/` 下所有子目录，找到最大 prd-NNN 编号，+1 得到新编号
3. 用新编号和名称填充模板：
   - `id`: `prd-<新编号>`
   - `title`: 用户提供的名称
   - `created` / `updated`: 今天日期
4. 写入 `.specs/prd/_planning/prd-<NNN>-<slug>.md`
5. 输出确认：创建了什么、在哪里、下一步建议

### `new design <名称>`

1. 读取 `.specs/designs/_template/design-spec.md`
2. 扫描 `.specs/designs/` 找到最大 design-NNN 编号，+1
3. 创建目录 `.specs/designs/_planning/design-<NNN>-<slug>/`
4. 在目录中创建 `design-spec.md`，填充模板
5. 输出确认

### `promote <id>`

1. 根据 id 前缀判断类型（prd- / design-）
2. 在对应的 `_planning/` 中查找文件/目录
3. 移动到 `_active/`
4. 更新 frontmatter：`status: active`，`updated: 今天`
5. 输出确认

### `archive <id>`

1. 在 `_active/` 中查找
2. 移动到 `_archive/`，文件名加日期前缀：`YYYY-MM-DD_原名`
3. 更新 frontmatter：`status: archived`，`updated: 今天`
4. 输出确认

### `snapshot <版本号>`

1. 创建目录 `.specs/_versions/<版本号>/`
2. 复制 `.specs/prd/_active/` 所有内容到 `.specs/_versions/<版本号>/prd/`
3. 复制 `.specs/designs/_active/` 所有内容到 `.specs/_versions/<版本号>/designs/`
4. 复制 `.specs/epics/` 所有内容到 `.specs/_versions/<版本号>/epics/`
5. 复制 `.specs/stories/` 所有内容到 `.specs/_versions/<版本号>/stories/`
6. 生成 `.specs/_versions/<版本号>/snapshot.yaml`：

```yaml
version: "<版本号>"
created: "YYYY-MM-DD HH:mm"
branch: "<当前分支>"
contents:
  prd: [文件列表]
  designs: [目录列表]
  epics: [文件列表]
  stories: [文件列表]
```

7. 输出确认及快照内容摘要

### `restore <版本号>`

1. 确认用户意图（⚠️ 此操作会覆盖当前 `_active/` 内容）
2. 从 `.specs/_versions/<版本号>/prd/` 恢复到 `.specs/prd/_active/`
3. 从 `.specs/_versions/<版本号>/designs/` 恢复到 `.specs/designs/_active/`
4. 更新所有恢复文件的 frontmatter `updated` 字段
5. 输出确认

### `diff <v1> <v2>`

1. 读取 `.specs/_versions/<v1>/snapshot.yaml` 和 `.specs/_versions/<v2>/snapshot.yaml`
2. 对比两个版本中的文件列表差异（新增/删除/修改）
3. 对同名文件进行内容 diff
4. 输出差异报告表格

### `switch <版本> [角色]`

1. 创建分支 `feat/<版本>-<scope>[-role]`（scope 从当前上下文或用户输入推断）
2. 更新 `.ai/CONTEXT.md` 的 Version Anchor 段落：

```markdown
## Version Anchor
- **Version**: <版本>
- **Role**: <角色或 —>
- **Branch**: <分支名>
- **Active PRDs**: <列出 _active/ 中的 PRD>
- **Active Designs**: <列出 _active/ 中的设计>
```

3. 输出确认

### `status`

输出当前状态概览：

```
📌 上下文锚定: v2.0 · search · frontend (或 "无版本上下文")

## PRD
| ID | 标题 | 状态 | 版本 |
|----|------|------|------|

## 设计
| ID | 标题 | 状态 | 关联 PRD |
|----|------|------|----------|

## 版本快照
| 版本 | 创建日期 | 分支 | 产物数 |
|------|----------|------|--------|
```

### `link <from> <to>`

1. 解析两个 ID 的类型
2. 读取双方文件的 frontmatter
3. 在 `from` 的 frontmatter 中添加 `to` 到对应的 linked-* 字段
4. 在 `to` 的 frontmatter 中添加 `from` 到对应的 linked-* 字段
5. 输出确认双向链接

### `trace`

1. 扫描所有 `.specs/` 下的文件（prd, designs, epics, stories）
2. 提取每个文件的 frontmatter 中的 linked-* 字段
3. 生成追踪矩阵：

```
PRD → Epic → Story → Design 追踪矩阵

| PRD | Epics | Stories | Designs | 覆盖率 |
|-----|-------|---------|---------|--------|
```

4. 检测孤儿产物（没有任何链接的产物）
5. 输出矩阵 + 孤儿警告

---

## 自然语言识别

当用户未使用明确子命令时，根据意图匹配：

| 用户表达 | 映射子命令 |
|----------|-----------|
| "我要规划搜索功能" / "新建一个 PRD" | `new prd` |
| "开始设计登录页" / "做个设计方案" | `new design` |
| "这个 PRD 定了" / "可以开始做了" | `promote` |
| "这个功能做完了" / "归档" | `archive` |
| "打个快照" / "存一下当前版本" | `snapshot` |
| "回到 v1.0" / "恢复之前的版本" | `restore` |
| "对比一下" / "看看改了什么" | `diff` |
| "切到 v2.0" / "开始新版本" | `switch` |
| "现在什么状态" / "看看进度" | `status` |
| "关联一下" / "这个 PRD 对应那个 epic" | `link` |
| "追踪矩阵" / "检查覆盖率" | `trace` |

如果意图不明确，询问用户想要执行什么操作。

---

## ID 与命名约定

- **ID 格式**: `<type>-<NNN>`，三位数字，零填充（如 `prd-001`）
- **文件名 slug**: 取名称的拼音或英文小写，连字符分隔
- **目录型产物**（设计包）: 使用目录名作为 ID 载体，内含 `design-spec.md`
- **编号规则**: 全局递增，不回收已使用的编号

---

## 端到端场景指引

### 场景一：用户说"我想做一个搜索功能"

```
1. 识别意图 → new prd
2. /spec new prd 搜索功能
3. 引导用户填写 PRD（背景、场景、功能需求、成功指标）
4. 如果涉及 UI → /spec new design 搜索页
5. /spec link prd-001 design-001
6. 用户确认后 → /spec promote prd-001
7. 拆 Epic/Story → 正常开发流程
```

### 场景二：用户说"v2.0 要重做前端"

```
1. /spec snapshot v1.0          → 先保存当前状态
2. /spec switch v2.0 frontend   → 创建版本分支 + 锚定
3. /spec new prd 前端重构       → 在新版本下规划
4. 开发过程中分支名自动锚定上下文
5. 完成后 → /spec snapshot v2.0
```

### 场景三：用户说"看看现在什么情况"

```
1. /spec status → 输出完整状态表
2. 如果发现孤儿产物 → 建议 /spec link 或 /spec archive
3. 如果有 _planning/ 中停留过久的产物 → 提醒用户决定是否 promote 或废弃
```

### 场景四：用户说"这个功能做完了"

```
1. /spec archive prd-001
2. /spec archive design-001（如果有关联设计）
3. 建议执行 /wrap-up 归档 Story/Task 并刷新 CONTEXT.md
4. 建议 /spec snapshot 保存里程碑
```

---

## AI 行为准则

1. **主动建议，不强制执行** — 当识别到适合使用 `/spec` 的场景时，向用户建议而非直接操作
2. **操作前确认** — `promote`、`archive`、`restore` 等状态变更操作前，简要说明将要做什么并确认
3. **保持关联完整** — 创建新产物后，主动检查是否需要 `link` 到已有产物
4. **上下文感知** — 在版本分支上时，所有操作自动关联当前版本上下文
5. **收尾提醒** — 功能完成时，主动提醒归档和快照
