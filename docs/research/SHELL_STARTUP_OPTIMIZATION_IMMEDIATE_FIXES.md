<DONE>
# Shell Startup Optimization - Immediate Fixes

**Date:** 2026-02-17
**Current:** 654ms
**Target:** <=80ms
**Gap:** 574ms

---

## Research Summary

Based on research from:

- **santacloud.dev** - "How I Optimized My ZSH Startup to Under 70ms"
- **openreplay.com** - "Why zsh Is Slow to Start (and How to Fix It)"
- **scottspence.com** - "Speeding Up My ZSH Shell"

---

## Key Optimizations Identified

### 1. Lazy Loading Version Managers (200-300ms reduction)

- **pyenv**: 172ms → lazy load
- **nvm**: 300-500ms → lazy load
- **conda**: Similar overhead → lazy load

### 2. compinit Optimization (50-100ms reduction)

- Call `compinit` exactly once
- Use `compinit -C` to skip security checks (faster)
- Cache completions properly
- Compile zsh scripts with `zcompile`

### 3. Plugin Optimization (100-200ms reduction)

- Remove unused plugins
- Use async loading
- Defer heavy plugins
- Compile plugins with `zcompile`

### 4. Theme Optimization (20-50ms reduction)

- Use lightweight themes
- Avoid git status queries in prompt
- Use async prompt rendering

### 5. Auto-Update Disabling (10-50ms reduction)

- Disable Oh-My-Zsh auto-updates
- Disable plugin auto-updates

### 6. PATH Optimization (5-20ms reduction)

- Consolidate PATH exports
- Avoid command substitution in PATH (e.g., `$(go env GOPATH)`)

---

## Immediate Fixes Applied

### ✅ 1. direnv Flake Search Fix

- Updated `.envrc` to check subdirectories for `flake.nix`
- Prevents error when in parent directory

### ✅ 2. FUNCNEST Limit Increase

- Added `export FUNCNEST=1000` to `.envrc`
- Prevents nested function errors

### 🔄 3. Shell Config Optimization (IN PROGRESS)

- Need to check and optimize:
  - `~/.zshenv`
  - `~/.zshrc`
  - `~/.zsh_bundle.zsh`
  - Plugin loading
  - compinit calls
  - Version manager initialization

---

## Implementation Plan

### Phase 1: Profile Current Setup

1. ✅ Measure current startup time (654ms)
2. 🔄 Run `zprof` to identify bottlenecks
3. 🔄 Identify slow components

### Phase 2: Apply Quick Wins

1. 🔄 Disable auto-updates
2. 🔄 Lazy load version managers
3. 🔄 Optimize compinit
4. 🔄 Remove unused plugins
5. 🔄 Consolidate PATH exports

### Phase 3: Advanced Optimizations

1. 🔄 Compile zsh scripts
2. 🔄 Use async loading
3. 🔄 Optimize theme
4. 🔄 Profile and measure improvements

### Phase 4: Verify

1. 🔄 Measure final startup time
2. 🔄 Verify all functionality works
3. 🔄 Document changes

---

## Expected Results

| Optimization             | Expected Reduction | Cumulative  |
| ------------------------ | ------------------ | ----------- |
| Lazy load pyenv          | 172ms              | 482ms       |
| Optimize compinit        | 50ms               | 432ms       |
| Remove unused plugins    | 100ms              | 332ms       |
| Async loading            | 50ms               | 282ms       |
| Theme optimization       | 30ms               | 252ms       |
| PATH consolidation       | 10ms               | 242ms       |
| Compile scripts          | 50ms               | 192ms       |
| Additional optimizations | 112ms              | **80ms** ✅ |

---

**Status:** 🔄 **PROFILING AND OPTIMIZING**
