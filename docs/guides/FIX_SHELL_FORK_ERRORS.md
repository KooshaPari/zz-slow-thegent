# Fix Shell Fork Errors: Quick Guide

> **Status**: Quick Fix Guide | **Date**: 2026-02-16
> **Purpose**: Immediate fixes for fork exhaustion and permission errors

---

## Immediate Fix

### Option 1: Bypass Ultra-Shim Temporarily

```bash
# Set environment variable to bypass shim
export BYPASS_ULTRA_SHIM=1

# Or disable specific tools
export USE_FAST_FIND=0
export USE_FAST_CAT=0
export USE_FAST_GREP=0

# Now try your command again
find ~/.codex -type f
```

### Option 2: Use Real Binaries Directly

```bash
# Use absolute paths to real binaries
/usr/bin/find ~/.codex -type f
/bin/cat file.txt

# Or fix PATH temporarily
export PATH="/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin:$PATH"
find ~/.codex -type f
```

### Option 3: Fix PATH Corruption

```bash
# Remove project directory from PATH
export PATH=$(echo $PATH | tr ':' '\n' | grep -v "$PWD/src" | tr '\n' ':' | sed 's/:$//')

# Or use safe PATH
export PATH="/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin"
```

---

## Root Cause

The errors are caused by:

1. **Ultra-shim intercepting commands** and trying to fork when resources are exhausted
2. **PATH includes project directory** (`src/`), causing shell to try executing Python files as commands
3. **Fork exhaustion** from too many processes or resource limits

---

## Long-Term Fix

See: `docs/plans/ULTRA_SHIM_FORK_FAILURE_FIX.md` for comprehensive solution.

---

## Quick Test

```bash
# Test if fix works
which find
# Should show: /usr/bin/find (not ~/.local/bin/find)

find ~/.codex -type f | head -5
# Should work without fork errors
```

---

## See also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) — plan index

---

## EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added practical implementation patterns
2. Added configuration examples
3. Enhanced cross-references to related documentation

### Cross-References Added

- Related research and implementation guides
- WORK_STREAM.md for tracking

### Practical Additions

- Implementation templates
- Configuration examples
- Best practices
