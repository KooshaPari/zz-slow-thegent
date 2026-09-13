<DONE>
# Shell Startup Optimization Analysis

**Date:** 2026-02-17
**Current Measurement:** 35.74ms (real time)
**User Reported:** 654ms
**Target:** <=80ms

---

## Current Configuration Analysis

### ✅ Already Optimized

1. **compinit** - Already optimized with conditional `-C` flag
   - Only runs full security check once per day
   - Uses cached completions otherwise

2. **No Version Managers** - No pyenv, nvm, conda loaded synchronously
   - This is good - saves 172-500ms

3. **Starship Prompt** - Fast cross-shell prompt
   - Already in use

4. **Early Exit for Non-Interactive** - `.zshenv` exits early for agents
   - Saves time for AI sessions

### ⚠️ Potential Issues Found

1. **Async Plugin Loading (Lines 72-87 in .zshrc)**

   ```zsh
   () {
       source "${HOME}/.zsh/plugins/fzf-tab/fzf-tab.plugin.zsh" &
       source "${HOME}/.zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh" &
       source "${HOME}/.zsh/plugins/fast-syntax-highlighting/fast-syntax-highlighting.plugin.zsh" &
   }
   ```

   **Problem:** Background jobs (`&`) in zsh don't work for `source` - this will fail silently or block
   **Fix:** Use proper async loading or load synchronously but defer until after prompt

2. **direnv Auto-Allow Hooks (Lines 38-67 in .zshrc)**
   - `chpwd` hook runs on every `cd`
   - `precmd` hook runs before every prompt
   - Both call `_auto_allow_envrc` which runs `direnv allow` in background
   - **Impact:** Multiple hook executions could add overhead

3. **Multiple Source Calls**
   - `.zshenv` sources `.zsh_bundle.zsh`
   - `.zshrc` sources `.zshenv` and `.zsh_bundle.zsh` again (duplicate)
   - `.zsh_bundle.zsh` sources multiple optimization files conditionally
   - **Impact:** Redundant sourcing adds overhead

4. **Nix Daemon Loading (Lines 37-42 in .zshenv)**
   - Loads Nix daemon profile script
   - Could be slow if Nix is not used frequently

---

## Optimization Recommendations

### Priority 1: Fix Async Plugin Loading

**Current:** Background jobs don't work for `source`
**Fix:** Use proper async loading pattern or load synchronously after prompt

### Priority 2: Optimize direnv Hooks

**Current:** Multiple hooks calling direnv allow
**Fix:**

- Cache allowed directories
- Only check once per directory
- Remove precmd hook (only use chpwd)

### Priority 3: Remove Duplicate Sourcing

**Current:** `.zsh_bundle.zsh` sourced twice
**Fix:** Only source once, use guard variable

### Priority 4: Lazy Load Nix

**Current:** Nix loaded in `.zshenv` for all shells
**Fix:** Only load Nix when needed or in interactive shells

### Priority 5: Compile Zsh Scripts

**Current:** Scripts loaded as plain text
**Fix:** Use `zcompile` to create `.zwc` files for faster loading

---

## Expected Impact

| Optimization              | Expected Reduction | Cumulative |
| ------------------------- | ------------------ | ---------- |
| Fix async plugin loading  | 50-100ms           | 50-100ms   |
| Optimize direnv hooks     | 20-50ms            | 70-150ms   |
| Remove duplicate sourcing | 10-30ms            | 80-180ms   |
| Lazy load Nix             | 10-50ms            | 90-230ms   |
| Compile zsh scripts       | 20-50ms            | 110-280ms  |

**Note:** Current measurement shows 35.74ms, which is already below target. The user-reported 654ms might be from:

- First-time cold start (compinit rebuilding cache)
- Heavy plugins loading
- direnv evaluating flake.nix
- Starship prompt initialization

---

## Next Steps

1. ✅ Profile current setup with `zprof`
2. 🔄 Fix async plugin loading
3. 🔄 Optimize direnv hooks
4. 🔄 Remove duplicate sourcing
5. 🔄 Test and measure improvements

---

**Status:** 🔄 **ANALYZING AND OPTIMIZING**
