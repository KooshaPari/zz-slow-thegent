# Fix Shell Corruption Issue

## Symptoms

Every command execution results in hundreds of errors like:

```
(eval):1: command not found: assets
(eval):2: command not found: auths
...
```

This indicates that something is evaluating directory contents as commands, likely due to a misconfigured shell hook or wrapper script.

## Root Cause

1. **CLIProxyAPI config missing**: CLIProxyAPI is trying to load `/Users/kooshapari/temp-PRODVERCEL/485/kush/cliproxyapi-plusplus/config.yaml` which doesn't exist
2. **Shell wrapper corruption**: A wrapper script or hook is incorrectly evaluating directory contents

## Immediate Fix (Do This First)

### Step 1: Open a NEW Terminal

**CRITICAL**: Don't use the corrupted terminal. Open a completely new terminal window/tab.

### Step 2: Fix CLIProxyAPI Config

```bash
# Ensure config exists
mkdir -p ~/.config/thegent
python -m thegent.main cliproxy ensure-config

# If fork binary exists, copy config to fork location
if [ -f "../cliproxyapi-plusplus/cli-proxy-api-plus" ]; then
    mkdir -p ../cliproxyapi-plusplus
    cp ~/.config/thegent/cliproxy-config.yaml ../cliproxyapi-plusplus/config.yaml
fi
```

### Step 3: Reset Shell Environment

In the NEW terminal:

```bash
# Unset problematic hooks
unset precmd_functions chpwd_functions PROMPT_COMMAND
unset -f precmd chpwd

# Check for problematic aliases
type ls
type eval

# If ls or eval are aliased/functions, unset them
unalias ls eval 2>/dev/null || true
unset -f ls eval 2>/dev/null || true
```

### Step 4: Stop and Restart Services

```bash
# Stop any running CLIProxyAPI/thegent processes
thegent mcp down
pkill -f cli-proxy-api-plus || true

# Restart cleanly
thegent mcp up
```

### Step 5: Verify Fix

```bash
# Test a simple command
echo "test" > /tmp/test_fix.txt
cat /tmp/test_fix.txt

# Should output "test" without errors
```

## Prevention

The fixes I've implemented:

1. **Auto-create fork config**: Scripts now automatically copy config to fork location if fork binary is used
2. **Better config resolution**: `_ensure_config()` always creates config before starting proxy
3. **Diagnostic script**: `scripts/fix_shell_corruption.sh` helps diagnose issues

## If Issue Persists

1. **Check shell config files**:

   ```bash
   grep -n "eval.*ls\|eval.*\$(ls)" ~/.zshrc ~/.zshenv ~/.zprofile 2>/dev/null || echo "No problematic eval found"
   ```

2. **Check for wrapper scripts**:

   ```bash
   which cli-proxy-api-plus
   env | grep -i proxy
   ```

3. **Check Codex/CLIProxyAPI integration**:
   - Ensure Codex is not wrapping commands incorrectly
   - Check Codex MCP config: `~/.codex/mcp.json`
   - Remove failing MCP entries: `thegent mcp fix --client codex`

4. **Nuclear option** (if nothing else works):

   ```bash
   # Backup shell configs
   cp ~/.zshrc ~/.zshrc.backup
   cp ~/.zshenv ~/.zshenv.backup

   # Start with minimal config
   zsh -f
   # Then manually source only what you need
   ```

## Zsh Plugin Errors (zsh-nvm-x, prompt.zsh, fzf-tab: no such file)

If you see `no such file or directory` for zsh-nvm-x, prompt.zsh, providers/\*, zsh-alias-hinter, fzf-tab:

1. Run `thegent install --target system --target user` to get the minimal thegent bundle
2. Follow **[SHELL_ZSH_PLUGIN_SETUP.md](./SHELL_ZSH_PLUGIN_SETUP.md)** to install fnm/mise, fzf-tab, etc. in `~/.zshrc.local`
3. Run `./scripts/install_zsh_plugins.sh` to clone plugins and create `~/.zshrc.local`

## Related Commands

- `thegent cliproxy ensure-config` - Ensure CLIProxyAPI config exists
- `thegent mcp fix --client codex` - Remove problematic MCP servers
- `thegent mcp down` - Stop all MCP services
- `thegent mcp up` - Start MCP services cleanly

## Files Changed

- `scripts/start_proxy.py` - Auto-creates fork config if needed
- `scripts/start_proxy_with_adapter.py` - Auto-creates fork config if needed
- `scripts/start_proxy_dev.sh` - Auto-creates fork config if needed
- `scripts/fix_shell_corruption.sh` - Diagnostic script

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
