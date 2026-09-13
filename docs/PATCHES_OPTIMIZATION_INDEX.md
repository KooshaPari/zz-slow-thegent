# Patches & Optimization Index

**Single entry point** for install targets, patches, and optimization docs.

---

## Quick Start: New User Setup

```bash
# Full setup (envrc, shell, git-lock-cleanup, claude/cursor/droid, etc.)
thegent install -t all

# Or step-by-step:
thegent install -t envrc    # Guarded ~/.envrc (prevents direnv/FUNCNEST recursion)
thegent install -t shell    # Optimized zsh config to ~
thegent install-shims       # Tool accelerators to ~/.local/bin
thegent install-shims --system  # (Optional) Git wrapper to /usr/local for nix/direnv
```

---

## Install Targets

| Target           | Command                               | What It Does                                                              |
| ---------------- | ------------------------------------- | ------------------------------------------------------------------------- |
| envrc            | `thegent install -t envrc`            | Guarded ~/.envrc (flake only when flake.nix exists)                       |
| shell            | `thegent install -t shell`            | .zshenv, .zsh_bundle.zsh, .zsh_safeguards.zsh, .zshrc, etc.               |
| harness          | `thegent install -t harness`          | Claude Code, Codex, Droid, Cursor config + ensure-config + provider login |
| git-lock-cleanup | `thegent install -t git-lock-cleanup` | LaunchAgent to remove stale .git/index.lock                               |
| claude-code      | `thegent install -t claude-code`      | ~/.claude skills, hooks, MCP                                              |
| cursor           | `thegent install -t cursor`           | ~/.cursor skills                                                          |
| droid            | `thegent install -t droid`            | ~/.factory config                                                         |
| all              | `thegent install -t all`              | All of the above                                                          |

---

## Key Docs

| Doc                                                                                | Purpose                                 |
| ---------------------------------------------------------------------------------- | --------------------------------------- |
| [PATCHES_OPTIMIZATION_AUDIT_AND_PLAN.md](./PATCHES_OPTIMIZATION_AUDIT_AND_PLAN.md) | Full audit, phases, quick reference     |
| [ZSH_HANG_DROID_FIX.md](./ZSH_HANG_DROID_FIX.md)                                   | direnv hang, FUNCNEST, emergency bypass |
| [LLM_PROXY_RESEARCH_AUDIT_PLAN.md](./LLM_PROXY_RESEARCH_AUDIT_PLAN.md)             | CLIProxy, LiteLLM, provider primitive   |

---

## External Patches (Manual)

| Patch          | Location                      | Apply                                                        |
| -------------- | ----------------------------- | ------------------------------------------------------------ |
| cursor-minimax | CLIProxyAPIPlus-fork/patches/ | `cd fork && git apply patches/cursor-minimax-channels.patch` |
