# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Random-Timer** — A software project.

## Project Rules

@.ai/rules/*.md

## Architecture Decisions & Memory

- `.ai/decisions/` — ADRs with full context and rationale (@.ai/decisions/README.md)
- `.ai/changelog/` — Monthly change logs with context, reasoning, and impact
- `.ai/skills/` — Portable skill definitions; run `npx @siliconoid/agentkit sync` to generate platform adapters
- `.ai/memory/` — Shared memory files (debugging patterns, known issues, refactoring log)
- `.specs/` — PRD、设计、Epic、Story — 通过 /spec 管理 (@.specs/README.md)

### Memory Commands

| Command | Purpose |
|---------|---------|
| `/adr` | Record an architecture decision |
| `/devlog` | Append a changelog entry |
| `/wrap-up` | End-of-task: update all memory files at once |
| `/spec` | 管理 PRD、设计、版本快照和追踪矩阵 |

## 交互语言

所有 AI 回复、代码注释、commit message 和文档一律使用 **中文**。
