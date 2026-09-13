# Shell Startup Optimization - mise Migration

## Problem

Shell startup was taking 2217 seconds (36+ minutes) due to direnv loading `.envrc` files.

## Root Causes

1. **direnv loading `.envrc`**: Even with mise configured, direnv was still loading `.envrc` files
2. **No early exit**: `.envrc` didn't exit fast enough when mise was active
3. **Missing mise hooks**: mise shell hooks weren't automatically installed
4. **Starship timeout**: Starship timing out on `/opt/homebrew/bin/bun` command

## Solutions Implemented

### 1. Optimized `.envrc` for Fast Exit

- Added early exit checks before any slow operations
- Check for `MISE_ENV` environment variable first
- Check for `.mise.toml` file existence
- Exit immediately if mise should handle the directory
- Only fall back to direnv/venv if mise is not available

### 2. mise Shell Hook Auto-Installation

- `thegent install --system-deps` now automatically installs mise hooks
- Hooks are added to `.zshenv` (preferred) or `.zshrc`
- mise hooks are placed BEFORE direnv hooks to ensure precedence
- Sets `MISE_ENV=1` so direnv knows to skip

### 3. Shell Template Updates

- Updated `shell/.zshenv` template to:
  - Load mise FIRST before direnv
  - Set `MISE_ENV=1` after mise activation
  - Only load direnv if `MISE_ENV` is not set
  - Skip both in non-interactive shells

### 4. Starship Timeout Fix

- Starship timeout can be configured in `~/.config/starship.toml`:
  ```toml
  [cmd_duration]
  command_timeout = 2000  # Increase from default 1000ms
  ```

## Usage

### Install mise and Configure Hooks

```bash
# Install mise and auto-configure shell hooks
thegent install --system-deps

# Or use Nix
thegent install --system-deps --nix
```

### Verify mise is Active

```bash
# Check if mise is handling the directory
echo $MISE_ENV  # Should output "1" if mise is active

# Check mise status
mise doctor
```

### Manual Hook Installation

If hooks weren't auto-installed, add to `~/.zshenv`:

```zsh
# mise hook (fast alternative to direnv)
if command -v mise >/dev/null 2>&1 && [[ -n "${PS1:-}" || -t 0 ]]; then
  eval "$(mise activate zsh)" 2>/dev/null || true
  export MISE_ENV=1
fi
```

## Expected Performance

- **Before**: 2217 seconds (36+ minutes)
- **After**: < 1 second (mise loads instantly)

## Migration Checklist

- [x] Optimize `.envrc` for fast exit
- [x] Add mise hook auto-installation
- [x] Update shell templates
- [x] Ensure mise takes precedence over direnv
- [ ] Fix starship timeout (user needs to configure `command_timeout`)

## Long-term Plan

1. **Phase 1** (Current): Hybrid approach - mise preferred, direnv fallback
2. **Phase 2**: Remove direnv entirely, use only mise
3. **Phase 3**: Optimize all shell startup scripts for sub-second load times
