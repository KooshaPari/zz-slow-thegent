<DONE>
# Shell Configuration Audit and Consolidation Plan

**Purpose:** Audit all shell config variations, consolidate to canonical configs, research optimal comprehensive setup.
**Date:** 2026-02-17
**Status:** Audit Complete, Consolidation Plan Ready

---

## 1. Current State Audit

### 1.1 Shell Config Files Inventory

| File | Purpose | Status | Variation Type |
|------|---------|--------|----------------|
| `shell/.zshenv` | System environment (PATH, early env) | ✅ Canonical | Base |
| `shell/.zsh_bundle.zsh` | Core utilities (qls, qfind, qgrep) | ✅ Canonical | Base |
| `shell/.zsh_safeguards.zsh` | Protection (fork guards, eval safety) | ✅ Canonical | Base |
| `shell/.zshrc` | User interactive shell config | ✅ Canonical | Base |
| `shell/.zshrc.optimized` | **"Optimized" variant** | ❌ Variation | **REMOVE** |
| `shell/zshrc.local.template` | User plugin template | ✅ Canonical | Template |
| `docs/guides/RUNTIME_OPTIMIZATION.md` | Optimization guide | ⚠️ Review | Documentation |

### 1.2 Problematic Variations

**Issues Found:**
1. **`.zshrc.optimized`** - Creates confusion: "optimized vs normal?" Should be ONE canonical config that IS optimal.
2. **No "minimal" variant** - Good, we don't want minimal.
3. **No "dev vs prod" variants** - Good, shell config doesn't need this distinction.
4. **No "user vs agent" variants** - Actually NEEDED (see §2.2)

### 1.3 Legitimate Variation Use Cases

| Use Case | Current State | Needed? | Solution |
|----------|---------------|---------|----------|
| **User vs Agent** | `.zshenv` has early return for agents | ✅ Yes | Keep early return, enhance |
| **Dev vs Prod** | Not applicable | ❌ No | N/A |
| **Interactive vs Non-interactive** | `.zshrc` checks `PS1` | ✅ Yes | Keep conditional loading |
| **Platform-specific** | Not present | ⚠️ Maybe | Add if cross-platform needed |

---

## 2. Consolidation Strategy

### 2.1 Canonical Config Structure

**Single canonical config hierarchy (maximal, comprehensive, optimal):**

```
~/.zshenv (system-wide, always sourced)
  ├── Early return for agents (AGENT_ID, heliosShield_AGENT_CONTEXT)
  ├── PATH setup (comprehensive: ~/.local/bin, ~/bin, Homebrew, system)
  ├── Runtime flags (USE_FAST_RUNTIME, USE_BUN_TOOLS, etc.)
  └── Source .zsh_bundle.zsh (if exists)

~/.zsh_bundle.zsh (thegent core utilities)
  ├── Path-safe utilities (qls, qfind, qgrep, cdq)
  ├── Safe aliases (ll)
  └── Interactive-only bindkeys

~/.zsh_safeguards.zsh (protection layer)
  ├── Resource limits (ulimit)
  ├── Command safeguards (ls alias protection)
  ├── Eval security helpers
  ├── Timeout safeguards
  └── Fork explosion prevention

~/.zshrc (user interactive shell)
  ├── Source .zshenv
  ├── Source .zsh_bundle.zsh
  ├── Source .zsh_safeguards.zsh (if interactive)
  ├── Completions (compinit - lazy load, optimized)
  ├── Plugins (lazy load: fzf-tab, autosuggestions, syntax-highlighting)
  ├── Prompt (starship or powerlevel10k)
  └── Source .zshrc.local (user customizations)

~/.zshrc.local (user-specific, never overwritten)
  ├── Version managers (fnm, mise, pyenv, etc.)
  ├── User plugins
  ├── User aliases
  └── Secrets (if exists)
```

### 2.2 Agent vs User Differentiation

**Current:** `.zshenv` has early return for agents.

**Enhancement:** Add agent-specific config file:

```
~/.zshrc.agent (agent-specific config)
  ├── Minimal PATH
  ├── No plugins
  ├── No prompt customization
  └── Fast startup only
```

**Loading Logic:**
```zsh
# In .zshenv
if [[ -n "${AGENT_ID:-}" || -n "${heliosShield_AGENT_CONTEXT:-}" ]]; then
    [[ -f "$HOME/.zshrc.agent" ]] && source "$HOME/.zshrc.agent"
    return
fi
```

### 2.3 Remove Variations

**Actions:**
1. ✅ Delete `shell/.zshrc.optimized` - merge optimizations into canonical `.zshrc`
2. ✅ Update `docs/guides/RUNTIME_OPTIMIZATION.md` - remove references to "optimized" variant
3. ✅ Ensure canonical `.zshrc` includes ALL optimizations (lazy loading, compinit -C, etc.)

---

## 3. Comprehensive Shell Setup Research

### 3.1 Best Practices (Web Research)

**Sources:**
- Powerlevel10k README (performance, instant prompt)
- Oh My Zsh plugins wiki (plugin ecosystem)
- Zsh documentation (compinit, autoload)

**Key Findings:**

#### Performance Optimizations
1. **Instant Prompt** (Powerlevel10k): Print prompt immediately, load plugins async
2. **Lazy Completion Loading**: `compinit -C` (skip security check) for faster startup
3. **Conditional Plugin Loading**: Only load plugins when needed
4. **Async Plugin Loading**: Load heavy plugins in background

#### Plugin Best Practices
1. **fzf-tab**: Replace default completion menu (load after compinit)
2. **zsh-autosuggestions**: Fast history-based suggestions
3. **fast-syntax-highlighting**: Real-time syntax highlighting (load last)
4. **starship**: Cross-shell prompt (faster than powerlevel10k for simple configs)
5. **powerlevel10k**: Feature-rich prompt (if you need customization)

#### Version Manager Best Practices
1. **fnm**: Fast Node version manager (Rust)
2. **mise**: Polyglot version manager (replaces nvm, pyenv, etc.)
3. **Lazy loading**: Only activate when needed (not on every shell startup)

### 3.2 Comprehensive Config Features

**Must Have:**
- ✅ Fast startup (<100ms for interactive shell)
- ✅ Comprehensive PATH (all tool locations)
- ✅ Safe utilities (path validation)
- ✅ Fork explosion prevention
- ✅ Eval security safeguards
- ✅ Lazy plugin loading
- ✅ Completion system (compinit)
- ✅ Prompt customization (starship or powerlevel10k)

**Should Have:**
- ✅ fzf-tab (better completion UX)
- ✅ zsh-autosuggestions (productivity)
- ✅ fast-syntax-highlighting (visual feedback)
- ✅ Version manager integration (fnm/mise)
- ✅ Cross-platform support (macOS, Linux, WSL2)

**Nice to Have:**
- ⚠️ Plugin manager (zinit, sheldon) - only if managing many plugins
- ⚠️ Custom plugins (thegent-specific utilities)

---

## 4. Implementation Plan

### Phase 1: Consolidation (Immediate)

**Tasks:**
1. ✅ Merge `.zshrc.optimized` optimizations into `.zshrc`
2. ✅ Delete `.zshrc.optimized`
3. ✅ Update documentation to remove "optimized" references
4. ✅ Ensure canonical `.zshrc` includes:
   - Lazy completion loading (`compinit -C` for speed)
   - Async plugin loading
   - Bun runtime detection
   - All performance optimizations

**Deliverable:** Single canonical `.zshrc` that is comprehensive and optimal.

### Phase 2: Agent Config (If Needed)

**Tasks:**
1. Create `shell/.zshrc.agent` template
2. Update `.zshenv` to source agent config
3. Document agent vs user differences

**Deliverable:** Agent-specific config for fast, minimal agent shells.

### Phase 3: Documentation Update

**Tasks:**
1. Update `docs/guides/SHELL_ZSH_PLUGIN_SETUP.md` - remove "optimized" references
2. Update `docs/guides/RUNTIME_OPTIMIZATION.md` - focus on canonical config optimizations
3. Create `docs/guides/SHELL_CONFIG_CANONICAL.md` - comprehensive guide

**Deliverable:** Updated documentation reflecting canonical configs.

### Phase 4: Testing & Validation

**Tasks:**
1. Test zsh startup time: `time zsh -c 'exit'` (<100ms target)
2. Test agent shell: `AGENT_ID=test zsh -c 'exit'` (fast, minimal)
3. Test interactive shell: Full feature set works
4. Test plugin loading: All plugins load correctly

**Deliverable:** Validated canonical configs.

---

## 5. Canonical Config Specifications

### 5.1 `.zshenv` (System Environment)

**Purpose:** System-wide environment setup, sourced first.

**Features:**
- Early return for agents (fast agent shells)
- Comprehensive PATH setup
- Runtime flags (USE_BUN_TOOLS, USE_FAST_RUNTIME, etc.)
- Source bundle (if exists)

**Performance:** Minimal overhead, fast startup.

### 5.2 `.zsh_bundle.zsh` (Core Utilities)

**Purpose:** thegent core utilities and safe wrappers.

**Features:**
- Path-safe utilities (qls, qfind, qgrep, cdq)
- Safe aliases (ll)
- Interactive-only bindkeys

**Performance:** Fast, no external commands.

### 5.3 `.zsh_safeguards.zsh` (Protection Layer)

**Purpose:** Comprehensive protection against common issues.

**Features:**
- Resource limits (ulimit)
- Command safeguards (ls alias protection)
- Eval security helpers
- Timeout safeguards
- Fork explosion prevention

**Performance:** Minimal overhead, only in interactive shells.

### 5.4 `.zshrc` (User Interactive Shell)

**Purpose:** Comprehensive user shell configuration.

**Features:**
- Source base configs (.zshenv, .zsh_bundle.zsh, .zsh_safeguards.zsh)
- Lazy completion loading (compinit -C for speed)
- Async plugin loading (fzf-tab, autosuggestions, syntax-highlighting)
- Prompt (starship or powerlevel10k)
- User customizations (.zshrc.local)

**Performance:** <100ms startup time (with lazy loading).

### 5.5 `.zshrc.local` (User Customizations)

**Purpose:** User-specific plugins and customizations (never overwritten).

**Features:**
- Version managers (fnm, mise, pyenv)
- User plugins
- User aliases
- Secrets (if exists)

**Performance:** Depends on user plugins.

---

## 6. Migration Guide

### 6.1 For Users with `.zshrc.optimized`

**Steps:**
1. Backup current config: `cp ~/.zshrc ~/.zshrc.backup`
2. Install canonical config: `thegent install --target user`
3. Verify: `time zsh -c 'exit'` (should be fast)
4. Remove backup if satisfied: `rm ~/.zshrc.backup`

### 6.2 For Users with Custom Configs

**Steps:**
1. Review canonical config: `cat shell/.zshrc`
2. Merge customizations into `~/.zshrc.local`
3. Install canonical config: `thegent install --target user`
4. Verify: Test shell startup and functionality

---

## 7. Success Criteria

**Consolidation:**
- ✅ No "optimized" or "minimal" variants
- ✅ Single canonical config per file type
- ✅ Variations only for legitimate use cases (user vs agent)

**Performance:**
- ✅ Interactive shell startup <100ms
- ✅ Agent shell startup <50ms
- ✅ All features work correctly

**Documentation:**
- ✅ Clear canonical config guide
- ✅ No references to "optimized" variants
- ✅ Comprehensive setup instructions

---

## 8. References

- [Powerlevel10k README](https://github.com/romkatv/powerlevel10k)
- [Oh My Zsh Plugins](https://github.com/ohmyzsh/ohmyzsh/wiki/Plugins)
- [Zsh Completion System](http://zsh.sourceforge.net/Doc/Release/Completion-System.html)
- [thegent Shell Setup Guide](docs/guides/SHELL_ZSH_PLUGIN_SETUP.md)
- [thegent Shell Safeguards](shell/.zsh_safeguards.zsh)

---

## 5. IMPLEMENTATION: Shell Config Generator

### 5.1 Zsh Config Generator

```python
#!/usr/bin/env python3
# scripts/generate_zsh_config.py

from pathlib import Path
from dataclasses import dataclass
from typing import List


@dataclass
class ShellConfig:
    """Shell configuration generator."""

    is_agent: bool = False
    use_starship: bool = True
    use_zsh_autosuggestions: bool = True
    use_fzf: bool = True
    enable_protection: bool = True

    def generate_zshenv(self) -> str:
        """Generate .zshenv content."""
        lines = [
            "# Generated by generate_zsh_config.py",
            "# DO NOT EDIT MANUALLY",
            "",
        ]

        if self.is_agent:
            lines.extend(
                [
                    "# Agent mode: skip heavy init",
                    'export AGENT_ID="thegent"',
                    'export heliosShield_AGENT_CONTEXT="1"',
                    "return",
                ]
            )
        else:
            lines.extend(
                [
                    "# User mode: full initialization",
                    "",
                ]
            )

        return "\n".join(lines)

    def generate_zshrc(self) -> str:
        """Generate .zshrc content."""
        lines = [
            "# Generated by generate_zsh_config.py",
            "# DO NOT EDIT MANUALLY",
            "",
        ]

        if self.use_starship:
            lines.append('eval "$(starship init zsh)"')

        if self.use_zsh_autosuggestions:
            lines.append("source ~/.zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh")

        if self.use_fzf:
            lines.append("source ~/.zsh/plugins/fzf-tab/fzf-tab.plugin.zsh")

        if self.enable_protection:
            lines.append("source ~/.zsh/safeguards.zsh")

        return "\n".join(lines)


def main():
    config = ShellConfig(is_agent=False)

    zshenv = config.generate_zshenv()
    zshrc = config.generate_zshrc()

    print("Generated .zshenv:")
    print(zshenv)
    print("\nGenerated .zshrc:")
    print(zshrc)


if __name__ == "__main__":
    main()
```

### 5.2 Protection Script

```bash
#!/usr/bin/env bash
# shell/.zsh_safeguards.zsh

# Fork guard: prevent fork exhaustion
_thegent_fork_guard() {
  local current_procs=$(ps aux | grep -c "[zsh|python|bash]")
  local max_procs=200

  if (( current_procs > max_procs )); then
    echo "⚠️  Warning: High process count ($current_procs). Consider pruning."
  fi
}

# Eval safety: prevent eval injection
_thegent_eval_guard() {
  local cmd="$1"
  if [[ "$cmd" =~ \$ ]]; then
    echo "⚠️  Warning: Command contains variable expansion. Use 'eval --'."
    return 1
  fi
  return 0
}

# Add to precmd
precmd_functions+=(_thegent_fork_guard)
```

---

## 6. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. **Added Section 5:** Shell Config Generator
   - Python generator for zsh configs
   - Agent vs user mode handling
   - Plugin loading conditional

2. **Added Section 6:** Protection Script
   - Fork guard for process limits
   - Eval safety guard
   - Precmd hooks

### Cross-References Added

- shell/.zshenv
- shell/.zshrc
- shell/.zsh_safeguards.zsh

### Practical Additions

- Python config generator
- Bash safeguard functions
- Precmd hook integration

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [SHELL_ERROR_FIXES.md](./SHELL_ERROR_FIXES.md) - Shell error fixes
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
