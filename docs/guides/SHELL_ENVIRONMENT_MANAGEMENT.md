# Shell Environment Management

## Overview

thegent provides comprehensive shell environment management with safeguards against common issues. All shell configuration is centralized in `thegent/shell/` and installed via `thegent install`.

## Architecture

### Shell Configuration Files

1. **`.zshenv`** - System-wide environment (sourced first, always)
   - PATH setup
   - Environment variables
   - Early return for non-interactive/agent sessions

2. **`.zsh_bundle.zsh`** - Core utilities and aliases
   - Path-safe utilities (`qls`, `qfind`, `qgrep`)
   - Safe navigation (`cdq`)
   - Loads safeguards

3. **`.zsh_safeguards.zsh`** - Comprehensive protection (NEW)
   - Command aliasing safeguards (ls tree/recursive issues)
   - Fork explosion prevention
   - Timeout safeguards
   - Resource limits
   - Eval security helpers

4. **`.zshrc`** - User interactive shell config
   - Sources `.zshenv` and `.zsh_bundle.zsh`
   - User-specific customizations (via `.zshrc.local`)

### Installation Flow

```
thegent install --target system
  → Installs: .zshenv, .zsh_bundle.zsh, .zsh_safeguards.zsh

thegent install --target user
  → Installs: .zshrc
  → Creates: .zshrc.local (template)
```

## Safeguards

### 1. Command Aliasing Protection

**Problem**: Commands like `ls` get aliased to `lsd --tree` or similar, causing:

- Recursive tree output when single-level is expected
- Unwanted directories (node_modules, etc.) in output
- Performance issues

**Solution**:

- Detects problematic aliases (containing `--tree`, `-R`, `recursive`)
- Removes or overrides them
- Provides safe wrapper that ensures single-level output by default

**Example**:

```zsh
# Before safeguard: ls shows tree
$ ls
├── src/
│   ├── file1.py
│   └── file2.py
└── node_modules/  # unwanted!

# After safeguard: ls shows single-level
$ ls
src/  file1.py  file2.py
```

### 2. Fork Explosion Prevention

**Problem**: Scripts spawn too many processes, causing:

- `fork: Resource temporarily unavailable` errors
- System slowdown
- Process limit exhaustion

**Solution**:

- Sets `ulimit -u 4096` (max processes per user)
- Sets `ulimit -n 1024` (max open files)
- Sets `ulimit -v 4194304` (4GB virtual memory)
- Background monitor warns if process count > 3000

**Configuration**:

```zsh
# Limits are set automatically, but can be adjusted:
ulimit -u 8192  # Increase if needed
```

### 3. Timeout Safeguards

**Problem**: Commands hang indefinitely, especially:

- `find -exec` commands
- Network operations
- Long-running scripts

**Solution**:

- Wraps `find -exec` with 30s timeout
- Uses `gtimeout` on macOS, `timeout` on Linux
- Prevents infinite hangs

**Example**:

```zsh
# find -exec automatically gets 30s timeout
find . -name "*.py" -exec python {} \;
# If it hangs > 30s, it's killed automatically
```

### 4. Eval Security

**Problem**: `eval` executing file paths accidentally:

- `eval $(find ...)` executes file paths as commands
- `eval $(ls)` executes filenames
- Security risk

**Solution**:

- Provides `_thegent_safe_eval()` helper function
- Documents safe eval patterns
- Detects file paths in eval arguments

**Safe Pattern**:

```zsh
# ✅ Safe: Variable assignment
eval "$(command that outputs VAR=value)"

# ❌ Unsafe: File paths
eval "$(find . -type f)"  # DON'T DO THIS

# ✅ Safe alternative
find . -type f | while read f; do
  # process file
done
```

### 5. Resource Limits

**Problem**: Resource exhaustion from:

- Too many file descriptors
- Memory leaks
- Process accumulation

**Solution**:

- Sets reasonable defaults via `ulimit`
- Monitors resource usage
- Provides cleanup helpers

## Integration with Nix-Hybrid System

thegent's shell environment works seamlessly with nix:

1. **`.zshenv`** checks for nix and loads it first:

   ```zsh
   if has nix_direnv || has nix; then
     use flake
   fi
   ```

2. **PATH ordering**: thegent tools come after nix tools:

   ```zsh
   path=(
     "$HOME/.local/bin"  # thegent tools
     "/opt/homebrew/bin" # system tools
     $path               # nix tools (if loaded)
   )
   ```

3. **Safeguards work with nix**: All safeguards are nix-aware and don't interfere with nix shell environments.

## Customization

### User-Specific Config

Create `~/.zshrc.local` for user-specific customizations:

```zsh
# ~/.zshrc.local
# Your custom aliases, functions, etc.

alias myalias='command'
```

### Disabling Safeguards

If you need to disable safeguards temporarily:

```zsh
# Disable fork guard
unset THEGENT_FORK_GUARD_PID

# Disable ls wrapper
unalias ls 2>/dev/null || true
command ls "$@"
```

### Adjusting Limits

Modify limits in `~/.zshrc.local`:

```zsh
# Increase process limit
ulimit -u 8192

# Increase file descriptor limit
ulimit -n 2048
```

## Troubleshooting

### ls Still Shows Tree Output

1. Check for aliases: `alias ls`
2. Check for functions: `type ls`
3. Reload safeguards: `source ~/.zsh_safeguards.zsh`
4. Reinstall: `thegent install --target system --mode force`

### Fork Errors Persist

1. Check current limits: `ulimit -a`
2. Check process count: `ps -u $USER | wc -l`
3. Kill stuck processes: `pkill -f <pattern>`
4. Increase limit: `ulimit -u 8192`

### Timeouts Too Aggressive

1. Adjust timeout in safeguards file
2. Or use `command find` to bypass wrapper
3. Or set `THEGENT_TIMEOUT_DISABLED=1`

## Best Practices

1. **Always use `command ls`** in scripts to bypass aliases
2. **Use `_thegent_safe_eval()`** instead of `eval` when possible
3. **Set timeouts** for long-running commands
4. **Monitor resource usage** regularly
5. **Keep safeguards enabled** unless debugging

## Migration from Legacy Setup

If you have existing shell configs:

1. **Backup existing configs**:

   ```bash
   cp ~/.zshrc ~/.zshrc.backup
   cp ~/.zshenv ~/.zshenv.backup
   ```

2. **Install thegent shell config**:

   ```bash
   thegent install --target all --mode smart
   ```

3. **Merge customizations** into `~/.zshrc.local`

4. **Test** in a new terminal session

5. **Remove old configs** once verified

## Future Enhancements

- [ ] Cross-platform support (bash, fish)
- [ ] Configurable safeguard thresholds
- [ ] Per-project shell configs
- [ ] Shell config versioning
- [ ] Automatic cleanup of stale processes

---

## See also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) — canonical backlog
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

---

## 10. Troubleshooting Shell Issues

### 10.1 Common Issues

| Issue               | Symptom             | Solution                          |
| ------------------- | ------------------- | --------------------------------- |
| PATH corruption     | "command not found" | Check .zshenv sourcing            |
| Fork exhaustion     | "cannot fork"       | Restart terminal, check processes |
| Alias conflicts     | Unexpected behavior | Check `alias` output              |
| Slow startup        | Long .zshrc load    | Profile with `timezsh`            |
| Environment not set | Missing variables   | Check .zshenv content             |

### 10.2 Debug Commands

```bash
# Check shell configuration
cat ~/.zshenv
cat ~/.zshrc

# List aliases
alias

# Check PATH
echo $PATH

# Profile shell startup
timezsh

# Check sourcing order
zsh -xvic "exit" 2>&1 | head -100
```

### 10.3 Recovery Procedures

```bash
# Reset shell environment
rm ~/.zshenv ~/.zshrc
source shell/.zshenv
source shell/.zshrc

# Reset with backup
cp ~/.zshenv ~/.zshenv.bak
cp ~/.zshrc ~/.zshrc.bak
rm ~/.zshenv ~/.zshrc
thegent install --target user

# Emergency shell
exec bash  # Switch to bash temporarily
```

---

## 11. Extension Summary

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. **Added Section 10:** Troubleshooting Shell Issues
   - Common issues table
   - Debug commands
   - Recovery procedures

### Cross-References Added

- [FIX_SHELL_CORRUPTION.md](./FIX_SHELL_CORRUPTION.md)
- [FIX_SHELL_FORK_ERRORS.md](./FIX_SHELL_FORK_ERRORS.md)
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

### Practical Additions

- Troubleshooting table for common issues
- Debug commands for shell analysis
- Recovery procedures for emergencies
