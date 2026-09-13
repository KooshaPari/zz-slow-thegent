# Patches & Optimization Audit and Plan

**Date:** 2026-02-18  
**Scope:** Identify patches, shell config, and install targets that should be optimized and integrated into `thegent install` (same pattern as `envrc`).  
**Status:** Audit complete, all phases done. See [PATCHES_OPTIMIZATION_INDEX.md](./PATCHES_OPTIMIZATION_INDEX.md) for quick reference.

---

## 1. Executive Summary

**Pattern established:** `thegent install -t envrc` installs guarded `~/.envrc` from `shell/envrc.home.template`, ensuring $HOME is set up correctly. This document audits other areas that should follow the same pattern: templates in thegent → install target → user/system-wide setup.

**Key findings:**

- **Shell config** — now in `thegent install -t shell` ✅
- **install-shims --system** (git wrapper for nix/direnv) — implemented ✅
- **Git lock-cleanup daemon** is **planned** but not implemented.
- **CLIProxyAPIPlus patch** (cursor-minimax) is applied to fork; not thegent-installable.
- Several **optimization docs** exist but fixes are scattered; no single install path.

---

## 2. Audit: What `thegent install` Covers Today

| Target         | Installs To                        | Source                      | Status   |
| -------------- | ---------------------------------- | --------------------------- | -------- |
| claude-code    | ~/.claude/                         | skills, hooks, agents, etc. | ✅       |
| claude-desktop | Library/Application Support/Claude | MCP config                  | ✅       |
| cursor         | ~/.cursor/                         | skills-cursor               | ✅       |
| codex          | ~/.codex/                          | MCP config                  | ✅       |
| droid          | ~/.factory/                        | hooks, skills, config       | ✅       |
| **envrc**      | ~/.envrc                           | shell/envrc.home.template   | ✅ (new) |

**Also in install:**

- envrc, shell, git-lock-cleanup (see §9 Quick Reference)

---

## 3. Patches & Configs to Optimize

### 3.1 Shell Config (High Priority)

**Current:** Shell files live in `thegent/shell/`. Users must manually:

- Copy/symlink to ~/
- Or source from project path via ZDOTDIR / custom wiring

**Gap:** No `thegent install -t shell` to set up home shell config.

**Proposed:** Add `shell` target:

| File                  | Source                      | Target                  | Mode                                  |
| --------------------- | --------------------------- | ----------------------- | ------------------------------------- |
| .zshenv               | shell/.zshenv               | ~/.zshenv               | smart                                 |
| .zsh_bundle.zsh       | shell/.zsh_bundle.zsh       | ~/.zsh_bundle.zsh       | smart                                 |
| .zsh_safeguards.zsh   | shell/.zsh_safeguards.zsh   | ~/.zsh_safeguards.zsh   | smart                                 |
| .zsh_optimization.zsh | shell/.zsh_optimization.zsh | ~/.zsh_optimization.zsh | smart                                 |
| .zsh_advanced.zsh     | shell/.zsh_advanced.zsh     | ~/.zsh_advanced.zsh     | smart                                 |
| .zshrc                | shell/.zshrc                | ~/.zshrc                | smart                                 |
| zshrc.local.template  | shell/zshrc.local.template  | ~/.zshrc.local          | **never overwrite** (only if missing) |

**Guards:** Shell config has FUNCNEST, non-interactive skips, direnv guards. Installing ensures users get the optimized, guarded versions.

**Effort:** 1–2 days. Add `shell` to VALID_TARGETS, install loop, wizard.

---

### 3.2 install-shims --system (Medium Priority)

**Current:** `thegent install-shims` installs to `~/.local/bin`. Git shim, grep→rg, etc. Nix and direnv invoke git from system PATH (`/usr/bin`, `/opt/homebrew/bin`), bypassing thegent shim.

**Gap:** `install-shims --system` (or `--prefix /usr/local`) is planned in GIT_INDEX_LOCK_OS_LEVEL_AND_AGENT_SYSTEM_USER_PLAN.md but not implemented.

**Proposed:**

- Add `--system` / `--prefix` to `install-shims`
- Install git wrapper to `/usr/local/bin` (or configurable)
- Requires admin/root; document clearly

**Effort:** 2–3 days. Wrapper logic exists; need install path, backup of real git.

---

### 3.3 Git Lock-Cleanup Daemon (Medium Priority)

**Current:** Stale `.git/index.lock` blocks nix, direnv. Manual fix: `rm -f .git/index.lock`.

**Gap:** `thegent git lock-cleanup` + launchd/systemd timer is planned but not implemented.

**Proposed:**

- Add `thegent git lock-cleanup` command
- Scan common repo paths; remove locks older than 60s
- Install as launchd LaunchAgent via `thegent install -t service` or new `prune service install`

**Effort:** 1–2 days.

---

### 3.4 envrc (Done)

**Status:** ✅ Implemented. `thegent install -t envrc` installs guarded ~/.envrc. Included in `thegent install -t all`.

---

### 3.5 CLIProxyAPIPlus cursor-minimax Patch (External)

**Current:** `CLIProxyAPIPlus-fork/patches/cursor-minimax-channels.patch` adds Cursor and MiniMax to config.example.yaml and model_definitions.go.

**Gap:** Patch must be applied to fork manually. Not thegent-installable (fork is separate repo).

**Proposed:** Document in install flow: "For CLIProxyAPIPlus fork, apply patches from fork/patches/." Optional: `thegent cliproxy ensure-fork` could check patch status.

**Effort:** Documentation only; or small script to verify patch applied.

---

### 3.6 zshrc.local — Never Overwrite

**Current:** `zshrc.local.template` exists. Users copy manually. thegent should never overwrite ~/.zshrc.local (user customizations).

**Proposed:** When installing `shell` target, copy template to ~/.zshrc.local **only if file does not exist**. If exists, skip (or offer `--force` with backup).

---

## 4. Optimization Docs Cross-Reference

| Doc                                                | Key Content                                | Install Integration                 |
| -------------------------------------------------- | ------------------------------------------ | ----------------------------------- |
| SHELL_CONFIG_AUDIT_AND_CONSOLIDATION_PLAN          | Canonical configs, remove .zshrc.optimized | Add shell target                    |
| SHELL_STARTUP_OPTIMIZATION_IMMEDIATE_FIXES         | Lazy loading, compinit, direnv fix         | envrc done; shell target for rest   |
| DIRENV_HANG_FORK_GUARD_FIX                         | DIRENV_IN_ENVRC, fork guard skip           | In envrc template                   |
| GIT_INDEX_LOCK_OS_LEVEL_AND_AGENT_SYSTEM_USER_PLAN | install-shims --system, lock-cleanup       | Implement both                      |
| TOOLING_AND_GLOBAL_OPTIMIZATIONS_AUDIT (sharecli)  | PERF-001/002/003, QUAL-001                 | Separate project                    |
| SHELL_OPTIMIZATION_PLAN                            | zsh > bash, hooks use zsh                  | Hooks in ~/.claude (install target) |

---

## 5. Implementation Plan

### Phase 1: Shell Target (1–2 weeks) ✅ Done

- [x] Add `shell` to VALID_TARGETS
- [x] Add install logic for .zshenv, .zsh_bundle.zsh, .zsh_safeguards.zsh, .zsh_optimization.zsh, .zsh_advanced.zsh, .zshrc
- [x] zshrc.local: copy only if missing
- [x] Add to `thegent install -t all`
- [x] Add to wizard (option 7)
- [x] Document in SHELL_CONFIG_AUDIT (see §3.1, §9)

### Phase 2: install-shims --system (2–3 weeks) ✅ Done

- [x] Add `--system` / `--prefix` to install-shims
- [x] Implement git wrapper install to /usr/local/bin (or --prefix/bin)
- [x] Backup real git to git.bin
- [x] Document admin requirements (sudo, PATH)
- [x] Add --uninstall to restore original git

### Phase 3: Git Lock-Cleanup (1–2 weeks) ✅ Done

- [x] Add `thegent git lock-cleanup` command
- [x] Implement scan + remove stale locks
- [x] Integrate with launchd (reuse service plumbing)
- [x] Document in GIT_INDEX_LOCK plan

### Phase 4: Documentation & Verification ✅ Done

- [x] Update ZSH_HANG_DROID_FIX with full install flow
- [x] Create PATCHES_OPTIMIZATION_INDEX.md (single entry point)
- [x] Document `thegent install -t all` flow for new users

---

## 6. Success Criteria

1. **New user runs `thegent install -t all`** → gets envrc + (Phase 1) shell config in home.
2. **Shell startup** → no FUNCNEST, no direnv hang, <100ms target.
3. **Power user** → can run `thegent install-shims --system` for nix/direnv git lock handling.
4. **Stale locks** → `thegent git lock-cleanup` or daemon removes them automatically.

---

## 7. File Reference

| Purpose                     | Path                                                                                                  |
| --------------------------- | ----------------------------------------------------------------------------------------------------- |
| **Full install + Nix plan** | docs/INSTALL_SETUP_AND_NIX_COMPREHENSIVE_PLAN.md — bootstrap, Nix, auto-install, setup --hooks/skills |
| envrc template              | thegent/shell/envrc.home.template                                                                     |
| Shell configs               | thegent/shell/\*.zsh                                                                                  |
| Install logic               | thegent/src/thegent/install.py                                                                        |
| GIT index lock plan         | thegent/docs/research/GIT_INDEX_LOCK_OS_LEVEL_AND_AGENT_SYSTEM_USER_PLAN.md                           |
| Shell audit                 | thegent/docs/research/SHELL_CONFIG_AUDIT_AND_CONSOLIDATION_PLAN.md                                    |
| CLIProxy patch              | CLIProxyAPIPlus-fork/patches/cursor-minimax-channels.patch                                            |

---

## 8. Risks & Mitigations

| Risk                                       | Mitigation                                               |
| ------------------------------------------ | -------------------------------------------------------- |
| Overwriting user shell config              | Use SMART mode; zshrc.local never overwrite              |
| install-shims --system requires root       | Document clearly; optional for power users               |
| Shell target conflicts with existing setup | Check for existing files; interactive mode for conflicts |

---

## 9. Quick Reference: Patches & Configs

| Item                      | Type        | Install Target                               | Status    |
| ------------------------- | ----------- | -------------------------------------------- | --------- |
| ~/.envrc                  | Template    | `thegent install -t envrc`                   | ✅ Done   |
| ~/.zshenv                 | Shell       | `thegent install -t shell`                   | ✅ Done   |
| ~/.zsh_bundle.zsh         | Shell       | `thegent install -t shell`                   | ✅ Done   |
| ~/.zsh_safeguards.zsh     | Shell       | `thegent install -t shell`                   | ✅ Done   |
| ~/.zsh_optimization.zsh   | Shell       | `thegent install -t shell`                   | ✅ Done   |
| ~/.zsh_advanced.zsh       | Shell       | `thegent install -t shell`                   | ✅ Done   |
| ~/.zshrc                  | Shell       | `thegent install -t shell`                   | ✅ Done   |
| ~/.zshrc.local            | Template    | `thegent install -t shell` (copy if missing) | ✅ Done   |
| ~/.local/bin/git          | Shim        | `install-shims`                              | ✅ Exists |
| /usr/local/bin/git        | System shim | `install-shims --system`                     | ✅ Done   |
| lock-cleanup daemon       | Service     | `thegent install -t git-lock-cleanup`        | ✅ Done   |
| cursor-minimax (CLIProxy) | Patch       | Manual (fork)                                | External  |
