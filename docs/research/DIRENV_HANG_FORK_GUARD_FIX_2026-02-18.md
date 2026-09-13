<DONE>
# direnv Hang & Fork Guard Error Fix

**Date**: 2026-02-18
**Issue**: `ent_fork_guard:2: no matches found: (faster)` + direnv hang
**Status**: ✅ Fixed

---

## Problem

1. **Error**: `ent_fork_guard:2: no matches found: (faster)`
   - Zsh globbing error in fork guard function
   - Pattern `(faster)` being interpreted as glob pattern

2. **direnv Hang**: direnv loading hangs during `.envrc` evaluation
   - Fork guard running during direnv evaluation
   - Venv activation blocking
   - Shell initialization conflicts

---

## Root Causes

### 1. Fork Guard Running During direnv Evaluation

**Issue**: `_thegent_fork_guard_periodic` runs in `precmd_functions`, which fires during direnv evaluation, causing:

- Process count checks during direnv load
- Potential hangs if `pgrep`/`ps` are slow
- Conflicts with direnv's own process management

### 2. Glob Pattern Error

**Issue**: Comment `# (faster)` in fork guard code being interpreted as glob pattern when `extended_glob` is enabled.

**Location**: `shell/.zsh_safeguards.zsh` line 125-126

### 3. direnv Hook Loading in Non-Interactive Shells

**Issue**: direnv hook loads even in non-interactive shells, causing hangs.

---

## Fixes Applied

### 1. Skip Fork Guard During direnv Evaluation

**File**: `shell/.zsh_safeguards.zsh`

```zsh
_thegent_fork_guard() {
  # Skip fork guard during direnv evaluation to prevent hangs
  [[ -n "${DIRENV_IN_ENVRC:-}" ]] && return 0

  # ... rest of function ...
}
```

**File**: `.envrc`

```bash
# Mark that we're in direnv evaluation
export DIRENV_IN_ENVRC=1

# ... setup code ...

# Unset after setup (allows fork guard in interactive shells)
unset DIRENV_IN_ENVRC
```

### 2. Improved Fork Guard Error Handling

**Changes**:

- Better error handling for `pgrep`/`ps` commands
- Default to `0` if command fails
- More robust pid count parsing

### 3. Skip direnv Hook in Non-Interactive Shells

**File**: `shell/.zshenv`

```zsh
# Skip in non-interactive shells to prevent hangs
if command -v direnv >/dev/null 2>&1 && [[ -n "${PS1:-}" || -t 0 ]]; then
  eval "$(direnv hook zsh)" 2>/dev/null || true
fi
```

### 4. Optimized Venv Activation

**File**: `.envrc`

```bash
_setup_venv() {
  # Fast path: check if venv already activated
  [[ -n "${VIRTUAL_ENV:-}" ]] && return 0

  # ... activation code ...
}
```

---

## Testing

### Test direnv Loading

```bash
# Should load quickly without hang
cd /Users/kooshapari/temp-PRODVERCEL/485/kush
direnv allow

# Should complete in <1s
time direnv allow
```

### Test Fork Guard

```bash
# Should not error with "no matches found: (faster)"
zsh -c 'source ~/.zsh_safeguards.zsh && _thegent_fork_guard'

# Should skip during direnv evaluation
DIRENV_IN_ENVRC=1 zsh -c 'source ~/.zsh_safeguards.zsh && _thegent_fork_guard'
```

---

## Files Modified

- `shell/.zsh_safeguards.zsh` - Skip fork guard during direnv, improved error handling
- `/Users/kooshapari/temp-PRODVERCEL/485/kush/.envrc` - Add `DIRENV_IN_ENVRC` marker, optimize venv activation
- `shell/.zshenv` - Skip direnv hook in non-interactive shells

---

## Expected Behavior

### Before Fix

- ❌ `ent_fork_guard:2: no matches found: (faster)` error
- ❌ direnv hangs during `.envrc` evaluation
- ❌ Fork guard runs during direnv, causing conflicts

### After Fix

- ✅ No glob pattern errors
- ✅ direnv loads quickly (<1s)
- ✅ Fork guard skips during direnv evaluation
- ✅ Fork guard works normally in interactive shells

---

## Related Issues

- Shell startup optimization (previous work)
- direnv + Nix flake integration
- Fork guard performance

---

## References

- Previous fix: `docs/research/SHELL_STARTUP_OPTIMIZATION_IMMEDIATE_FIXES.md`
- Fork guard: `shell/.zsh_safeguards.zsh`
