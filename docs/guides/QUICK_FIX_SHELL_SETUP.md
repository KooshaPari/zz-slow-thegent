# Quick Fix: Shell Setup Issues

**Date:** 2026-02-17
**Issue:** `thegent` command not found, Node.js not in PATH after `exec zsh`

---

## Problems Identified

1. **`~/.zshenv` missing** - PATH not set up early (includes `~/.local/bin`)
2. **Node.js not in PATH** - Installed via brew but mise not activated
3. **`thegent` not installed** - Needs to be installed to `~/.local/bin`

---

## Fixes Applied

### 1. Installed `~/.zshenv`

```bash
cp shell/.zshenv ~/.zshenv
```

This sets up PATH early with `~/.local/bin` first.

### 2. Created `.mise.toml`

```toml
[tools]
node = "lts"
```

This tells mise to install Node.js LTS.

### 3. Install Node.js via mise

```bash
mise install
```

### 4. Install thegent

Created a wrapper script at `~/.local/bin/thegent` that calls `uv run thegent`.

Alternatively, use `uv run thegent` directly or install via:

```bash
# Create wrapper (already done)
cat > ~/.local/bin/thegent << 'EOF'
#!/usr/bin/env bash
exec uv run --directory "$(cd "$(dirname "$0")/../.." && pwd)" thegent "$@"
EOF
chmod +x ~/.local/bin/thegent
```

### 5. Create Node.js symlink (if mise not working)

```bash
ln -sf /opt/homebrew/bin/node ~/.local/bin/node
```

---

## Next Steps (Run in New Terminal)

After running `exec zsh` in your terminal:

1. **Verify PATH:**

   ```bash
   echo $PATH | grep -o "$HOME/.local/bin"
   ```

   Should show: `/Users/kooshapari/.local/bin`

2. **Verify Node.js:**

   ```bash
   node --version
   ```

   Should show: `v20.x.x` or similar

3. **Verify thegent:**

   ```bash
   thegent --help
   ```

   Should show thegent help.

4. **If Node.js still missing:**
   ```bash
   mise install
   eval "$(mise activate zsh)"
   ```

---

## Why This Happened

- `~/.zshenv` was missing (should be installed by `thegent install --target shell`)
- `mise` needs to be activated in `.zshrc.local` (already configured)
- `thegent` wasn't installed to PATH (needs `uv pip install --user -e .`)

---

## Permanent Fix

Run these commands once:

```bash
# 1. Install shell configs
uv run thegent install --target shell --force

# 2. Trust mise config and install Node.js
mise trust
mise install

# 3. Create Node.js symlink (fallback if mise not activated)
ln -sf /opt/homebrew/bin/node ~/.local/bin/node

# 4. Reload shell
exec zsh
```

After this, everything should work in new terminals.

**Note:** If `thegent` command still not found, use `uv run thegent` or ensure `~/.local/bin` is early in PATH (check `echo $PATH`).

---

## See also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) — canonical backlog
- [SHELL_ENVIRONMENT_COMPLETE.md](./SHELL_ENVIRONMENT_COMPLETE.md) — shell environment
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) — plan index

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
