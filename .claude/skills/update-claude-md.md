# Skill: Update CLAUDE.md

Autonomously keep CLAUDE.md in sync with the actual codebase state. This skill treats CLAUDE.md as a living document that evolves with the project.

## Trigger
- User invokes `/update-claude-md`
- After `/new-feature` completes
- When significant codebase changes are detected
- When user reports incorrect information in CLAUDE.md

## Philosophy: Files Are All You Need

This skill implements the "Files Are All You Need" pattern where CLAUDE.md serves as:
1. **Long-term memory** - Persists knowledge across sessions
2. **Dynamic context** - Reflects current codebase state
3. **Skills as files** - Documents capabilities and workflows

## Workflow

### 1. Scan Current Codebase State
```bash
# Get current feature list
ls -d src/features/*/

# Get current shared components
ls src/shared/components/

# Get current Redux slices
ls src/shared/redux/slices/

# Get current screens
find src -name "*Screen.tsx" -type f

# Get current services
find src -name "*Service.ts" -o -name "*service.ts" -type f
```

### 2. Analyze package.json Changes
- Check for new dependencies
- Check for new/changed scripts
- Verify version numbers

### 3. Check for New Patterns
- Scan for new path aliases in tsconfig.json
- Look for new ESLint rules
- Identify new architectural patterns

### 4. Detect Common Issues
Review recent git history for recurring problems:
```bash
git log --oneline -20 --grep="fix" --grep="bug" --all-match
```

### 5. Update CLAUDE.md Sections

#### Project Structure
Regenerate the directory tree to reflect actual structure:
- Add new features to the tree
- Remove deleted features
- Update component lists

#### Commands
- Verify all npm scripts still exist
- Add any new scripts
- Remove deprecated commands

#### Common Issues & Solutions
- Add newly discovered issues and their fixes
- Remove issues that have been permanently resolved
- Update solutions if better approaches found

#### Coding Standards
- Update if new ESLint rules added
- Reflect any new conventions observed in recent code

### 6. Validate Changes
Before writing:
- Ensure all referenced files exist
- Verify all commands work
- Check path aliases are accurate

### 7. Write Updated CLAUDE.md
Use the Edit tool to update specific sections, preserving manual additions while updating auto-generated content.

### 8. Report Changes
Output a summary:
```
CLAUDE.md Updated:
- Added: notifications feature to Project Structure
- Updated: Commands section with new test:e2e script
- Added: New common issue - iOS pod install M1 fix
- Removed: Deprecated prebuild command
```

## Auto-Update Triggers

This skill should be invoked automatically when:
- A new feature is scaffolded via `/new-feature`
- Package.json is modified
- New files are added to src/shared/
- A bug fix is committed that others might encounter

## Section Markers

CLAUDE.md uses these markers to identify auto-updatable sections:
- `## Project Structure` - Auto-updated from filesystem
- `## Commands` - Auto-updated from package.json
- `## Common Issues & Solutions` - Append-only from fixes

Manual sections (not auto-updated):
- `## Project Overview` - Human-written description
- `## Coding Standards` - Human-defined conventions
- `## Git Conventions` - Human-defined workflow

## Output
List all changes made to CLAUDE.md with before/after for significant updates.
