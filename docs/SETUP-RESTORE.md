# Setup Restore — Long-term Fixes Applied

## Summary of Changes

### 1. **thegent Shims (MTSP-10)**

**Purpose:** Tool accelerators for optimization and multi-tenant coordination.

- **Git shim** (`~/.local/bin/git`): Wraps git to inject hooks from `thegent/hooks/lib/common.sh` — multi-tenant lock coordination, index.lock contention handling, git_cached for read-only ops.
- **Tool accelerators:** grep→rg, find→fd, jq→jaq, uv (faster alternatives).
- **Agent accelerators (NEW):** `codex` and `copilot` — exec real binaries directly to avoid:
  - zsh parsing Node.js scripts (copilot `/*---` glob error)
  - git subcommand routing (`git codex` / `git copilot` not a git command)
- **Role accelerators:** run, bg, ps, logs, etc. → `thegent {role}`.

**PATH:** `~/.local/bin` must be early in PATH (first). Your `~/.zshenv` sets this.

### 2. **Copilot Parse Error (Fixed)**

The copilot script is a Node.js binary. When invoked as `zsh /opt/homebrew/bin/copilot`, zsh tries to parse it and fails on `/*---` (glob). **Fix:** thegent shims in `~/.local/bin` exec the real binary directly via bash, so the shebang is respected. Run `copilot` (not `zsh copilot`).

### 3. **Codex / Copilot Git Routing (Fixed)**

Same fix: thegent agent shims ensure `codex` and `copilot` resolve to the real binaries in `~/.local/bin` (before homebrew), and they `exec` directly — no git involvement.

**If you see** `git: '/opt/homebrew/bin/codex' is not a git command` when running `codex`:

1. **Install shell + shims:**

   ```bash
   thegent install -t shell
   thegent install-shims --force
   ```

2. **Reload shell:** `exec zsh` (or open a new terminal)

3. **Verify:** `which codex` should show `~/.local/bin/codex` (not `/opt/homebrew/bin/codex`)

4. **If still wrong:** Check PATH — `echo $PATH` must have `~/.local/bin` first. Your `~/.zshenv` should set this. Run `thegent doctor` to verify.

### 4. **Zsh Setup Restored**

- **~/.zshenv** — Restored from `thegent/shell/.zshenv`. Sets PATH, sources `~/.zsh_bundle.zsh`.
- **~/.zshrc** — Restored from `thegent/shell/.zshrc`. Sources zshenv and bundle.
- **~/.zsh_bundle.zsh** — Replaced with thegent minimal (68 lines). Your previous 150KB bundle referenced missing files (zsh-nvm-x, prompt.zsh, providers/\*, zsh-alias-hinter, fzf-tab, etc.). Backup: `~/.zsh_bundle.zsh.broken` if you created one.

**Full shell setup:** Run:

```bash
thegent install -t shell
```

This installs:

- `~/.zshenv`, `~/.zshrc`, `~/.zsh_bundle.zsh` (thegent core)
- `~/.zshrc.local` from template (when missing)
- Zsh plugins: fzf-tab, zsh-autosuggestions, fast-syntax-highlighting

Use `--no-plugins` to skip plugin install. Verify with `thegent doctor`.

**To restore custom modules:** Use the proper long-term setup:

1. Run `./scripts/install_zsh_plugins.sh` to install fzf-tab, autosuggestions, etc.
2. Copy `shell/zshrc.local.template` to `~/.zshrc.local` (or let the script do it)
3. See **[SHELL_ZSH_PLUGIN_SETUP.md](guides/SHELL_ZSH_PLUGIN_SETUP.md)** for fnm/mise (nvm replacement), starship/p10k, and troubleshooting

### 5. **Ghostty Config**

Created `~/.config/ghostty/config`:

- Shell: `/bin/zsh -l` (login shell, loads ~/.zshenv)
- Theme: one-dark
- Font: JetBrains Mono 13
- Cursor: bar, blink

Reload: `cmd+shift+,` (macOS).

---

## Troubleshooting

### "find: illegal option -- o" / "find: illegal option -- q"

**Cause:** find shim or fd-wrapper was passing find args to fd. **Fixed** in fd-wrapper.sh and install find shim:

- Complex find args (-o, -name, -path, -print, -quit, etc.) now use `command find` (real find)
- Find shim only routes to fd when called with a single path (e.g. `find .`)

### "fork: Resource temporarily unavailable"

**Cause:** Process limit hit (too many hooks/subprocesses). **Mitigations:**

- Set `THEGENT_HOOKS_MINIMAL=1` to skip lightweight advisory hooks (e.g. session-start-pending-notice)
- Close other terminals/IDEs to free processes
- Run `ulimit -u` to check process limit; increase if needed

### "(eval):1: command not found: OPTIMIZATION_INITIATIVE_COMPLETE.md"

**Cause:** Something is `eval`'ing output that contains file paths (each line executed as a command). Check your `.zshrc` / `.zshenv` for `eval $(...)` that might output paths. Avoid eval'ing find/grep output directly.

### "No such option: -e"

**Cause:** Option conflict or wrong tool. With `thegent install`, `-e` is short for `--editable`. If you see this from another command (e.g. codex, copilot), that tool may not support `-e`.

### "No such option: --force" on `dex --native --force`

**Cause:** You are hitting a stale `dex` shim tied to an older CLI surface. The current shim path expects `--force-yolo` for force behavior.

**Fix:**

```bash
thegent install-shims --force
exec zsh  # or open a new terminal
thegent doctor
```

If `which dex` does not point at `~/.local/bin/dex`, reload PATH to prioritize `~/.local/bin` and retry.

### "ps aux" or "ps -ef" hangs 130+ seconds / shell commands very slow

**Cause:** A legacy `~/.local/bin/ps` shim (thegent role accelerator) shadows the system `ps`. When agents or users run `ps aux`, they invoke `thegent ps` (Python CLI for agent sessions) instead of the system process list — which hangs waiting for MCP/API.

**Fix:**

```bash
rm ~/.local/bin/ps
# Or refresh all shims (removes ps, installs current set):
thegent install-shims --force
```

**Verify:** `which ps` should show `/bin/ps` (or `/usr/bin/ps`), not `~/.local/bin/ps`.

---

## Next Steps

1. **Open a new terminal** (or `exec zsh`) to pick up the restored config.
2. **Verify:** `codex --help` and `copilot --help` should work without git errors.
3. **Optional:** Run `./scripts/install_zsh_plugins.sh` and follow [SHELL_ZSH_PLUGIN_SETUP.md](guides/SHELL_ZSH_PLUGIN_SETUP.md) for fnm/mise, fzf-tab, starship.
4. **thegent install:** Run `thegent install` with targets `system` and `user` to sync shell files on future updates.

---

## See also

- [WORK_STREAM.md](reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](plans/00-MASTER-INDEX.md) — plan index
