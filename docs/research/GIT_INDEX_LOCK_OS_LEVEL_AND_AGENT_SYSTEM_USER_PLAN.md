<DONE>
# Git index.lock, OS-Level Universalization, and Agent System User Plan

**Date:** 2026-02-18 (expanded 2026-02-18)
**Status:** Research Complete, Plan Ready
**Extends:** GIT_TOOLING_AUDIT_AND_PLAN.md, DIRENV_FIX_2026-02-18.md, AGENT_OS_PRINCIPALS_DEPTH.md, CROSS_PLATFORM_MULTI_TENANT_QUICK_REFERENCE.md
**Implementation WBS:** [GIT_INDEX_LOCK_MULTITENANCY_IMPLEMENTATION_WBS.md](../plans/GIT_INDEX_LOCK_MULTITENANCY_IMPLEMENTATION_WBS.md)

---

## Executive Summary

**Problem:** Stale `.git/index.lock` blocks Nix, direnv, and other tools that invoke `git` directly. The thegent multitenant git logic (MTSP-09) only runs when `git` is invoked through the thegent shim in `~/.local/bin`. Most system and tool invocations use `/usr/bin/git` or `/opt/homebrew/bin/git` and bypass our logic.

**Goal:** Universalize git multitenant behavior to OS level so all git invocations (nix, direnv, agents, system services) benefit. Integrate with agent-as-system-user deployment where hooks must live and run for managed agent processes.

**Architectural principle — true multi-tenancy:** Worktrees will eventually be used for isolation when needed, but the primary value is **agent teams in one git repo**. Multiple agents (and humans) must coexist in the same repository, sharing the same index and staging area. True multi-tenancy = lock coordination, wait/steal, read-path bypass — not structural isolation. Worktrees are complementary (escape hatch for heavy parallel work); the core design serves shared-repo multi-tenant coordination.

---

## 1. Current State

### 1.1 What Works Today

| Invocation Path                              | Uses MTSP-09? | index.lock Handling      |
| -------------------------------------------- | ------------- | ------------------------ |
| User shell with `~/.local/bin` first in PATH | ✅ Yes        | Wait + steal stale lock  |
| thegent hooks (via dispatcher)               | ✅ Yes        | common.sh git() function |
| Nix flake evaluation                         | ❌ No         | Fails on stale lock      |
| direnv (nix use flake)                       | ❌ No         | Fails on stale lock      |
| Agent as system user (launchd/systemd)       | ⚠️ Depends    | Only if PATH has shim    |

### 1.2 Root Cause

- **Nix** invokes `git` from its own PATH (typically `/usr/bin` or `/opt/homebrew/bin`).
- **direnv** runs in a subshell; nix's `use flake` spawns nix which spawns git.
- **Agent services** (launchd, systemd) run with minimal PATH; may not include `~/.local/bin`.

### 1.3 Gitoxide / Multitenant Git (Recap)

- **Multitenant git (MTSP-09):** `hooks/lib/common.sh`, `hooks/lib/git-wrapper.sh` — wait for `index.lock`, steal if >10s old.
- **Gitoxide (gix):** Not implemented; GIT_TOOLING_AUDIT_AND_PLAN recommends migration for 5–20x speedup. `gix` uses different locking (`gix-lock`); does not create `index.lock` for read-only ops.
- **git-cache.sh:** TTL cache for read-only git; used by hooks when git() is invoked through common.sh.

---

## 2. Long-Term / Optimal Fixes for index.lock

### 2.1 Option A: System-Level Git Wrapper (Recommended)

**Mechanism:** Install thegent git wrapper as the system `git` so all invocations use it.

| Platform              | Install Location                  | Method                                                                               |
| --------------------- | --------------------------------- | ------------------------------------------------------------------------------------ |
| **macOS (Homebrew)**  | `/opt/homebrew/bin/git` → wrapper | Backup real git, symlink wrapper; or use `brew link --overwrite` with custom formula |
| **macOS (Apple Git)** | `/usr/bin/git`                    | SIP-protected; use `/usr/local/bin/git` if in PATH before `/usr/bin`                 |
| **Linux**             | `/usr/local/bin/git`              | Ensure `/usr/local/bin` before `/usr/bin` in system PATH                             |
| **NixOS**             | Nix profile                       | Override git package to use wrapper                                                  |

**Implementation:**

1. `thegent install-shims --system` (new flag): Install git wrapper to `/usr/local/bin` (or configurable prefix).
2. Wrapper script: Same logic as current shim but uses fixed `THEGENT_GIT_BIN` pointing to real git (e.g. `/opt/homebrew/bin/git` or `/usr/bin/git.bin`).
3. Rename or move real git to `git.bin`; wrapper invokes `git.bin` after lock handling.

**Pros:** All git invocations (nix, direnv, agents, CI) get lock handling.
**Cons:** Requires admin/root; may affect system packages that expect vanilla git.

### 2.2 Option B: Stale Lock Cleanup Daemon

**Mechanism:** Periodic job that removes stale `index.lock` files system-wide.

```yaml
# launchd (macOS) or systemd timer (Linux)
# Run every 5 minutes
# Find .git/index.lock older than 60s, remove
```

**Implementation:**

- `thegent git lock-cleanup` — scan common repo paths, remove stale locks.
- Install as launchd LaunchAgent (user) or LaunchDaemon (system).
- Config: `stale_lock_age_seconds`, `scan_paths`.

**Pros:** No PATH changes; works for any git caller.
**Cons:** Reactive (cleanup after failure); small window where lock can block.

### 2.3 Option C: Nix-Specific Workaround

**Mechanism:** Configure Nix to use a git that goes through our wrapper.

- **NIX_PATH / flake:** Nix uses `git` from PATH when evaluating flakes. If we ensure thegent git wrapper is the _only_ git in PATH for the nix process, it works.
- **direnv:** When `use flake` runs, it inherits direnv's environment. We could `export PATH="$HOME/.local/bin:$PATH"` in `.envrc` before `use flake` — but that brings back the flake evaluation and potential lock contention.
- **Alternative:** Skip flake in direnv (current fix); run `nix develop` manually. No lock contention in direnv.

**Pros:** No system changes.
**Cons:** Doesn't fix nix when run by other tools (CI, scripts).

### 2.4 Option D: Gitoxide (gix) for Read-Only

**Mechanism:** Use `gix` (gitoxide) for read-only operations. `gix` does not create `index.lock` for status/diff/rev-parse.

- **Nix:** Nix uses `git` for fetch/nix flake metadata. We cannot replace Nix's git with gix without patching Nix.
- **Hooks:** thegent-hooks (Rust) can use `gix` for read-only; avoids subprocess and index.lock for those ops.
- **Impact:** Reduces lock contention from our own hooks; does not help nix/direnv.

**Pros:** 5–20x faster; less lock contention from thegent.
**Cons:** Does not solve nix/direnv using canonical git.

---

## 3. Recommended Phased Approach

### Phase 1: Immediate (Done)

- **kush/.envrc:** Venv-only; no flake in direnv. Avoids lock contention in shell startup.
- **Manual:** `rm -f .git/index.lock` when needed.

### Phase 2: Stale Lock Daemon (Low Effort)

- Add `thegent git lock-cleanup` command.
- Install via `thegent prune service install` (reuse existing launchd/systemd plumbing).
- Run every 5 min; remove locks older than 60s.

### Phase 3: System-Level Git Wrapper (Medium Effort)

- Add `thegent install-shims --system` (or `--prefix /usr/local`).
- Document for admin install; optional for power users.
- Ensures nix, direnv, and all tools use lock-aware git.

### Phase 4: Gitoxide Integration (Per GIT_TOOLING_AUDIT)

- Implement gix in thegent-git and thegent-hooks.
- Reduces lock creation from our own code path.

---

## 4. Agent as System User — Hooks and Git

### 4.1 Requirements

When thegent runs as a **system user** (launchd, systemd, Windows Service):

- **Hooks** must be discoverable and executable.
- **Git** invocations from hooks must use multitenant logic (lock wait/steal).
- **PATH** for the agent process may not include `~/.local/bin`.

### 4.2 Current Agent Service Layout

| Component      | Location                       | Agent User Access                       |
| -------------- | ------------------------------ | --------------------------------------- |
| thegent binary | `~/.local/bin/thegent` or venv | User-specific; system user has own home |
| Hooks          | `$(thegent root)/hooks/`       | Must be under agent install path        |
| Git shim       | `~/.local/bin/git`             | Not in system user PATH                 |
| common.sh      | `hooks/lib/common.sh`          | Sourced by hooks                        |

### 4.3 System User Deployment Model

For **agent as system user** (e.g. `_thegent` or dedicated `thegent-agent`):

1. **Install prefix:** `/opt/thegent` or `/usr/local/thegent` (configurable).
2. **Binaries:** `$PREFIX/bin/thegent`, `$PREFIX/bin/git` (our wrapper).
3. **Hooks:** `$PREFIX/share/thegent/hooks/`.
4. **Config:** `$PREFIX/etc/thegent/config.yaml` or `/etc/thegent/config.yaml`.
5. **Data:** `/var/lib/thegent` (sessions, cache, run registry).

### 4.4 PATH for Agent Service

- **launchd (macOS):** Set `PATH` in plist: `PATH=/opt/thegent/bin:/usr/bin:/bin:/usr/sbin:/sbin`.
- **systemd (Linux):** `Environment="PATH=/opt/thegent/bin:/usr/bin:/bin"`.
- **Windows Service:** Add `C:\Program Files\thegent\bin` to system PATH or use `Environment` in service config.

### 4.5 Hook Discovery

- **THGENT_ROOT** or **THGENT_HOOKS_DIR** env var for agent service.
- Fallback: `$(dirname $(which thegent))/../share/thegent/hooks` or similar.

---

## 5. Universalize to OS Level — Implementation Checklist

### 5.1 Git Wrapper Universalization

- [x] **thegent install-shims --system** (or `--prefix /usr/local`): Install git wrapper to system path.
- [x] **thegent install-shims --system --uninstall**: Restore original git.
- [ ] Document in INSTALLATION.md: "For nix/direnv compatibility, run as admin: `thegent install-shims --system`."
- [ ] **Stale lock daemon:** `thegent git lock-cleanup` + cron/launchd/systemd timer.

### 5.2 Agent System User Support

- [ ] **Install target:** `thegent install --target system` (or `--prefix /opt/thegent`).
- [ ] **System layout:** bin, share/thegent/hooks, etc/thegent, var/lib/thegent.
- [ ] **launchd plist:** PATH includes thegent bin first.
- [ ] **systemd unit:** Same.
- [ ] **Hooks path:** Resolve from THGENT_ROOT or install prefix.

### 5.3 Integration with Existing Plans

- [ ] **GIT_TOOLING_AUDIT_AND_PLAN:** Add Phase 5 "OS-Level Git Wrapper" and Phase 6 "Stale Lock Daemon".
- [ ] **AGENT_OS_PRINCIPALS_DEPTH:** Add "Git wrapper in agent PATH" to systemd/launchd scope.
- [ ] **CROSS_PLATFORM_MULTI_TENANT:** Add git wrapper to agent-user isolation requirements.
- [ ] **HOOK_RUNTIME_RUST_DESIGN:** thegent-hooks `git` subcommand implements lock logic; can be called by system-level wrapper.

---

## 6. Web Research Summary

### 6.1 Git index.lock

- **Standard behavior:** Git creates `.git/index.lock` during index-modifying operations; removes on success. If process crashes, lock remains.
- **No git config** to disable or auto-clean index.lock. `core.fsync` controls fsync behavior, not lock handling.
- **Best practice:** External cleanup (cron, daemon) or wrapper that waits/steals.

### 6.2 Gitoxide (gix)

- **gix-lock:** Gitoxide uses `gix-lock` for locking; different from `index.lock`. Read-only ops (status, diff, rev-parse) do not create index.lock.
- **Relevance:** Using gix for our read-only path reduces lock creation; does not help nix/direnv which use canonical git.

### 6.3 System-Level Wrappers

- **/usr/local/bin precedence:** On many systems, `/usr/local/bin` is before `/usr/bin` in default PATH. Installing wrapper to `/usr/local/bin/git` can shadow system git.
- **Homebrew:** `/opt/homebrew/bin` is typically first on Apple Silicon. Wrapper there would catch most invocations.
- **Nix:** Uses its own store; `git` comes from nixpkgs. Overriding would require nix overlay or custom package.

---

## 9. Wider and Deeper Research

### 9.1 Git Upstream: Stale Lock Debugging (2025–2026)

**Source:** [public-inbox.org/git](https://public-inbox.org/git/?q=index.lock)

- **Patch series:** "lockfile: add PID file for debugging stale locks" (Paulo Casaretto, v1–v6, Dec 2025–Feb 2026).
- **Idea:** Write PID into lock file (or companion file) so stale locks can be diagnosed: check if process still exists before stealing.
- **Status:** In review; Junio Hamano, Patrick Steinhardt, Taylor Blau, Jeff King commenting.
- **Relevance:** Future git may improve stale-lock diagnostics; our wrapper can adopt similar logic (check PID before steal).

### 9.2 Known index.lock Failure Modes

| Scenario                        | Source                                                                         | Notes                                                                                                              |
| ------------------------------- | ------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------ |
| **Parallel worktree checkouts** | [git@vger](https://public-inbox.org/git/?q=index.lock) — Raul Rangel, Feb 2023 | `index.lock exists` when multiple worktrees check out concurrently; brian m. carlson discussed.                    |
| **FreeBSD ports**               | [git@vger](https://public-inbox.org/git/?q=index.lock) — Yuri, Sep 2021        | Intermittent `Unable to create '/usr/ports/.git/index.lock': File exists`; Jeff King: external cleanup or wrapper. |
| **git stash**                   | [git@vger](https://public-inbox.org/git/?q=index.lock) — Keith Layne, Jan 2023 | `git stash` exits without output when lockfile present; Patrick Steinhardt: report failure to write index.         |
| **git merge**                   | [git@vger](https://public-inbox.org/git/?q=index.lock) — Kyle Zhao, 2024       | Merge avoids writing merge state when unable to write index; better error handling.                                |

### 9.3 Git Repository Layout (Official)

**Source:** [git-scm.com/docs/gitrepository-layout](https://git-scm.com/docs/gitrepository-layout)

- **index:** "The current index file for the repository. It is usually not found in a bare repository."
- **index.lock:** Not explicitly documented in layout; created transiently during index writes.
- **sharedindex.\***: Split-index mode; references shared index.
- **worktrees/\*/locked:** Per-worktree lock; different from `index.lock`.

### 9.4 Gitoxide (gix) — Crate Status Deep Dive

**Source:** [gitoxide/crate-status.md](https://github.com/GitoxideLabs/gitoxide/blob/main/crate-status.md)

| Crate                  | index.lock / Locking                          | Status                                                   |
| ---------------------- | --------------------------------------------- | -------------------------------------------------------- |
| **gix-index**          | Read: no lock. Write: uses lock (V2/V3 write) | Read ✅; Write ✅ (V2, V3); V4, REUC, UNTR, FSMN partial |
| **gix-lock**           | Separate locking abstraction                  | Production-grade (Stability Tier 1)                      |
| **gix-tempfile**       | Temp files, cleanup                           | Production-grade (Stability Tier 2)                      |
| **gix-status**         | Read-only; no index write                     | ✅ differences index↔worktree                           |
| **gix-worktree-state** | Checkout, index write                         | ✅ checkout; uses locking when writing                   |

**Implication:** gix _does_ use locking when writing index; read-only ops (status, diff, rev-parse, ls-files) avoid index.lock. Our hooks' read path can use gix without creating locks.

### 9.5 direnv + Nix Integration Landscape

**Source:** [direnv/direnv/wiki/Nix](https://github.com/direnv/direnv/wiki/Nix)

| Option                 | Caching | GC Root | Flakes | Notes                                     |
| ---------------------- | ------- | ------- | ------ | ----------------------------------------- |
| **Standard `use nix`** | ❌      | ❌      | ✅     | Slow; no GC protection                    |
| **Nix-direnv**         | ✅      | ✅      | ✅     | Most common; `use flake`                  |
| **Lorri**              | ✅      | ✅      | ✅     | Daemon; background pre-eval               |
| **Lorelei**            | ✅      | ✅      | ❌     | Uses Lorri GC logic                       |
| **Nixify**             | ✅      | ✅      | ❌     | Scaffold; overwrites `use_nix`            |
| **Hand-rolled**        | Varies  | ❌      | ✅     | `eval "$(nix print-dev-env)"`; no GC root |

**Lock contention:** All options that run `nix` (flake or shell) invoke git. If `.envrc` runs flake eval, git is used; stale index.lock blocks. **Lorri** pre-evaluates in background — first load can still hit lock; subsequent loads use cache.

### 9.6 Nix Flakes and Git

- **Nix** uses `git` for: flake metadata, `git+file://` inputs, `git` fetcher.
- **Flake evaluation** happens when `nix develop`, `nix build`, or `use flake` runs.
- **No Nix-native index.lock handling:** Nix does not wrap or intercept git; it uses whatever `git` is in PATH.
- **NixOS/nix issues:** No direct `index.lock` issues in Nix repo search; problem is environmental (user repos, not nixpkgs).

### 9.7 CI/CD and Multi-Tenant Git Patterns

| Pattern                     | Use Case                    | Lock Handling                                          |
| --------------------------- | --------------------------- | ------------------------------------------------------ |
| **Ephemeral clones**        | CI (GitHub Actions, GitLab) | Fresh clone per job; no shared index.lock              |
| **Shared workspace**        | Monorepo, multi-agent       | Lock contention; wrapper or daemon needed              |
| **Parallel jobs same repo** | Matrix builds               | Each job typically has own clone; isolation            |
| **Bare + worktrees**        | Servers, deployment         | Each worktree has own index; `index.lock` per worktree |

**thegent case:** Multiple agents (Cursor, Codex, Claude) share same repo; hooks run in same dir. Classic shared-workspace contention.

### 9.8 Security and Correctness

- **Stealing stale lock:** Safe if lock is truly stale (process dead). Risk: process alive but slow → steal → corruption. Our 10s threshold is conservative; 60s for daemon is safer.
- **PID check:** If lock file (or companion) contains PID, `kill -0 $PID` can verify process exists before steal. Aligns with upstream PID-file patch.
- **Atomicity:** Git writes index to temp file, then renames. Lock protects the write. Stealing lock then running git may see partially written index; git may recover or error.

### 9.9 Alternative Lock Strategies (Not Git)

| Approach                 | Pros                                             | Cons                                               |
| ------------------------ | ------------------------------------------------ | -------------------------------------------------- |
| **fcntl advisory lock**  | OS-level; survives process crash if OS cleans up | Git doesn't use it for index; would need patch     |
| **PID file**             | Debuggable; can check liveness                   | Not atomic with lock; race window                  |
| **Lease / heartbeat**    | Can detect slow-but-alive process                | Complex; git doesn't support                       |
| **Separate lock daemon** | Centralized coordination                         | Overkill for single-repo; multi-repo could benefit |

### 9.10 Cross-Platform Considerations

| Platform                  | System git path                    | Wrapper install          | Notes                              |
| ------------------------- | ---------------------------------- | ------------------------ | ---------------------------------- |
| **macOS (Intel)**         | `/usr/bin/git` (Xcode)             | `/usr/local/bin/git`     | SIP protects `/usr/bin`            |
| **macOS (Apple Silicon)** | `/opt/homebrew/bin/git`            | Same or `/usr/local/bin` | Homebrew first in PATH             |
| **Linux (typical)**       | `/usr/bin/git`                     | `/usr/local/bin/git`     | FHS; local before usr              |
| **NixOS**                 | `/run/current-system/sw/bin/git`   | Nix override             | Need overlay or wrapper in profile |
| **Windows**               | `C:\Program Files\Git\cmd\git.exe` | Prepend custom path      | PATH order; no /usr/local          |

### 9.11 Related thegent Docs (Stale Lock Patterns)

- **HOOK_RUST_MIGRATION_COMPLETE.md:** Rust hook checks `index.lock`, steals if >5 min.
- **HOOK_RUNTIME_RUST_COMPLETE.md:** `is_lock_stale()`, steal logic in Rust.
- **ROBUSTNESS_AND_FUTURE_DEPTH.md:** Gardener removes stale locks >5 mins.
- **WORK_STREAM_CLAIM_LOCK_AUDIT_AND_PLAN.md:** Stale claim reclaim (TTL, heartbeat).
- **CONVERSATION_DUMP_2026-02-18-CROSS_PLATFORM.md:** Stale locks cleaned after 5 min no heartbeat.

**Consistency:** Align stale threshold (10s for interactive, 60s for daemon) across shell, Rust, and docs.

---

## 10. DuckDuckGo Web Research (2026-02-18)

### 10.1 Industry Best Practices (dev.to, Microsoft Learn, GeeksforGeeks)

**Prevention (dev.to, Geek Logbook):**

- Avoid running multiple Git commands on the same repository at once
- Don't interrupt a Git command that is writing data
- Keep terminal/IDE from closing during commit or pull
- Close editors (VS Code, JetBrains) that may run background Git processes

**Recovery (Microsoft Learn, dev.to):**

1. Check for active Git processes (`ps aux | grep git`, Task Manager for `git.exe`)
2. If none running, remove: `rm -f .git/index.lock`
3. Verify: `git status`; if corrupted: `git reset`, `git gc --prune=now`, `git fsck`

**Microsoft Azure DevOps:** "Orphaned index.lock" = process terminated or unresponsive; delete after verifying no Git processes. Error: "The index is locked. This might be due to a concurrent or crashed process."

### 10.2 Additional Root Causes (w3tutorials, codestudy.net)

- **Antivirus/Backup:** Windows Defender, OneDrive may lock `index.lock` while scanning/backing up `.git`
- **Concurrent Git + IDE:** Terminal `git pull` while VS/GitHub Desktop syncing
- **Corrupted index:** Damaged staging area can hang, leaving lock behind

### 10.3 Git Override: PATH Wrapper (Stack Overflow)

**Source:** [SO 3538774](https://stackoverflow.com/questions/3538774/is-it-possible-to-override-git-command-by-git-alias)

- **Git alias cannot override builtins** (Hamano WONTFIX 2009)
- **Solution:** Symlink or script in directory early in PATH (e.g. `~/bin/git`)
- **David Mertens:** `export PATH="~/bin:$PATH"` + `alias git='my-git'`; script checks first arg and delegates to `/usr/local/bin/git`
- **Dabe Murphy:** `~/bin/git` wrapper that looks for `~/bin/git-${command}` and runs it, else falls back to real git
- **Critical:** Wrapper must not exec itself (avoid recursion); use `command git` or absolute path to real binary

### 10.4 Git Locking Strategy (Stack Overflow)

**Source:** [SO 19962024](https://stackoverflow.com/questions/19962024/locking-strategy-of-git-to-achieve-concurrency)

- **index.lock:** Used for index (staging area); local repo only, usually single user
- **index-pack:** Creates `.keep` file to prevent race during pack operations
- **Refs:** Atomic compare-and-set; lock file, check old value, replace, delete lock

### 10.5 Cron/Automated Cleanup — Caveat (Stack Overflow)

**Source:** [SO 71442207](https://stackoverflow.com/questions/71442207/how-to-safely-remove-git-index-lock)

- **torek (501k rep):** Do **not** automate removal based on "no git process" — inherently racy
- **Risk:** Cron could remove lock just as you're committing; `index.lock` holds the _new_ index being written
- **Mitigation:** Use **file age** (mtime) — only remove locks older than N seconds (e.g. 60s). Our daemon design (remove if >60s old) is safe; avoid "process check then delete" logic.

### 10.6 Nix + Git (NixOS/nix #8854)

- **Issue:** `nix develop` fails when `flake.lock` is gitignored; Nix stages `flake.lock` via `git add`; if git fails (e.g. index.lock), nix fails
- **Workaround:** `nix develop path://$PWD` bypasses Git integration (costly: copies dir to store)
- **Alternative:** `--no-write-lock-file` for certain workflows
- **Relevance:** Nix _always_ invokes git for flake repos; git lock blocks nix

### 10.7 Gitoxide Performance (GitHub Discussions, Reddit, gist)

- **Gitoxide diff discussion #74:** ~4x faster than libgit2 in multithreaded mode; libgit2 ~30% behind even with threading
- **gix status:** Early implementation; git2-to-gix migration improved gengo 40x–60x on WebKit repo
- **Checkout benchmarks (gist):** git vs. gitoxide on Linux kernel repo; gitoxide faster for clone/checkout
- **Relevance:** Confirms 5–20x speedup potential for read-only ops; our gix migration aligns with industry benchmarks

### 10.8 Git for Windows Wrapper

**Source:** [gitforwindows.org/git-wrapper.html](https://gitforwindows.org/git-wrapper.html)

- Git for Windows uses a wrapper that modifies PATH so Git's own bins come first
- **Pattern:** Prepend custom path to intercept; our system wrapper follows same pattern

### 10.9 Git Upstream: PID File for Stale Locks (2025–2026)

**Source:** [public-inbox.org/git](https://public-inbox.org/git/?q=index.lock+PID)

- **Paulo Casaretto:** [PATCH v6] lockfile: add PID file for debugging stale locks (Jan–Feb 2026)
- Patch series v1–v6 (Dec 2025–Feb 2026); under review by Junio Hamano, Patrick Steinhardt, Taylor Blau, Jeff King
- **Purpose:** Write PID into lock file so tools can check if owning process is still alive before stealing
- **Relevance:** When merged, our daemon can use PID check _in addition to_ mtime for safer stale detection

### 10.10 Git `--no-optional-locks` / `GIT_OPTIONAL_LOCKS=0`

**Sources:** [git-status docs](https://git-scm.com/docs/git-status), [shadow-rs #221](https://github.com/baoyachi/shadow-rs/issues/221), [superuser](https://superuser.com/questions/1566604)

- **git-status docs:** "Scripts running status in the background should consider using `git --no-optional-locks status`"
- **Mitigation:** `GIT_OPTIONAL_LOCKS=0` (env) or `git --no-optional-locks status` — avoids creating index.lock for read-only status
- **shadow-rs #221 (Mar 2025):** Next.js build invokes git; optional locks can leave stale index.lock; fixed by vercel/next.js#76773
- **Scope:** Currently only `git status`; Git may extend to more commands
- **Relevance:** Hooks/scripts that run `git status` in background can set `GIT_OPTIONAL_LOCKS=0` to reduce lock creation

### 10.11 Git Worktrees for AI/CLI Agents (2025)

**Source:** [blog.balakumar.dev Sep 2025](https://blog.balakumar.dev/2025/09/25/why-git-worktrees-beat-switching-branches-especially-with-ai-cli-agents/)

- **"Fewer Git lock fights."** Agents and scripts can trigger `index.lock` conflicts if they overlap. Separate worktrees = separate indexes; far fewer "Another git process seems to be running" errors.
- **Workflow:** `git worktree add -b spike/agent-rewrite ../repo-agent-rewrite origin/main` — isolated checkout for agent; merge back when done
- **Benefits:** Stable paths for AI context; isolated deps (`.venv`, `node_modules`); long-running jobs don't conflict
- **Relevance:** Agent-as-system-user can use worktrees per task to avoid index.lock contention with user/main worktree

### 10.12 Gitoxide / gix 2025–2026 Status

**Sources:** [Gitoxide Jan 2025](https://github.com/GitoxideLabs/gitoxide/discussions/1791), [Starship #6476](https://github.com/starship/starship/pull/6476), [CVE-2025-22620](https://www.wiz.io/vulnerability-database/cve/cve-2025-22620)

- **Jan 2025:** Complete `gix status` (tree→index diff); `gix blame` experimental; CVE-2025-22620 (gix-worktree-state 0777 permissions) fixed in **0.17.0**
- **Starship (merged Apr 2025):** gix for `git_status` and `git_metrics`; 2x WebKit, 2x Linux kernel, up to 6.75x Rust repo; opt-out for `core.fsmonitor`; sparse repos fallback to git
- **CVE-2025-22620:** Use gix-worktree-state ≥0.17.0 for checkout operations
- **Relevance:** gix status production-ready; use gix ≥0.17.0; consider `core.fsmonitor` fallback in our hooks

### 10.13 Lock Types and Diagnostics (LabEx, dev.to Nov 2025)

**Sources:** [LabEx](https://labex.io/tutorials/git-how-to-fix-git-repository-lock-problem-419780), [dev.to Rijul Rajesh Nov 2025](https://dev.to/rijultp/fixing-common-git-lock-errors-understanding-and-recovering-from-gitindexlock-47ej)

- **Lock types:** index.lock (staging), ref lock (`.git/refs/`), worktree lock (`.git/worktrees/`)
- **Diagnostics:** `lsof .git/index.lock` — check process holding lock; `stat .git/index.lock` — mtime for staleness
- **dev.to Nov 2025:** Step-by-step recovery; `git reset`, `git gc --prune=now`, `git fsck` for corrupted index

### 10.14 Next.js / shadow-rs (Mar 2025)

**Source:** [shadow-rs #221](https://github.com/baoyachi/shadow-rs/issues/221)

- Build tools that invoke `git` (e.g. version from `git describe`) can leave stale index.lock
- **Fix:** `GIT_OPTIONAL_LOCKS=0` or `git --no-optional-locks status`; vercel/next.js#76773
- **Relevance:** CI/build environments; ensure build scripts use `--no-optional-locks` for read-only git

---

## 11. Long-Term Optimal Solution (Synthesis)

**Recommendation (DDG + prior research, as of 2026):**

| Layer                             | Solution                                     | Rationale                                                                                                  |
| --------------------------------- | -------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| **1. Prevention**                 | System git wrapper in PATH                   | All invocations (nix, direnv, IDE, agents) get wait/steal; Stack Overflow confirms PATH override           |
| **2. Stale cleanup**              | Daemon by **file age only** (≥60s)           | Never remove based on process check (torek: racy); mtime is safe; when Git PID patch merges, add PID check |
| **3. Read path**                  | Gitoxide (gix) ≥0.17.0 for hooks             | 2x–6.75x faster (Starship); no index.lock for status; CVE-2025-22620 fixed in 0.17.0                       |
| **4. Reduce locks**               | `GIT_OPTIONAL_LOCKS=0` for background status | git-status docs; shadow-rs, Next.js; avoids optional index.lock for read-only status                       |
| **5. Agent isolation (optional)** | Git worktrees per agent task                 | Complementary; primary = shared-repo multi-tenancy                                                         |
| **6. Windows**                    | Exclude `.git` from antivirus/OneDrive scan  | w3tutorials: AV/backup can lock index.lock                                                                 |
| **7. Agent**                      | Install prefix + PATH for system user        | Hooks + git wrapper must be in agent service PATH                                                          |

**Avoid:** Cron that removes lock when "no git process" — inherently racy (torek).

**Upstream watch:** Paulo Casaretto's PID-in-lockfile patch (Git mailing list, Feb 2026) — when merged, enables safer stale detection.

---

## 12. References

- [GIT_TOOLING_AUDIT_AND_PLAN.md](./GIT_TOOLING_AUDIT_AND_PLAN.md)
- [DIRENV_FIX_2026-02-18.md](./DIRENV_FIX_2026-02-18.md)
- [AGENT_OS_PRINCIPALS_DEPTH.md](../reference/AGENT_OS_PRINCIPALS_DEPTH.md)
- [CROSS_PLATFORM_MULTI_TENANT_QUICK_REFERENCE.md](../reference/CROSS_PLATFORM_MULTI_TENANT_QUICK_REFERENCE.md)
- [HOOK_RUST_MIGRATION_RESEARCH_SYNTHESIS.md](./HOOK_RUST_MIGRATION_RESEARCH_SYNTHESIS.md)
- [HOOK_RUNTIME_RUST_DESIGN.md](../plans/HOOK_RUNTIME_RUST_DESIGN.md)
- [Gitoxide](https://github.com/GitoxideLabs/gitoxide)
- [git config core.fsync](https://git-scm.com/docs/git-config#Documentation/git-config.txt-corefsync)
- [Git repository layout](https://git-scm.com/docs/gitrepository-layout)
- [direnv Nix wiki](https://github.com/direnv/direnv/wiki/Nix)
- [Gitoxide crate-status](https://github.com/GitoxideLabs/gitoxide/blob/main/crate-status.md)
- [Git list index.lock](https://public-inbox.org/git/?q=index.lock)
- [Stack Overflow: How to safely remove git index lock](https://stackoverflow.com/questions/71442207/how-to-safely-remove-git-index-lock) (torek: avoid process-check cron; use age)
- [Stack Overflow: Override git by alias](https://stackoverflow.com/questions/3538774/is-it-possible-to-override-git-command-by-git-alias)
- [Stack Overflow: Git locking strategy](https://stackoverflow.com/questions/19962024/locking-strategy-of-git-to-achieve-concurrency)
- [NixOS/nix #8854](https://github.com/NixOS/nix/issues/8854) (nix + gitignored flake.lock)
- [Git for Windows wrapper](https://gitforwindows.org/git-wrapper.html)
- [Git mailing list: index.lock PID patch](https://public-inbox.org/git/?q=index.lock+PID) (Paulo Casaretto, 2025–2026)
- [Git --no-optional-locks](https://git-scm.com/docs/git-status) (git-status docs)
- [shadow-rs #221](https://github.com/baoyachi/shadow-rs/issues/221) (optional locks, Next.js)
- [Why Git Worktrees Beat Switching Branches (AI/CLI agents)](https://blog.balakumar.dev/2025/09/25/why-git-worktrees-beat-switching-branches-especially-with-ai-cli-agents/) (Sep 2025)
- [Gitoxide Jan 2025](https://github.com/GitoxideLabs/gitoxide/discussions/1791) (gix status complete)
- [Starship #6476](https://github.com/starship/starship/pull/6476) (gix integration, Apr 2025)
- [CVE-2025-22620](https://www.wiz.io/vulnerability-database/cve/cve-2025-22620) (gix-worktree-state, use ≥0.17.0)
- [dev.to: Fixing Git Lock Errors](https://dev.to/rijultp/fixing-common-git-lock-errors-understanding-and-recovering-from-gitindexlock-47ej) (Nov 2025)
- [LabEx: Git repository lock problem](https://labex.io/tutorials/git-how-to-fix-git-repository-lock-problem-419780)

---

## 13. Summary

| Fix                            | Effort    | Impact                                         | When      |
| ------------------------------ | --------- | ---------------------------------------------- | --------- |
| Venv-only .envrc               | Done      | Avoids direnv lock loop                        | Immediate |
| GIT_OPTIONAL_LOCKS=0 for hooks | Low       | Reduces lock creation for status               | Phase 2   |
| Stale lock daemon              | Low       | Proactive cleanup (mtime ≥60s)                 | Phase 2   |
| System git wrapper             | Medium    | Universal lock handling                        | Phase 3   |
| Agent worktrees (optional)     | Low       | Complementary isolation; primary = shared-repo | Phase 3   |
| Gitoxide (gix) ≥0.17.0         | Per audit | 2x–6.75x speed; CVE fixed                      | Phase 4   |
| Agent system user layout       | Medium    | Hooks + git for services                       | Phase 3   |

**Optimal long-term (2026):** System git wrapper + stale lock daemon (mtime; add PID when upstream merges) + `GIT_OPTIONAL_LOCKS=0` for background status + gix ≥0.17.0. Worktrees optional for heavy parallel work; **true multi-tenancy** (shared repo, many agents) is the primary design.

---

## 14. Engineered Solutions (First-Principles & Cross-Domain)

_Reasoning from scratch and borrowing strategies from other domains to engineer robust solutions._

### 14.1 Cross-Domain Strategy Mapping

| Domain                     | Pattern                                              | Application to index.lock                                                     |
| -------------------------- | ---------------------------------------------------- | ----------------------------------------------------------------------------- |
| **Database locking**       | Read vs write locks; read-only ops bypass write lock | Route status/diff to gix or `--no-optional-locks`; only write ops contend     |
| **Distributed systems**    | Lease + heartbeat; if no renewal, assume dead        | mtime = implicit lease expiry; 60s = no heartbeat → stale                     |
| **File systems (NFS)**     | Stale lock detection via open-handle check           | `lsof .git/index.lock` — if no process has file open, safe to remove          |
| **Circuit breaker**        | Fail fast after N consecutive failures               | After 3 lock-wait failures in 5 min, run cleanup once and retry               |
| **Build systems (Bazel)**  | Hermetic, cache-first; avoid touching shared state   | gix for read path = no index.lock; cache (git_cached) = fewer git invocations |
| **CI/CD**                  | Ephemeral clones vs shared workspace                 | Worktrees = per-task isolation; each has own index                            |
| **Advisory locks (flock)** | Cooperative; holder signals "I'm alive"              | When Casaretto PID merges: PID in lock = can verify process alive             |

### 14.2 First-Principles Analysis

**Root cause:** Git uses a single global lock (index.lock) for all index-modifying ops. Staleness occurs when (a) process crashes mid-write, (b) optional locks from `git status` overlap with writes, (c) concurrent tools (nix, direnv, IDE, agent) contend.

**Invariant we need:** "No process is actively writing the index" before we remove the lock. We cannot observe this directly. Proxies:

- **mtime > T:** Lock untouched for T seconds → likely orphaned (distributed-lease analogy)
- **lsof empty:** No process has file open → either stale or just released (NFS-style)
- **PID dead:** When upstream adds PID, we can check `/proc/<pid>` or `kill -0` (future)

**Safety vs liveness:** Removing a live lock corrupts data (safety). Never removing blocks forever (liveness). We bias toward liveness (allow removal) only when confidence of staleness is high: mtime ≥ 60s. Adding lsof as a _negative_ check (if lsof shows a holder, never remove) improves safety without harming liveness.

### 14.3 Engineered Strategies

#### Strategy E1: Preemptive Cleanup at Entry Points

**Idea:** Before tools that are known to invoke git (nix, direnv `use flake`), run a lightweight cleanup. Don't wait for failure.

**Implementation:**

- In `.envrc` before `use flake`: `thegent git lock-cleanup --path . --max-age 60 2>/dev/null || true`
- In agent task start: `thegent git lock-cleanup --path $REPO --max-age 60` before first git op
- **Cost:** ~50–200ms if no lock; ~1s if lock removed. **Benefit:** nix/direnv rarely see stale lock.

#### Strategy E2: lsof as Secondary Staleness Check

**Idea:** torek warned against "no git process" (racy). But `lsof .git/index.lock` checks if the _file_ is open. If a process has it open, it's alive. If not, either stale or just released.

**Implementation (daemon):**

```
if [[ -f .git/index.lock ]]; then
  age=$(mtime_now - mtime_of .git/index.lock)
  if [[ $age -ge 60 ]]; then
    if lsof .git/index.lock 2>/dev/null | grep -q .; then
      # Process holds it — do NOT remove
      continue
    fi
    rm -f .git/index.lock  # Safe: old and no open handle
  fi
fi
```

**Rationale:** mtime alone can have a race (process started 59s ago, slow). lsof adds: "if anyone has it open, don't touch." Reduces false-positive removals.

#### Strategy E3: Circuit Breaker for Lock Contention

**Idea:** If we've failed to acquire lock repeatedly, don't spin — run cleanup and retry once.

**Implementation (wrapper):**

- Maintain per-repo failure count (in-memory or `.git/thegent.lock.failures` with timestamp)
- On lock-wait timeout (max retries): increment. If count ≥ 3 in last 5 min, run `lock-cleanup` for this repo, reset count, retry once.
- **Benefit:** User gets unblocked faster; avoids endless retry loops.

#### Strategy E4: Read Path — Zero Lock Creation

**Idea:** Never create index.lock for read-only ops we control.

**Implementation:**

1. **git_cached** (and gix when available): Use `gix` for status/diff/rev-parse — no index.lock.
2. **Fallback to git:** When invoking `git status` from hooks/scripts, use `GIT_OPTIONAL_LOCKS=0` or `git --no-optional-locks status`.
3. **Wrapper passthrough:** For read-only subcommands, wrapper could inject `--no-optional-locks` before delegating to real git (where supported).

#### Strategy E5: Worktrees as Complementary Isolation (Not Primary)

**Idea:** Worktrees are optional for heavy parallel work. The primary design is **true multi-tenancy** — many agents in one repo, coordinated via lock wait/steal.

**Implementation:**

- `thegent agent worktree create --task $TASK` → optional escape hatch when isolation is needed
- **Default:** Agents share the main repo; wrapper + daemon handle contention; no worktree required
- **When to use worktrees:** Long-running agent spikes, heavy parallel branches; merge back when done
- **Benefit:** Shared repo remains the primary value; worktrees complement, not replace, multi-tenancy.

#### Strategy E6: Graceful Degradation with Clear Signals

**Idea:** When we can't acquire lock, fail in a way that tools and users can act on.

**Implementation:**

- Exit code 128 + message: "GIT-MUTEX: Lock held. Run 'thegent git lock-cleanup' or wait."
- Optional: `THEGENT_GIT_LOCK_RETRY=0` to disable wait (fail fast for CI).
- **Benefit:** Scripts can catch 128 and run cleanup or exit cleanly.

### 14.4 Implementation Priority (Engineered)

| Priority | Strategy                                         | Effort | Impact                                     | Phase |
| -------- | ------------------------------------------------ | ------ | ------------------------------------------ | ----- |
| P0       | E4: GIT_OPTIONAL_LOCKS=0 for git_cached fallback | Low    | Reduces lock creation                      | 2     |
| P0       | E2: lsof in lock-cleanup daemon                  | Low    | Safer staleness detection                  | 2     |
| P1       | E1: Preemptive cleanup in direnv .envrc          | Low    | Prevents nix/direnv failures               | 2     |
| P1       | E6: Clear exit codes + THEGENT_GIT_LOCK_RETRY    | Low    | Better script/CI handling                  | 2     |
| P2       | E3: Circuit breaker in wrapper                   | Medium | Faster recovery from contention            | 3     |
| P3       | E5: `thegent agent worktree` command             | Medium | Optional isolation; shared repo is primary | 3     |

### 14.5 Summary: Engineered Solution Stack

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 1: Avoid (gix, --no-optional-locks, git_cached)          │
│  → Never create index.lock for read path we control             │
├─────────────────────────────────────────────────────────────────┤
│  Layer 2: Isolate (worktrees optional; shared repo primary)   │
│  → True multi-tenancy = many agents in one repo; worktrees complement │
├─────────────────────────────────────────────────────────────────┤
│  Layer 3: Preempt (cleanup before nix/direnv/agent)              │
│  → Clear stale locks at entry points                             │
├─────────────────────────────────────────────────────────────────┤
│  Layer 4: Wait + Steal (wrapper with mtime, future: PID)          │
│  → Cooperative wait; steal only when mtime≥60s (+ lsof check)    │
├─────────────────────────────────────────────────────────────────┤
│  Layer 5: Daemon (periodic cleanup, mtime + lsof)                │
│  → Reactive cleanup for locks we didn't catch                    │
├─────────────────────────────────────────────────────────────────┤
│  Layer 6: Fail gracefully (exit 128, THEGENT_GIT_LOCK_RETRY)    │
│  → Scripts and CI can handle; no silent hangs                     │
└─────────────────────────────────────────────────────────────────┘
```

### 14.6 Implementation Notes (Code Touchpoints)

| Strategy                 | File                                    | Change                                                                                 |
| ------------------------ | --------------------------------------- | -------------------------------------------------------------------------------------- |
| E4: GIT_OPTIONAL_LOCKS=0 | `hooks/lib/git-cache.sh`                | Before `"$_git" "$@"`, set `GIT_OPTIONAL_LOCKS=0` in env for status/diff/ls-files      |
| E4                       | `hooks/lib/common.sh` git()             | When delegating read-only to git (no git_cached), use `--no-optional-locks` for status |
| E2: lsof check           | `thegent git lock-cleanup` (new)        | After mtime≥60, run `lsof .git/index.lock`; skip removal if any process holds it       |
| E1: Preemptive cleanup   | `.envrc` template                       | Add `thegent git lock-cleanup --path . 2>/dev/null \|\| true` before `use flake`       |
| E6: Fail fast            | `hooks/lib/git-wrapper.sh`, `common.sh` | Support `THEGENT_GIT_LOCK_RETRY=0` to skip wait; exit 128 with clear message           |
