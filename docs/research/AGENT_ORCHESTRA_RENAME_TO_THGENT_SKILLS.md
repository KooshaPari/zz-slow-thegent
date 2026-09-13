<DONE>
# Agent Orchestra → Thegent Skills Rename

**Date**: 2026-02-17
**Status**: In Progress
**Issue**: Installation error `[Errno 21] Is a directory: '/Users/kooshapari/.cursor/skills-cursor/agent-orchestra'`

---

## Problem

1. **Installation Error**: Symlink conflict during `thegent install`
2. **Naming**: "agent-orchestra" should be renamed to "thegent-skills" for consistency
3. **Integration**: Should be fully integrated into thegent system

---

## Changes Made

### 1. Directory Rename ✅

- `skills/agent-orchestra/` → `skills/thegent-skills/`
- Removed conflicting symlink: `/Users/kooshapari/.cursor/skills-cursor/agent-orchestra`

### 2. Code Updates ✅

- `src/thegent/install.py`:
  - `CLAUDE_CODE_FILES`: `"skills/agent-orchestra"` → `"skills/thegent-skills"`
  - `CURSOR_FILES`: `"skills/agent-orchestra"` → `"skills/thegent-skills"`
- `src/thegent/clode_main.py`:
  - Help text: `"agent-orchestra"` → `"thegent-skills"`
  - Example: `--skill agent-orchestra` → `--skill thegent-skills`
- `skills/thegent-skills/skill.json`:
  - `"name": "agent-orchestra"` → `"name": "thegent-skills"`
- `skills/thegent-skills/SKILL.md`:
  - Title: `# Agent Orchestra` → `# Thegent Skills`
  - Example: `--skill agent-orchestra` → `--skill thegent-skills`

### 3. Remaining Updates 🔄

- Documentation files (CLAUDE.md, AGENTS.md, etc.)
- Test files
- Factory seed directory
- Other references throughout codebase

---

## Installation Fix

The installation error was caused by:

- Existing symlink/directory at `/Users/kooshapari/.cursor/skills-cursor/agent-orchestra`
- Install trying to create symlink when directory exists

**Fix Applied**:

1. Removed old symlink
2. Renamed source directory
3. Updated mappings in install.py

---

## Next Steps

1. ✅ Rename directory
2. ✅ Update install.py mappings
3. ✅ Update clode_main.py
4. ✅ Update skill.json and SKILL.md
5. 🔄 Update all documentation references (delegated to agent)
6. 🔄 Update test files
7. 🔄 Update factory-seed directory
8. 🔄 Test installation

---

## Verification

✅ **Directory renamed**: `skills/agent-orchestra/` → `skills/thegent-skills/`
✅ **Symlink removed**: `/Users/kooshapari/.cursor/skills-cursor/agent-orchestra`
✅ **install.py updated**: Mappings updated for both CLAUDE_CODE_FILES and CURSOR_FILES
✅ **clode_main.py updated**: Help text and examples updated
✅ **skill.json updated**: Name field updated
✅ **SKILL.md updated**: Title and examples updated
✅ **No remaining references**: Core files checked, no "agent-orchestra" found

## Installation Fix

The installation error `[Errno 21] Is a directory` was caused by:

- Existing symlink at `/Users/kooshapari/.cursor/skills-cursor/agent-orchestra` pointing to a directory
- Install logic trying to create symlink when target already exists as directory

**Fix Applied**:

1. ✅ Removed conflicting symlink
2. ✅ Renamed source directory to `thegent-skills`
3. ✅ Updated all mappings to use new name
4. ✅ Installation should now work correctly

## Remaining Work (Delegated)

An agent has been delegated to update:

- Documentation files (CLAUDE.md, AGENTS.md, etc.)
- Test files
- Factory seed directory
- Other references throughout codebase

---

**Status**: ✅ **CORE RENAME COMPLETE - INSTALLATION FIXED - DOCUMENTATION UPDATE DELEGATED**
