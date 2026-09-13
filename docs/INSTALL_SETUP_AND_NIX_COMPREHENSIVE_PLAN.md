# Install/Setup & Nix Integration — Comprehensive Plan

**Date:** 2026-02-18  
**Scope:** Ensure thegent install/setup covers everything (user, system, full stack); Nix integration, config sharing, and optimization.  
**Status:** Plan draft (expanded).  
**Related:** [PATCHES_OPTIMIZATION_AUDIT_AND_PLAN.md](PATCHES_OPTIMIZATION_AUDIT_AND_PLAN.md), [SETUP_PROPOSED_ITEMS.md](../thegent/docs/plans/SETUP_PROPOSED_ITEMS.md), [AUTO_INSTALL_AUTO_SETUP](../thegent/docs/research/AUTO_INSTALL_AUTO_SETUP_IMPLEMENTATION_2026-02-18.md)

---

## 1. Executive Summary

**Goal:** A single `thegent setup` (or `thegent install -t all`) that covers absolutely everything — user home, shell, agents, shims, system-level git, LSP/IDE auto-setup, lock-cleanup, and optional Nix/home-manager integration.

**Nix angle:** Nix users share configs via **home-manager** (dotfiles, packages), **flakes** (reproducible dev shells), **nix-direnv** (`use flake`), and **nix-darwin** (macOS system config). thegent should both **work inside** Nix (flake.nix dev shell) and **optionally provide** home-manager modules / flake outputs so Nix users can declaratively include thegent in their configs.

**Philosophy (from AUTO_INSTALL):** Instructions as last resort; auto-install, auto-configure, auto-detect everything possible.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Install/Setup Taxonomy](#2-installsetup-taxonomy--what-exists-today)
3. [Full System Setup](#3-full-system-setup--definition)
4. [Nix — Config Sharing](#4-nix--how-people-typically-share-configs)
5. [thegent + Nix Optimization](#5-how-thegent-enhancesextendoptimizes-nix)
6. [Implementation Plan](#6-implementation-plan)
7. [Quick Reference](#7-quick-reference-install-commands)
8. [Nix User Workflows](#8-nix-user-workflows)
9. [File Reference](#9-file-reference)
10. [Current Wizard Flow](#10-current-thegent-setup-flow-wizard)
11. [MCP & Provider Setup](#11-mcp--provider-setup-complementary)
12. [New Discoveries](#12-new-discoveries-summary)
13. [Research References](#13-research-references-ddgweb)
14. [Success Criteria](#14-success-criteria)

---

## 2. Install/Setup Taxonomy — What Exists Today

### 2.1 User-Level (Home Directory)

| Target             | What It Does                             | Status |
| ------------------ | ---------------------------------------- | ------ |
| **claude-code**    | ~/.claude/ (skills, hooks, agents)       | ✅     |
| **claude-desktop** | Library/Application Support/Claude (MCP) | ✅     |
| **cursor**         | ~/.cursor/ (skills-cursor)               | ✅     |
| **codex**          | ~/.codex/ (MCP)                          | ✅     |
| **droid**          | ~/.factory/ (hooks, skills, config)      | ✅     |
| **envrc**          | ~/.envrc (direnv, guarded use flake)     | ✅     |
| **shell**          | ~/.zshenv, .zshrc, .zsh_bundle.zsh, etc. | ✅     |

### 2.2 User-Level Shims (~/.local/bin)

| Command                    | What It Does                                              | Status         |
| -------------------------- | --------------------------------------------------------- | -------------- |
| **install-shims**          | git, grep→rg, find→fd, jq→jaq, uv, npm, role accelerators | ✅             |
| **install-shims --system** | git wrapper to /usr/local/bin (nix/direnv)                | ✅ (auto-sudo) |

### 2.3 System-Level (Planned / Partial)

| Target                     | What It Does                                              | Status      |
| -------------------------- | --------------------------------------------------------- | ----------- |
| **install-shims --system** | Git wrapper for nix/direnv/agents                         | ✅          |
| **install -t system**      | /opt/thegent or /usr/local/thegent (agent-as-system-user) | 🔲 Planned  |
| **git lock-cleanup**       | Stale index.lock removal + launchd/systemd                | 🔲 Phase 3  |
| **MCP launchd service**    | Background MCP for agents                                 | ✅ (wizard) |

### 2.4 Auto-Install / Auto-Setup (LSP, IDE)

| Component                  | What It Does                                                                              | Status |
| -------------------------- | ----------------------------------------------------------------------------------------- | ------ |
| **LSP auto-install**       | Auto-install pyright, typescript-language-server, rust-analyzer, gopls, etc. when missing | ✅     |
| **IDE auto-setup**         | Auto-detect JetBrains, Serena plugin, Ghostty shell integration                           | ✅     |
| **Auto-init on MCP start** | Runs auto-setup when `thegent serve` starts                                               | ✅     |
| **thegent lsp auto-setup** | CLI to run all IDE/LSP setup                                                              | ✅     |

### 2.5 Bootstrap Methods (First-Time Install)

| Method              | Command                                                    | Platform                                |
| ------------------- | ---------------------------------------------------------- | --------------------------------------- |
| **pip**             | `pip install thegent`                                      | All                                     |
| **Homebrew**        | `brew install thegent`                                     | macOS                                   |
| **Nix profile**     | `nix profile install github:router-for-me/thegent`         | Nix                                     |
| **winget**          | `winget install router-for-me.thegent`                     | Windows                                 |
| **apt/yum**         | `apt install thegent` / `yum install thegent`              | Linux                                   |
| **curl \| sh**      | (Not implemented)                                          | —                                       |
| **nix run**         | `nix run github:router-for-me/thegent`                     | Nix (ephemeral)                         |
| **Determinate Nix** | `curl -fsSL https://install.determinate.systems/nix \| sh` | Nix (7M+ installs; flakes enabled)      |
| **pipx**            | `pipx install thegent`                                     | Isolated Python app (no venv pollution) |
| **uv**              | `uv tool install thegent` or `uvx thegent`                 | Fast; thegent flake uses uv             |

### 2.6 Shim Variants (Discovery)

| Shim System                  | Location                             | Purpose                                                               |
| ---------------------------- | ------------------------------------ | --------------------------------------------------------------------- |
| **install-shims** (Python)   | main.py `_install_tool_accelerators` | git, grep→rg, find→fd, jq→jaq, uv, npm, role accelerators             |
| **install-thegent-shims.sh** | scripts/                             | Rust `thegent-shims` binary; thegent-git, thegent-grep, thegent-agent |
| **runtime-dispatch**         | crates/thegent-runtime/install.sh    | Symlinks git, grep, find, ls, du, cat, node, npm, npx, python, pip    |

**Note:** Python `install-shims` is the primary path. Rust scripts may be legacy or alternate builds.

### 2.7 Gaps (Not in Install Today)

| Gap                             | Description                                                                    |
| ------------------------------- | ------------------------------------------------------------------------------ | --- |
| **Full system install**         | No `thegent install -t system` for /opt/thegent layout                         |
| **Lock-cleanup daemon**         | No `thegent git lock-cleanup` or timer                                         |
| **Nix/home-manager module**     | No declarative Nix module for thegent                                          |
| **Single-command full setup**   | `install -t all` covers user targets but not shims, system git, lock-cleanup   |
| **Bootstrap curl \| sh**        | No one-liner for first-time install                                            |
| **setup --hooks**               | No `thegent setup --hooks` for pre-commit/husky/thegent hooks (SETUP_PROPOSED) |
| **setup --skills**              | No `thegent setup --skills` to sync skills template (SETUP_PROPOSED)           |
| **devcontainer**                | No .devcontainer/ for Codespaces/VS Code                                       | —   |
| **pipx/uv in INSTALLATION**     | Not documented                                                                 | —   |
| **chezmoi/dotfile integration** | No templates for dotfile managers                                              | —   |

### 2.8 Dotfile Managers (Non-Nix Alternative)

Users who don't use Nix often use dotfile managers. thegent install targets overlap with what these manage:

| Tool             | Stars | Key Features                                       | Overlap with thegent          |
| ---------------- | ----- | -------------------------------------------------- | ----------------------------- |
| **chezmoi**      | 18k   | Single binary, templates, private files, 1Password | ~/.zshrc, ~/.envrc, ~/.claude |
| **yadm**         | 6k    | Git-based, encryption, alternate files             | Same                          |
| **Home Manager** | 9k    | Nix; declarative                                   | Full overlap (Nix path)       |
| **dotbot**       | 7.8k  | Lightweight, symlinks                              | Same                          |
| **dotter**       | 1.9k  | Rust, templating                                   | Same                          |

**Implication:** thegent could provide chezmoi templates or document how to add thegent config to existing dotfile repos. See [dotfiles.github.io/utilities](https://dotfiles.github.io/utilities/).

---

## 3. Full System Setup — Definition

**Full system setup** means:

1. **User home:** All user targets (claude, cursor, codex, droid, envrc, shell).
2. **User shims:** `~/.local/bin` with git, rg, fd, jaq, etc.
3. **System git:** `install-shims --system` so nix/direnv/agents use lock-aware git.
4. **Lock-cleanup:** `thegent git lock-cleanup` + launchd/systemd timer.
5. **MCP service:** launchd (macOS) or systemd (Linux) for background MCP.
6. **Optional system install:** `/opt/thegent` for agent-as-system-user (CI, shared agents).

**Single command:** `thegent setup` or `thegent install --full` that runs all of the above, prompting for sudo when needed.

---

## 4. Nix — How People Typically Share Configs

### 4.1 Patterns

| Pattern                 | Tool                | Purpose                                    |
| ----------------------- | ------------------- | ------------------------------------------ |
| **User env + dotfiles** | home-manager        | Declarative ~/.config, ~/.zshrc, packages  |
| **Dev shells**          | flakes + direnv     | `nix develop` or `use flake` per project   |
| **nix-direnv**          | nix-direnv          | Caches `use flake`; fast `cd` into project |
| **macOS system**        | nix-darwin          | Declarative system config (launchd, etc.)  |
| **NixOS**               | NixOS config        | Full OS + home-manager module              |
| **nix profile**         | nix profile install | Imperative user env; `~/.nix-profile`      |

### 4.2 nix-direnv (Critical for Flakes)

- **What:** direnv extension that caches `use flake` / `nix shell` so repeated `cd` is fast.
- **Install:** `nix profile install nixpkgs#nix-direnv` or home-manager `programs.direnv.nix-direnv.enable`.
- **.envrc:** `use flake` (or `use nix`) — loads flake dev shell when entering directory.
- **thegent envrc:** Guards `use flake` (only when `flake.nix` exists); avoids FUNCNEST in home.
- **direnv-instant:** Optional daemon for async direnv; combined with nix-direnv gives near-instant shell on `cd`.

### 4.3 home-manager

- **What:** Manages user environment: packages, dotfiles, services.
- **Config:** `~/.config/home-manager/home.nix` or flake-based.
- **Commands:** `home-manager switch`, `home-manager build`.
- **Dotfiles:** `home.file."path"`, `xdg.configFile`, `programs.zsh`, etc.
- **Flake:** `homeManagerConfigurations` or `home-manager` as flake module.

### 4.4 Flakes (Project-Level)

- **What:** Reproducible dev environments per project.
- **Config:** `flake.nix` in project root.
- **Outputs:** `devShells`, `packages`, `overlays`, `homeManagerModules`, `nixosModules`.
- **thegent flake:** `devShells.default` — Python, uv, node, rg, fd, jaq, git, tmux.

### 4.5 nix profile vs nix develop

| Command               | Scope                     | Persistence              |
| --------------------- | ------------------------- | ------------------------ |
| `nix profile install` | User env (~/.nix-profile) | Persistent across shells |
| `nix develop`         | Project shell             | Only in that shell       |
| `use flake` (direnv)  | Project dir               | Auto-loads on `cd`       |

### 4.6 nix-darwin (macOS)

- **What:** Declarative macOS system config (like NixOS for Mac).
- **Config:** `~/.nixpkgs/darwin-configuration.nix` or flake.
- **Manages:** launchd, system packages, defaults.

### 4.7 Config Sharing (Typical)

| Approach               | How                                                             | Use Case          |
| ---------------------- | --------------------------------------------------------------- | ----------------- |
| **Dotfiles repo**      | Git repo with .zshrc, .config etc.; symlink or copy             | Non-Nix           |
| **home-manager flake** | Flake with home-manager config; `home-manager switch --flake .` | Nix users         |
| **Dev shell flake**    | `flake.nix` per project; `use flake` in .envrc                  | Per-project tools |
| **nix-darwin flake**   | Flake with darwin config; `darwin-rebuild switch --flake .`     | macOS system      |

### 4.8 devenv (Alternative to Raw Flakes)

- **What:** Declarative dev environments; JSON-like `devenv.nix`; faster than raw flakes (caching).
- **Features:** packages, languages, processes (process-compose), services, git-hooks, tasks, profiles.
- **direnv:** Auto-activates on `cd` via direnv.
- **Claude Code:** Native `claude.code` module; mcps.nix provides MCP presets.
- **URL:** [devenv.sh](https://devenv.sh)

### 4.9 FlakeHub & Registries

- **FlakeHub:** [flakehub.com](https://flakehub.com) — discover and publish flakes (Determinate Systems).
- **Registry:** `nixpkgs`, `home-manager`, `flake-utils` are symbolic IDs in default registry.
- **Reference:** `github:org/repo`, `path:/path`, `nixpkgs/release-22.11`.

### 4.10 home-manager programs.claude-code (Precedent)

home-manager has native `programs.claude-code` with:

- `settings`, `agents`, `commands`, `hooks`, `memory`, `rules`, `skills`
- `mcpServers`, `enableMcpIntegration` (merge with `programs.mcp.servers`)
- `rulesDir`, `agentsDir`, `commandsDir`, `hooksDir`, `skillsDir`
- Writes to `~/.claude/` declaratively

**Implication:** thegent home-manager module can follow this pattern; or extend claude-code for thegent-specific config.

---

## 5. How thegent Enhances/Extends/Optimizes Nix

### 5.1 Work Inside Nix (Already)

- **thegent flake.nix:** Dev shell with Python, uv, node, rg, fd, jaq, git.
- **envrc.home.template:** Guards `use flake` (only when flake.nix exists); avoids FUNCNEST in home.
- **install-shims --system:** Ensures nix/direnv use lock-aware git.

### 5.2 Provide home-manager Module (New)

**Precedent:** [mcps.nix](https://github.com/roman/mcps.nix) — MCP presets for home-manager + devenv; integrates with `programs.claude-code`. [home-manager programs.claude-code](https://github.com/nix-community/home-manager/blob/master/modules/programs/claude-code.nix) — native module for settings, agents, commands, hooks, skills, mcpServers.

**Idea:** thegent can ship a Nix module that home-manager users can import.

```nix
# home.nix
{
  imports = [
    (fetchTarball "https://github.com/.../thegent/archive/main.tar.gz" + "/nix/home-manager.nix")
  ];
  programs.thegent = {
    enable = true;
    installTargets = [ "all" ];  # or ["shell" "envrc" "cursor" ...]
    installShims = true;
    installShimsSystem = true;   # requires sudo
  };
}
```

**Alternative:** Extend `programs.claude-code` with thegent-specific config (skills, hooks from thegent) rather than separate module.

**Effect:** `home-manager switch` installs thegent config (shell, envrc, etc.) declaratively. No manual `thegent install`.

### 5.3 Flake Outputs (New)

**Idea:** thegent flake can expose:

- `packages.${system}.thegent` — thegent CLI
- `overlays.default` — overlay for thegent
- `homeManagerModules.thegent` — home-manager module
- `nixosModules.thegent` — NixOS module (if ever needed)

**Effect:** Nix users add thegent as a flake input and get reproducible thegent in their config.

### 5.4 nix-darwin Integration (New)

**Idea:** thegent nix-darwin module for:

- launchd service (MCP)
- git lock-cleanup timer
- PATH with thegent bin

**Effect:** `darwin-rebuild switch` sets up thegent system services.

### 5.5 Optimize Existing Nix Setups

| Optimization          | How                                                       |
| --------------------- | --------------------------------------------------------- |
| **Avoid direnv hang** | envrc template with flake guard, non-interactive skip     |
| **Git lock for nix**  | install-shims --system                                    |
| **Stale locks**       | lock-cleanup daemon (works regardless of Nix)             |
| **Shell startup**     | thegent shell config (lazy compinit, FUNCNEST guard)      |
| **Shared hooks**      | thegent hooks in ~/.claude, discoverable by Nix dev shell |

### 5.6 Nix User Checklist (Concrete Steps)

| Step | Action                                  | Why                           |
| ---- | --------------------------------------- | ----------------------------- |
| 1    | Install nix-direnv                      | Fast `use flake` on `cd`      |
| 2    | Add `use flake` to project .envrc       | Auto-load thegent dev shell   |
| 3    | `thegent install -t envrc` for ~/.envrc | Guarded; no FUNCNEST in home  |
| 4    | `thegent install-shims --system`        | Nix/direnv use lock-aware git |
| 5    | (Future) home-manager module            | Declarative thegent in config |
| 6    | (Future) lock-cleanup daemon            | Remove stale index.lock       |

---

## 6. Implementation Plan

### Phase A: Unify Install into "Full Setup" (1–2 weeks) ✅ Done

- [x] Add `thegent setup --full` that runs:
  - `install -t all` (user targets)
  - `install-shims` (user shims)
  - `install-shims --system` (system git, auto-sudo)
  - `thegent git lock-cleanup service install` + start
  - MCP service (if macOS, prompts)
- [ ] Document in INSTALLATION.md as the "one command" for new users.

### Phase B: Git Lock-Cleanup (1–2 weeks) ✅ Done

- [x] Implement `thegent git lock-cleanup` (git_lock_manage.py)
- [x] Add `thegent git lock-cleanup service install|start|stop|status|uninstall` (launchd/systemd)
- [x] Preemptive cleanup in envrc template (before `use flake`)
- [x] Integrate into `thegent setup --full` (Phase A)

### Phase C: System Install Target (2–3 weeks) ✅ Done

- [x] Add `thegent install -t system` (or `--prefix /opt/thegent`)
- [x] Layout: bin, share/thegent/hooks, etc/thegent, var/lib/thegent
- [x] For agent-as-system-user deployment
- [ ] Document: run `install-shims --prefix <prefix>` after for git wrapper

### Phase D: Nix home-manager Module (2–3 weeks) ✅ Done

- [x] Create `nix/home-manager.nix`
- [x] Options: enable, installTargets, installShims, installShimsSystem, installLockCleanupService
- [x] Activation script runs `thegent install` with selected targets
- [x] Flake output: `homeManagerModules.thegent`
- [ ] Document: "For home-manager users, add this module"

### Phase E: Flake Outputs (1 week)

- [ ] Add `homeManagerModules.thegent` to flake outputs
- [ ] Optional: `packages.thegent` if we want nix to build thegent
- [ ] Publish to FlakeHub for discoverability
- [ ] Document in flake.nix and README

### Phase E2: devenv Module (Optional, 1 week)

- [ ] Add `devenvModules.thegent` (like mcps.nix) for projects using devenv
- [ ] Integrate with devenv's `claude.code` if applicable
- [ ] For teams that prefer devenv over raw flakes

### Phase F: nix-darwin Module (Optional, 1–2 weeks)

- [ ] Create nix-darwin module for MCP service, lock-cleanup timer
- [ ] For users who manage macOS via nix-darwin

### Phase G: setup --hooks, --skills (from SETUP_PROPOSED)

- [ ] `thegent setup --hooks` — Install pre-commit/husky or thegent hooks into .git/hooks
- [ ] `thegent setup --skills` — Sync skills template (ECC or custom) to project
- [ ] Document in SETUP_PROPOSED_ITEMS

### Phase H: Bootstrap curl | sh (Optional)

- [ ] Create `scripts/bootstrap.sh` or `get.thegent.io` one-liner
- [ ] Installs thegent + runs `thegent install -t all` + `thegent install-shims`
- [ ] Reference: [Determinate Nix Installer](https://github.com/DeterminateSystems/nix-installer) pattern — `curl -fsSL https://... | sh -s -- install`
- [ ] Fallback: `curl -sSL https://... | bash`

### Phase I: devcontainer (Optional)

- [ ] Add `.devcontainer/devcontainer.json` for GitHub Codespaces / VS Code Dev Containers
- [ ] Include thegent, uv, direnv, nix-direnv in container
- [ ] Reference: [containers.dev](https://containers.dev/implementors/json_reference/)

### Phase J: pipx/uv + Dotfile Integration (Optional)

- [ ] Document `pipx install thegent` and `uv tool install thegent` in INSTALLATION.md
- [ ] Provide chezmoi templates or dotfile-manager integration guide
- [ ] Reference: [dotfiles.github.io/utilities](https://dotfiles.github.io/utilities/)

---

## 7. Quick Reference: Install Commands

| Command                                      | Scope                                                                                    | Sudo?           |
| -------------------------------------------- | ---------------------------------------------------------------------------------------- | --------------- |
| `thegent install -t all`                     | User home (agents, shell, envrc)                                                         | No              |
| `thegent install -t shell`                   | Shell config only                                                                        | No              |
| `thegent install -t envrc`                   | ~/.envrc only                                                                            | No              |
| `thegent install-shims`                      | ~/.local/bin shims                                                                       | No              |
| `thegent install-shims --system`             | /usr/local/bin git wrapper                                                               | Yes (auto)      |
| `thegent install-shims --system --uninstall` | Restore original git                                                                     | Yes (auto)      |
| `thegent setup --full`                       | install -t all, install-shims, install-shims --system, lock-cleanup service, MCP (macOS) | Yes when needed |
| `thegent install -t system` (proposed)       | /opt/thegent                                                                             | Yes             |

---

## 8. Nix User Workflows

### 8.1 Non-Nix User

```
curl -sSL https://... | sh   # or: pip install thegent
thegent setup
```

### 8.2 Nix User (Flake Only)

```
cd my-project
nix develop   # or direnv use flake
thegent install -t all
thegent install-shims --system   # for nix/direnv git
```

### 8.3 Nix User (home-manager)

```
# flake.nix inputs
inputs.thegent.url = "github:router-for-me/thegent";  # or path:../thegent

# home.nix
{ inputs, ... }: {
  imports = [ inputs.thegent.homeManagerModules.thegent ];
  programs.thegent = {
    enable = true;
    installTargets = [ "claude-code" "cursor" "envrc" "shell" ];
    installShims = true;
    installShimsSystem = false;  # requires sudo
    installLockCleanupService = true;
  };
}

home-manager switch
```

### 8.4 Nix User (nix-darwin)

```
# darwin-configuration.nix
services.thegent.enable = true;   # MCP + lock-cleanup

darwin-rebuild switch
```

### 8.5 Nix User (devenv)

```
# devenv.nix
{ inputs, ... }: {
  imports = [ inputs.thegent.devenvModules.thegent ];
  claude.code.enable = true;   # if using devenv's claude module
  # or: thegent config for project
}
```

---

## 9. File Reference

| Purpose                  | Path                                                                        |
| ------------------------ | --------------------------------------------------------------------------- |
| Git lock-cleanup         | thegent/src/thegent/git_lock_manage.py                                      |
| Install logic            | thegent/src/thegent/install.py                                              |
| Flake                    | thegent/flake.nix                                                           |
| envrc template           | thegent/shell/envrc.home.template                                           |
| home-manager module      | thegent/nix/home-manager.nix                                                |
| PATCHES audit            | docs/PATCHES_OPTIMIZATION_AUDIT_AND_PLAN.md                                 |
| GIT index lock plan      | thegent/docs/research/GIT_INDEX_LOCK_OS_LEVEL_AND_AGENT_SYSTEM_USER_PLAN.md |
| INSTALLATION guide       | thegent/docs/guides/INSTALLATION.md                                         |
| SETUP_PROPOSED_ITEMS     | thegent/docs/plans/SETUP_PROPOSED_ITEMS.md                                  |
| AUTO_INSTALL_AUTO_SETUP  | thegent/docs/research/AUTO_INSTALL_AUTO_SETUP_IMPLEMENTATION_2026-02-18.md  |
| install-thegent-shims.sh | thegent/scripts/install-thegent-shims.sh                                    |
| runtime-dispatch install | thegent/crates/thegent-runtime/install.sh                                   |
| Starship + direnv        | thegent/docs/guides/STARSHIP_DIRENV_SETUP.md                                |
| HYBRID_ENV_SETUP         | thegent/docs/checklists/HYBRID_ENV_SETUP_CHECKLIST.md                       |

---

## 10. Current thegent setup Flow (Wizard)

```
thegent install -w   # Wizard
  → Select targets (1–7: cursor, claude-code, claude-desktop, codex, droid, envrc, shell)
  → Mode: smart | editable | force
  → Install launchd service? (macOS)
  → Proceed
  → run_install() for each target
```

**Wizard does NOT run:** install-shims, install-shims --system, lock-cleanup, provider login (cliproxy).

---

## 11. MCP & Provider Setup (Complementary)

| Command                             | Purpose                                      |
| ----------------------------------- | -------------------------------------------- |
| `thegent cliproxy login <provider>` | OAuth for Claude, OpenAI, etc.               |
| `thegent cliproxy ensure-config`    | Ensure cliproxy config exists                |
| `thegent mcp up`                    | Start MCP + proxy via process-compose        |
| `thegent install -w`                | Wizard includes MCP service (launchd) option |

**Gap:** `thegent setup` or `install -t all` does not auto-run cliproxy login; user must configure providers separately.

---

## 12. New Discoveries (Summary)

| Discovery                             | Source                                       | Action                                            |
| ------------------------------------- | -------------------------------------------- | ------------------------------------------------- |
| **AUTO_INSTALL_AUTO_SETUP**           | LSP, IDE, Serena, Ghostty                    | Already implemented; document in plan             |
| **SETUP_PROPOSED_ITEMS**              | Hooks, skills, MCP mounts, ECC               | Add setup --hooks, --skills phases                |
| **Shim variants**                     | install-thegent-shims.sh, runtime-dispatch   | Clarify Python install-shims is primary           |
| **nix-direnv**                        | use flake caching                            | Add to Nix section                                |
| **nix profile install**               | INSTALLATION.md                              | Add to bootstrap methods                          |
| **Starship + direnv**                 | Project-specific .starship.toml              | Optional envrc enhancement                        |
| **HYBRID_ENV_SETUP**                  | Cross-device (Mac/Windows)                   | Reference for multi-machine users                 |
| **mcps.nix**                          | MCP presets for home-manager + devenv        | Model for thegent home-manager module             |
| **devenv**                            | Declarative dev envs; claude.code, git-hooks | Alternative to raw flakes; consider devenv module |
| **Determinate Nix Installer**         | curl \| sh; 7M+ installs; flakes by default  | Reference for bootstrap pattern                   |
| **home-manager programs.claude-code** | Native module; settings, agents, mcpServers  | Precedent for thegent module design               |
| **FlakeHub**                          | flakehub.com — flake registry                | Publish thegent flake                             |
| **zero-to-nix**                       | Flake concepts, flake references             | Documentation reference                           |
| **pipx**                              | Isolated Python CLI install                  | Add to INSTALLATION; alternative to pip           |
| **uv**                                | Fast Python manager; uv tool install         | thegent flake uses uv; add to docs                |
| **devcontainer**                      | containers.dev; Codespaces                   | Phase I: .devcontainer/                           |
| **dotfile managers**                  | chezmoi 18k★, yadm, dotbot                   | Phase J: templates or integration guide           |
| **nix-direnv**                        | Caching use_flake; direnv-instant            | Recommend for Nix users; async loading            |
| **thegent nix**                       | GitHub search: 0 results                     | No existing Nix package; first-mover              |

---

## 13. Research References (DDG/Web)

| Topic                      | URL                                                                                                                            |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| Nix Flakes                 | [nixos.wiki/wiki/Flakes](https://nixos.wiki/wiki/Flakes)                                                                       |
| zero-to-nix Flakes         | [zero-to-nix.com/concepts/flakes](https://zero-to-nix.com/concepts/flakes)                                                     |
| Home Manager               | [github.com/nix-community/home-manager](https://github.com/nix-community/home-manager)                                         |
| home-manager claude-code   | [home-manager/.../claude-code.nix](https://github.com/nix-community/home-manager/blob/master/modules/programs/claude-code.nix) |
| mcps.nix                   | [github.com/roman/mcps.nix](https://github.com/roman/mcps.nix)                                                                 |
| devenv                     | [devenv.sh](https://devenv.sh)                                                                                                 |
| Determinate Nix Installer  | [github.com/DeterminateSystems/nix-installer](https://github.com/DeterminateSystems/nix-installer)                             |
| FlakeHub                   | [flakehub.com](https://flakehub.com)                                                                                           |
| nix-community impermanence | [github.com/nix-community/impermanence](https://github.com/nix-community/impermanence)                                         |
| nix-darwin                 | [github.com/LnL7/nix-darwin](https://github.com/LnL7/nix-darwin)                                                               |
| pipx                       | [pypa.github.io/pipx](https://pypa.github.io/pipx/)                                                                            |
| uv                         | [docs.astral.sh/uv](https://docs.astral.sh/uv/)                                                                                |
| devcontainer spec          | [containers.dev/implementors/json_reference](https://containers.dev/implementors/json_reference/)                              |
| dotfile utilities          | [dotfiles.github.io/utilities](https://dotfiles.github.io/utilities/)                                                          |
| chezmoi                    | [github.com/twpayne/chezmoi](https://github.com/twpayne/chezmoi)                                                               |
| nix-direnv                 | [github.com/nix-community/nix-direnv](https://github.com/nix-community/nix-direnv)                                             |
| direnv-instant             | [github.com/Mic92/direnv-instant](https://github.com/Mic92/direnv-instant) — async direnv with nix-direnv                      |

---

## 14. Success Criteria

1. **New user:** `thegent setup` (or equivalent) configures everything.
2. **Nix user:** Can use thegent via flake dev shell + optional home-manager module.
3. **System admin:** Can deploy thegent for agent-as-system-user via `install -t system`.
4. **Config sharing:** Nix users can declaratively include thegent in home-manager/nix-darwin.
5. **No manual steps:** Sudo is requested automatically when needed.
6. **Auto-install:** LSP, IDE, Serena, Ghostty auto-configure; instructions only as last resort.
7. **Bootstrap:** One command (pip/brew/nix) + `thegent setup` = full environment.
