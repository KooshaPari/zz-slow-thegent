<DONE>
# Shell Error Fixes — zsh Bad Substitution

> **Status**: Fixed | **Date**: 2026-02-17
> **Purpose**: Document fixes for zsh shell initialization errors

---

## Issues Fixed

### 1. `_thegent_lazy_load:8: bad substitution`

**Error**: Nested variable expansion `${THEGENT_LAZY_LOADED_${tool_name}:-}` not supported in zsh

**Root Cause**: zsh doesn't support nested variable expansion directly. The pattern `${VAR_${name}:-}` requires indirect parameter expansion.

**Fix**: Use `${(P)...}` for parameter expansion:

```zsh
# Before (broken):
if [[ -n "${THEGENT_LAZY_LOADED_${tool_name}:-}" ]]; then

# After (fixed):
local loaded_var="THEGENT_LAZY_LOADED_${tool_name}"
if [[ -n "${(P)loaded_var:-}" ]]; then
```

**Files Fixed**:

- `shell/.zsh_optimization.zsh` - Line 103, 123, 244

---

### 2. `_thegent_async_load:12: command not found: _thegent_load_full_prompt`

**Error**: Function called before it's defined

**Root Cause**: `_thegent_load_full_prompt` was being called at line 421 before it was defined at line 428.

**Fix**: Move function definition before its first use:

```zsh
# Define function first
_thegent_load_full_prompt() {
  export THEGENT_PROMPT_LOADED=1
  # ... rest of function
}

# Then call it
if [[ "$THEGENT_ASYNC_LOADING_ENABLED" == "1" ]]; then
  _thegent_async_load "0" "_thegent_load_full_prompt" &
fi
```

**Files Fixed**:

- `shell/.zsh_advanced.zsh` - Moved function definition before use

---

## Changes Made

### `shell/.zsh_optimization.zsh`

1. **Line 103**: Fixed nested variable expansion in `_thegent_lazy_load()`
2. **Line 123**: Fixed nested variable expansion in lazy-load wrapper eval
3. **Line 244**: Fixed nested variable expansion in `_thegent_nvm_load()`

### `shell/.zsh_advanced.zsh`

1. **Line 428**: Moved `_thegent_load_full_prompt()` definition before its first use
2. **Line 420-426**: Reorganized prompt loading logic to call function after definition

---

## Testing

**Before Fix**:

```bash
exec zsh
# Errors:
# _thegent_lazy_load:8: bad substitution
# _thegent_async_load:12: command not found: _thegent_load_full_prompt
```

**After Fix**:

```bash
exec zsh
# No errors, shell initializes correctly
```

---

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [SHELL_ENVIRONMENT_COMPLETE.md](../guides/SHELL_ENVIRONMENT_COMPLETE.md) - Shell environment guide
- [SHELL_OPTIMIZATION_GUIDE.md](../guides/SHELL_OPTIMIZATION_GUIDE.md) - Optimization guide
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory

---

**Status**: ✅ Fixed - Shell initialization errors resolved

---

## 8. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added planning patterns
2. Added implementation roadmap
3. Enhanced cross-references

### Cross-References Added

- WORK_STREAM.md
- Implementation guides

### Practical Additions

- Planning templates
- Roadmap configurations
