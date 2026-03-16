# Wrap-up Workflow — End-of-Task Memory Sync

One-stop command to update all project memory after completing a development task. Ensures nothing is lost between sessions.

## When to Use

- After finishing a feature or bug fix
- At the end of a development session
- After resolving a complex issue worth remembering
- Before switching to a different task/branch

## Workflow Steps

### Step 1: Analyze What Was Done

Review the current conversation to identify:
1. **Changes made**: Files modified, features added/fixed
2. **Decisions made**: Any architectural or technical decisions
3. **Issues encountered**: Bugs found, workarounds used, debugging insights
4. **Known issues**: Any remaining problems or TODOs

Also run these commands to supplement:
- `git diff --stat` — see file changes
- `git log --oneline -10` — recent commits
- `git status` — uncommitted work

### Step 2: Update Changelog (always)

Append an entry to `.ai/changelog/YYYY-MM.md` following the format in `.ai/skills/devlog/skill.md`.

If the current month's file doesn't exist, create it.

### Step 3: Create ADR (if a decision was made)

If a significant technical decision was made during the session:
1. Follow the workflow in `.ai/skills/adr/skill.md`
2. Create the ADR file and update the index

Skip this step if no architectural decisions were made.

### Step 4: Update Memory Files (if patterns discovered)

Update relevant files in `.ai/memory/` based on what was learned:

| File | Update when... |
|------|---------------|
| `debugging-patterns.md` | A non-obvious bug was debugged and solved |
| `known-issues.md` | A known issue was found or resolved (remove resolved ones) |
| `refactoring-log.md` | Code was refactored |

Only update files where there's genuinely new information. Don't add trivial entries.

### Step 5: Refresh CONTEXT.md (always)

Overwrite `.ai/CONTEXT.md` with fresh data:

1. **Current Phase** — Infer from conversation context (e.g., "功能开发 — 用户管理模块")
2. **Recent Changes** — Read `.ai/changelog/` files, extract the **last 10 entries** (newest first), format as table
3. **Active Decisions** — Read `.ai/decisions/README.md`, extract rows with status `accepted`
4. **Known Issues** — Read `.ai/memory/known-issues.md`, copy active entries
5. **Tech Stack** — Keep existing values unless they changed
6. **Version Anchor** — 保留现有的 Version Anchor 段落内容，不要清空。如果该段落不存在，添加空的 Version Anchor 段落。

This file is a **fixed-size snapshot** — always overwrite, never append. It serves as the entry point for AI agents starting a new session.

### Step 5.5: Version Anchor Check (if on version branch)

如果当前在版本分支上（`feat/<version>-<scope>` 格式）：

1. 解析分支名中的版本号和范围
2. 确认 `.ai/CONTEXT.md` 的 Version Anchor 段落与分支信息一致
3. 如果不一致，更新 Version Anchor：
   - **Version**: 从分支名解析
   - **Role**: 从分支名解析（如有）
   - **Branch**: 当前分支名
   - **Active PRDs**: 列出 `.specs/prd/_active/` 中的 PRD
   - **Active Designs**: 列出 `.specs/designs/_active/` 中的设计

如果不在版本分支上，跳过此步骤。

### Step 6: Archive Specs (if story/task completed)

If a story or task was completed:
1. Move the file from `.specs/stories/` or `.specs/tasks/` to `.specs/completed/YYYY-QN/`
2. Prefix with completion date: `YYYY-MM-DD_original-name.md`
3. Add `## Completion Notes` section

Skip if no specs were involved.

### Step 7: Summary Report

Output a concise summary:

```
## Wrap-up Complete

### Updated
- [x] Changelog: .ai/changelog/YYYY-MM.md
- [x] CONTEXT.md: Refreshed
- [x] ADR: .ai/decisions/NNN-title.md (or "No new decisions")
- [x] Memory: <file> (or "No new patterns")
- [x] Specs: Archived story-NNN (or "No specs involved")

### Key Takeaways
- <1-2 most important things to remember>
```

## Guidelines

- Be selective — only record information that has future value
- Don't duplicate information across files; each file has a specific purpose
- Prefer updating existing entries over creating new ones
- If nothing meaningful happened in a category, skip it
- Keep the summary brief and actionable
