<DONE>
# direnv and FUNCNEST Fix (2026-02-18)

## Problem

When running `exec zsh` in the `kush` directory, direnv was encountering multiple issues:

1. **Nix flake error**: `flake.nix` was not tracked by git (Nix requires tracked files)
2. **FUNCNEST error**: `maximum nested function level reached; increase FUNCNEST?`
3. **Slow direnv execution**: direnv was taking a long time to evaluate

## Root Causes

1. **Untracked flake.nix**: The `flake.nix` file in `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent` existed but wasn't tracked by git. Nix requires files to be tracked by git to use them in flakes.

2. **Nested function calls**: The `.envrc` file was using `cd "$local_flake" && use flake && cd -` pattern, which caused nested function calls in the direnv hook context, hitting the FUNCNEST limit.

3. **Git lock file**: A stale `.git/index.lock` file was preventing git operations.

## Solution

### 1. Added flake.nix to Git

```bash
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/thegent
rm -f .git/index.lock  # Remove stale lock file
git add flake.nix      # Add flake.nix to git
```

### 2. Fixed .envrc to Avoid Nested Function Issues

**Before:**

```bash
if [ -n "$local_flake" ]; then
  cd "$local_flake" && use flake && cd - >/dev/null 2>&1
fi
```

**After:**

```bash
if [ -n "$local_flake" ] && [ -f "$local_flake/flake.nix" ]; then
  # Use subshell to avoid nested function issues with cd
  (
    cd "$local_flake" || exit 1
    use flake
  )
fi
```

**Key changes:**

- Use subshell `(...)` instead of `cd` and `cd -` pattern
- Subshell isolates the directory change, preventing nested function calls
- Added explicit check for `flake.nix` existence before using it

### 3. Added Non-Interactive Shell Check

Added early return for non-interactive shells to skip flake evaluation:

```bash
# Skip flake evaluation in non-interactive shells to avoid hangs
if [ -z "${PS1:-}" ] && [ ! -t 0 ]; then
  # Non-interactive shell: just set up basic Python venv
  ...
fi
```

### 4. Ensured FUNCNEST is Set

- FUNCNEST is already set in `~/.zshenv` (line 5: `export FUNCNEST=1000`)
- Added explicit export in `.envrc` as well for redundancy

## Files Modified

1. **`/Users/kooshapari/temp-PRODVERCEL/485/kush/.envrc`**
   - Changed `cd` pattern to use subshell
   - Added non-interactive shell check
   - Added explicit FUNCNEST export
   - Improved error handling

2. **`/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/flake.nix`**
   - Added to git (now tracked)

## Verification

After the fix:

- ✅ `flake.nix` is tracked by git
- ✅ `.envrc` uses subshell to avoid nested function calls
- ✅ Non-interactive shells skip flake evaluation
- ✅ FUNCNEST is set early in `.zshenv` and redundantly in `.envrc`

## Testing

To test the fix:

```bash
cd /Users/kooshapari/temp-PRODVERCEL/485/kush
exec zsh  # Should now work without FUNCNEST errors
```

Expected behavior:

- direnv loads without errors
- FUNCNEST error should not occur
- Flake evaluation should work (if nix is available)
- Fallback to venv should work (if nix is not available)

## Prevention

To prevent similar issues in the future:

1. **Always track flake.nix**: Add `flake.nix` to git when creating it
2. **Use subshells in direnv**: Avoid `cd` and `cd -` patterns in `.envrc` files
3. **Set FUNCNEST early**: Ensure FUNCNEST is set in `.zshenv` before direnv hook loads
4. **Check for git locks**: Remove stale `.git/index.lock` files if git operations fail

## Related Issues

- Shell startup optimization (target: ≤80ms)
- direnv performance (avoiding hangs in non-interactive shells)
- Nix flake integration with git

---

## Update: Venv-Only (2026-02-18)

### Why Nix Flake Was Removed from kush/.envrc

Nix flake evaluation invokes `git` internally. When a stale `.git/index.lock` exists (from a crashed git process), nix fails with:

```
fatal: Unable to create '.git/index.lock': File exists.
Another git process seems to be running...
```

**Multitenant git / gitoxide**: The thegent project has multitenant git logic in `hooks/lib/common.sh` and `hooks/lib/git-wrapper.sh` that waits for `index.lock` and steals stale locks after 10 seconds. However, that only runs when `git` is invoked through the thegent git shim. Nix's own `git` calls for flake evaluation do **not** go through that shim, so the multitenant logic never runs and the stale lock blocks nix.

**Gitoxide**: Mentioned in plans but not implemented; `GIT_TOOLING_AUDIT_AND_PLAN.md` states it is not used.

### Final Fix

`kush/.envrc` was simplified to **venv-only**. No flake evaluation in direnv. This avoids:

- Nix + git index.lock contention
- FUNCNEST / nested function issues
- Slow direnv startup

For nix: run `cd thegent && nix develop` manually when needed.

### ~/.envrc via thegent install

**Long-term fix:** `thegent install -t envrc` (or `thegent install -t all`) installs the guarded `~/.envrc` from `shell/envrc.home.template`. Ensures $HOME is set up correctly for all users.

### Long-Term / Optimal Fix

See **[GIT_INDEX_LOCK_OS_LEVEL_AND_AGENT_SYSTEM_USER_PLAN.md](./GIT_INDEX_LOCK_OS_LEVEL_AND_AGENT_SYSTEM_USER_PLAN.md)** for:

- **Stale lock daemon:** `thegent git lock-cleanup` (periodic removal of stale `index.lock`)
- **System-level git wrapper:** `thegent install-shims --system` so nix, direnv, and all tools use lock-aware git
- **Agent system user:** Hooks and git wrapper for launchd/systemd agent services

---

_Fix Date: 2026-02-18_
_Status: ✅ Fixed (venv-only)_
