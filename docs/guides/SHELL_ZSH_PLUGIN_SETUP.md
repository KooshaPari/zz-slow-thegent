# Shell & Zsh Plugin Setup — Long-Term Fix

**Purpose:** Proper, enterprise-grade zsh setup with fnm/mise (nvm replacement), fzf-tab, and optional plugins. No random removal; install what you need.
**Audience:** Enthusiast dev users; DX/AX/UX optimized.

---

## 1. Architecture

```
~/.zshrc
  └── ~/.zshenv          (PATH, early env)
  └── ~/.zsh_bundle.zsh  (thegent minimal: qls, qfind, qgrep)
  └── ~/.zshrc.local     (YOUR plugins — fnm, fzf-tab, prompt, etc.)
```

**Rule:** `~/.zshrc.local` is for your custom plugins. thegent never overwrites it. Use conditional sourcing so missing plugins don't break startup.

---

## 2. Node Version Manager: fnm or mise (nvm replacement)

You migrated from nvm. Use **fnm** (fast, Rust) or **mise** (polyglot: node, python, go, etc.).

### Option A: fnm (Node only, fastest)

```bash
# Install
brew install fnm

# Add to ~/.zshrc.local:
[[ -n "$(command -v fnm)" ]] && eval "$(fnm env --use-on-cd --shell zsh)"
```

### Option B: mise (Node + Python + Go + 100+ tools)

```bash
# Install
brew install mise

# Add to ~/.zshrc.local:
[[ -n "$(command -v mise)" ]] && eval "$(~/.local/bin/mise activate zsh 2>/dev/null || eval \"\$(mise activate zsh)\")"
```

**mise** uses `.node-version`, `.nvmrc`, `.python-version`, etc. Single tool for all runtimes.

---

## 3. Required Plugins (install in order)

### 3.1 fzf (required for fzf-tab)

```bash
brew install fzf
# Optional: install shell keybindings
$(brew --prefix)/opt/fzf/install  # follow prompts
```

### 3.2 fzf-tab (Tab completion with fzf)

```bash
mkdir -p ~/.zsh/plugins
git clone https://github.com/Aloxaf/fzf-tab ~/.zsh/plugins/fzf-tab
```

Add to `~/.zshrc.local` (after compinit):

```zsh
# fzf-tab: load after compinit, before autosuggestions
autoload -U compinit; compinit
[[ -f ~/.zsh/plugins/fzf-tab/fzf-tab.plugin.zsh ]] && source ~/.zsh/plugins/fzf-tab/fzf-tab.plugin.zsh
```

### 3.3 zsh-autosuggestions (optional, fast)

```bash
git clone https://github.com/zsh-users/zsh-autosuggestions ~/.zsh/plugins/zsh-autosuggestions
```

### 3.4 fast-syntax-highlighting (optional)

```bash
git clone https://github.com/zdharma-continuum/fast-syntax-highlighting ~/.zsh/plugins/fast-syntax-highlighting
```

---

## 4. Prompt: starship or powerlevel10k

### starship (cross-shell, minimal config)

```bash
brew install starship
```

Add to `~/.zshrc.local`:

```zsh
[[ -n "$(command -v starship)" ]] && eval "$(starship init zsh)"
```

### powerlevel10k (zsh-only, highly customizable)

```bash
git clone --depth=1 https://github.com/romkatv/powerlevel10k.git ~/.zsh/themes/powerlevel10k
```

Add to `~/.zshrc.local`:

```zsh
[[ -f ~/.zsh/themes/powerlevel10k/powerlevel10k.zsh-theme ]] && source ~/.zsh/themes/powerlevel10k/powerlevel10k.zsh-theme
```

---

## 5. find -q Error (macOS BSD find)

**Cause:** macOS uses BSD `find`; GNU `find` has `-q` (quiet). Scripts/plugins that use `find -q` fail.

**Fixes:**

1. **Use fd instead** (thegent prefers fd):

   ```bash
   brew install fd
   # fd has no -q; use fd ... 2>/dev/null for quiet
   ```

2. **Install GNU find** (if you need find -q):

   ```bash
   brew install findutils
   # Use gfind for GNU find
   ```

3. **Fix the script:** Replace `find -q` with `find` (remove -q) or `fd` equivalent.

---

## 6. Secret Setup (API keys, tokens)

**Never** put secrets in `~/.zshrc` or `~/.zshrc.local` if those files are shared or versioned.

**Recommended:**

1. **~/.zshrc.secrets** (create manually, add to .gitignore):

   ```zsh
   # Source from ~/.zshrc.local only if file exists
   [[ -f ~/.zshrc.secrets ]] && source ~/.zshrc.secrets
   ```

2. **~/.config/thegent/secrets.env** (if using thegent secret handling):
   - Use `thegent` or your tool's secret management
   - Source via `set -a; source ~/.config/thegent/secrets.env; set +a` in .zshrc.local

3. **1Password / pass / gopass** for CLI:
   ```bash
   brew install 1password-cli  # or pass, gopass
   ```

---

## 7. Full ~/.zshrc.local Template

See `shell/zshrc.local.template` in this repo. Copy to `~/.zshrc.local` and customize:

```bash
cp /path/to/thegent/shell/zshrc.local.template ~/.zshrc.local
```

---

## 8. Plugin Manager (optional): zinit or sheldon

If you prefer a manager over manual git clones:

### zinit (fast, popular)

```bash
bash -c "$(curl --fail --show-error --silent --location https://raw.githubusercontent.com/zdharma-continuum/zinit/HEAD/scripts/install.sh)"
```

Add to `~/.zshrc.local`:

```zsh
[[ -f "${HOME}/.local/share/zinit/zinit.git/zinit.zsh" ]] && source "${HOME}/.local/share/zinit/zinit.git/zinit.zsh"
# Then: zinit light Aloxaf/fzf-tab
```

### sheldon (Rust, lockfile, reproducible)

```bash
brew install sheldon
```

---

## 9. Proposed Custom Plugins (create if needed)

| Plugin idea           | Purpose                                                          | Effort |
| --------------------- | ---------------------------------------------------------------- | ------ |
| **thegent-prompt**    | Minimal prompt showing agent/session context when `AGENT_ID` set | Small  |
| **thegent-fd-find**   | Shell function: `find` → `fd` when safe (single path, no -exec)  | Small  |
| **thegent-mise-hook** | Auto `mise install` on `cd` when `.mise.toml` present            | Small  |

---

## 10. Verification

After setup:

```bash
# New terminal or: exec zsh

# Check Node (fnm/mise)
node -v

# Check fzf-tab (Tab on a partial path)
cd /usr && cd l<Tab>   # should show fzf menu

# Check no errors
# (no "no such file or directory" for zsh-nvm-x, prompt.zsh, etc.)
```

---

## 11. Migrating from Old Bundle (~/.zsh_bundle.zsh.broken)

If you have a backup of your previous 150KB bundle:

1. **Don't restore it** — it references missing files (zsh-nvm-x, prompt.zsh, etc.)
2. **Extract what you need** — grep for `source` lines to see which plugins you used
3. **Reinstall via this guide** — fnm/mise replaces nvm; fzf-tab, starship replace old plugins

---

## 12. Troubleshooting

| Error                           | Fix                                                                                                                                 |
| ------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `zsh-nvm-x-*.zsh: no such file` | You're using old bundle. Run `thegent install --target system --target user` to get minimal bundle. Plugins go in `~/.zshrc.local`. |
| `find: illegal option -- q`     | Remove `-q` from find call, or use `fd`, or install `findutils` and use `gfind`.                                                    |
| `prompt.zsh: no such file`      | Install starship or powerlevel10k; add to .zshrc.local.                                                                             |
| `fzf-tab` not working           | Ensure fzf installed; load fzf-tab **after** compinit.                                                                              |
| Slow startup                    | Use lazy loading: `zinit ice wait'1'` or defer plugin sourcing.                                                                     |

---

## 13. Cross-References

- [SETUP-RESTORE.md](../SETUP-RESTORE.md) — thegent shell restore
- [FIX_SHELL_CORRUPTION.md](./FIX_SHELL_CORRUPTION.md) — eval/ls corruption
- [shell/zshrc.local.template](../../shell/zshrc.local.template) — template file

---

## EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added practical implementation patterns
2. Added configuration examples
3. Enhanced cross-references to related documentation

### Cross-References Added

- Related research and implementation guides
- WORK_STREAM.md for tracking

### Practical Additions

- Implementation templates
- Configuration examples
- Best practices
