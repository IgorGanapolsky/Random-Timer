# Project Calibrate — Brownfield Project Rules Alignment

Scan an existing (brownfield) project's real state and calibrate all AI configuration files to accurately reflect the project's actual tech stack, structure, and conventions. This ensures AI agents generate code that is consistent with the existing codebase.

## Core Principle

**This skill calibrates AI rules to match the project — it does NOT modify project source code, configurations, or dependencies.** The goal is to make AI agents understand the project as-is, so that newly generated code integrates seamlessly with existing patterns.

## When to Use

- After installing AgentKit into an existing/brownfield project
- When `.ai/rules/` contain scaffold defaults that don't match the project
- When the project's tech stack, structure, or conventions have changed
- When AI agents are generating code that doesn't fit the project's patterns
- Periodically, to keep AI configuration in sync with project evolution

---

## Three-Level Arbitration Strategy

Every rule is classified into one of three levels. This determines how conflicts between the rule and project reality are resolved:

### HARD Rules — AI Behavioral Mandates (Keep as-is)

Rules about **how the AI agent should behave**, regardless of project specifics. These are universal and should NOT be changed to match the project.

**Examples:** "Read existing files before writing code", "Keep changes minimal", "Ask when uncertain", "Rules directory is single source of truth"

**File:** `13-ai-agent.md` (behavioral instructions — preserve core directives)

### SOFT Rules — Tech Convention Defaults (Adapt to project)

Rules about **specific technology choices and coding conventions**. When the project uses a different technology or pattern than the rule describes, **update the rule to match the project**.

**Examples:** Rule says "CSS Modules" but project uses Tailwind; Rule says "React" but project uses Vue; Rule says "interface preferred" but project uses `type` everywhere.

**Files:** `03-coding-conventions.md`, `06-typescript.md`, `07-react.md`, `08-styling.md`, `09-naming.md`, `10-git-workflow.md`, `11-testing.md`, `12-forbidden-patterns.md`

### INFO Rules — Descriptive Facts (Must match reality 100%)

Rules that **describe what the project is** — tech stack, architecture, directory structure, environment commands. These must be rewritten to reflect the actual project state.

**Files:** `01-project-overview.md`, `02-architecture.md`, `04-directory-structure.md`, `05-environment.md`

---

## Workflow Steps

### Phase 1: Discovery — Scan Project Reality

Perform a comprehensive, read-only scan of the project. Collect facts, do not modify anything.

#### 1.1 Tech Stack Detection

Read dependency manifests to extract frameworks, libraries, and versions:

```
Scan targets (read whichever exist):
- package.json / package-lock.json / yarn.lock / pnpm-lock.yaml
- go.mod / go.sum
- pyproject.toml / requirements.txt / Pipfile
- Cargo.toml
- composer.json
- Gemfile
- build.gradle / pom.xml
- .tool-versions / .node-version / .nvmrc / .python-version
```

Extract and record:
- Primary language(s) and version(s)
- Framework(s) and version(s)
- UI component library (Ant Design, shadcn, MUI, Element UI, etc.)
- CSS approach (Tailwind, CSS Modules, styled-components, SCSS, etc.)
- State management (Redux, Zustand, Pinia, Vuex, Context, etc.)
- HTTP client (axios, fetch, ky, got, etc.)
- Testing framework (Jest, Vitest, Playwright, Cypress, pytest, etc.)
- Build tool (Vite, Webpack, Turbopack, esbuild, etc.)
- Linter/Formatter (ESLint, Prettier, Biome, Ruff, etc.)
- Package manager (npm, yarn, pnpm, bun, etc.)

#### 1.2 Directory Structure Scan

```bash
# Scan actual directory tree (depth 3, excluding common noise)
find . -maxdepth 3 -type d \
  -not -path '*/node_modules/*' \
  -not -path '*/.git/*' \
  -not -path '*/dist/*' \
  -not -path '*/build/*' \
  -not -path '*/.next/*' \
  -not -path '*/.nuxt/*' \
  -not -path '*/__pycache__/*' \
  -not -path '*/venv/*' \
  -not -path '*/.ai/*' \
  -not -path '*/_bmad/*' \
  | head -80
```

Also identify:
- Is this a monorepo? (workspaces in package.json, lerna.json, nx.json, turbo.json)
- Is this fullstack? (separate frontend/backend directories)
- Entry points (src/index, src/main, src/app, pages/, app/, etc.)
- Key architectural patterns visible from structure

#### 1.3 Code Pattern Sampling

Read 3-5 representative source files to detect actual conventions:

- **Component pattern**: Class vs functional, file naming, export style
- **Naming conventions**: camelCase, snake_case, kebab-case for files/directories
- **Import style**: Path aliases (@/, ~/), relative paths, barrel exports
- **Styling approach**: How styles are actually applied in components
- **Type usage**: TypeScript strict? Liberal `any`? JSDoc? Pure JavaScript?
- **Test patterns**: Co-located or separate? Naming convention? Framework idioms?

#### 1.4 Existing Documentation Scan

Read current AI configuration files:

```
Scan all that exist:
- .ai/rules/*.md              (all rule files)
- CLAUDE.md                    (Claude Code root doc)
- .cursor/rules/project.mdc   (Cursor rules)
- AGENTS.md                    (Codex root doc)
- GEMINI.md                    (Gemini root doc)
- .agent/rules.md             (Antigravity root doc)
- .windsurfrules               (Windsurf merged rules)
- README.md                    (Project readme)
- .ai/agentkit.json           (AgentKit config)
```

#### 1.5 Git Convention Detection

```bash
# Detect branch naming and commit message patterns
git log --oneline -20
git branch -a | head -20
```

Record: main branch name, branch naming pattern, commit message format.

---

### Phase 2: Audit — Compare and Report

Compare every scanned fact against every rule file. Generate a structured audit report.

#### 2.1 Per-Rule Analysis

For each file in `.ai/rules/`, compare its content against discovered reality:

| Status | Meaning |
|--------|---------|
| ✅ MATCH | Rule accurately reflects project reality |
| ⚠️ DRIFT | Rule is partially correct but has outdated/inaccurate details |
| ❌ CONFLICT | Rule assumes technology/pattern the project does not use |
| 🆕 MISSING | Project has important patterns/tech not covered by any rule |
| ➖ N/A | Rule topic is irrelevant to this project (e.g., React rules for a Python project) |

#### 2.2 Platform File Analysis

For each platform root doc (CLAUDE.md, GEMINI.md, etc.), check:
- Does the project description match reality?
- Are referenced directories/files correct?
- Are listed commands runnable?

#### 2.3 Output Audit Report

Present the report to the user in this format:

```markdown
# Project Calibration Audit Report

## Project Reality Summary
- **Project**: [detected name]
- **Language**: [detected] v[version]
- **Framework**: [detected] v[version]
- **UI Library**: [detected]
- **Styling**: [detected approach]
- **Testing**: [detected framework]
- **Build**: [detected tool]
- **Package Manager**: [detected]

## Rules Audit

| # | Rule File | Status | Key Findings | Proposed Action |
|---|-----------|--------|-------------|----------------|
| 1 | 01-project-overview.md | ⚠️ DRIFT | Tech stack table has placeholder values | Rewrite with detected tech stack |
| 2 | 02-architecture.md | ⚠️ DRIFT | Architecture description is generic | Rewrite based on detected patterns |
| ... | ... | ... | ... | ... |

## Platform Files Audit

| File | Exists | Status | Proposed Action |
|------|--------|--------|----------------|
| CLAUDE.md | ✅ | ⚠️ DRIFT | Update project description and commands |
| GEMINI.md | ✅ | ⚠️ DRIFT | Sync with updated rules |
| ... | ... | ... | ... |

## Irrelevant Rules (Candidates for Removal)

| File | Reason |
|------|--------|
| 07-react.md | Project uses Vue, not React |
| ... | ... |
```

#### 2.4 Wait for User Confirmation

**STOP HERE and present the audit report to the user.** Ask:

> "以上是项目校准审计报告。请确认：
> 1. 哪些修正项你同意执行？（默认全部执行）
> 2. 有没有需要跳过的？
> 3. 标记为 N/A 的规则文件，是否要删除还是保留？
> 4. 有没有遗漏的项目特征需要补充？"

**Do NOT proceed to Phase 3 until the user explicitly confirms.**

---

### Phase 3: Calibrate — Apply Corrections

After user confirmation, apply corrections file by file.

#### 3.1 Calibration Principles

1. **Point-fix, don't rewrite**: Modify only the sections that are incorrect. Preserve the overall structure and formatting of each rule file.
2. **Preserve the `<!-- tech-stack: ... -->` comment** on line 1 of each rule file.
3. **Maintain the rule's tone and style**: Rules should read as authoritative instructions to AI agents, not as project documentation.
4. **For SOFT rules**: Keep the prescriptive structure but update the specific technologies/patterns. For example, if the rule says "Use CSS Modules" but the project uses Tailwind, change to "Use Tailwind utility classes" — keep the directive tone.
5. **For INFO rules**: Rewrite descriptive sections with actual project data. Replace all `{{placeholder}}` values. Remove generic "Describe..." prompts.
6. **For HARD rules**: Only update tech-specific references embedded within behavioral rules (e.g., if rule 13 says "Use CSS Modules" as an example, update the example but keep the behavioral instruction).
7. **For N/A rules**: If user approved removal, delete the file. If user wants to keep, add a note at the top: `<!-- NOTE: This rule is not applicable to the current project stack but is retained for reference. -->`
8. **For MISSING patterns**: Create new rule files with the next available number, following the existing format.

#### 3.2 Rules Calibration Order

Process rules in this order (dependencies first):

1. `01-project-overview.md` — Foundation: tech stack table
2. `04-directory-structure.md` — Foundation: actual directory tree
3. `02-architecture.md` — Depends on 01 + 04
4. `05-environment.md` — Commands and env vars
5. `03-coding-conventions.md` — Conventions observed in code
6. `06-typescript.md` (or equivalent language rule)
7. `07-react.md` (or equivalent framework rule)
8. `08-styling.md`
9. `09-naming.md`
10. `10-git-workflow.md`
11. `11-testing.md`
12. `12-forbidden-patterns.md`
13. `13-ai-agent.md` — Last: update only tech references, keep behavior

#### 3.3 Platform Root Docs Calibration

After rules are updated, regenerate or update platform root docs:

**For each existing platform file**, update to reflect the calibrated rules:

- **CLAUDE.md**: Update project description, tech stack summary, key commands, and rule references
- **GEMINI.md**: Same as above, adapted to Gemini format
- **AGENTS.md**: Same, for Codex
- **.cursor/rules/project.mdc**: Same, in MDC format
- **.agent/rules.md**: Same, for Antigravity
- **.windsurfrules**: This is auto-generated — run `npx @siliconoid/agentkit sync` after calibration, or manually regenerate by concatenating updated `.ai/rules/*.md`

**Important**: Only update platform files that already exist. Do NOT create new platform files.

#### 3.4 README.md Calibration

If README.md contains project description, tech stack, or directory structure sections, update them to be consistent with the calibrated rules. Do NOT restructure the README — only update factual content.

#### 3.5 Post-Calibration Sync

If the project uses AgentKit sync:
```bash
npx @siliconoid/agentkit sync
```

This regenerates all auto-generated platform command stubs and merged rule files.

#### 3.6 Summary Report

Output a concise calibration summary:

```markdown
## Calibration Complete

### Files Modified
- [x] .ai/rules/01-project-overview.md — Updated tech stack
- [x] .ai/rules/04-directory-structure.md — Updated directory tree
- [x] .ai/rules/07-react.md — Replaced with Vue conventions
- [x] CLAUDE.md — Updated project description
- [x] GEMINI.md — Synced with rules
- ...

### Files Removed
- .ai/rules/08-styling.md (N/A — project uses inline styles only)

### Files Created
- .ai/rules/14-vue.md — Vue-specific conventions

### Remaining TODOs
- [ ] Review 02-architecture.md — auto-generated, may need manual refinement
- [ ] Run `npx @siliconoid/agentkit sync` to update platform command stubs
```

---

## Edge Cases

### Monorepo Projects
- Scan each workspace/package separately
- Note which rules apply globally vs per-package
- If fullstack layout detected, check for `frontend/` and `backend/` rule directories

### Projects Without package.json
- Use alternative manifests (go.mod, pyproject.toml, etc.)
- Detect language from file extensions if no manifest found

### Partially Filled Rules
- Some rules may have been manually customized by the user
- Detect user-added content (anything not matching scaffold templates) and preserve it
- Only overwrite scaffold placeholder content

### Multiple Frameworks
- If project uses both React and Vue (e.g., migration in progress), note both
- Create rules for the primary framework, add notes about secondary

---

## Scope Boundaries — What This Skill Does NOT Do

- Does NOT modify project source code, configs, or dependencies
- Does NOT run code migrations or upgrades
- Does NOT create new platform configurations (only updates existing ones)
- Does NOT change AI behavioral rules (HARD rules) unless tech examples are outdated
- Does NOT enforce rules on existing code — it aligns rules WITH existing code
