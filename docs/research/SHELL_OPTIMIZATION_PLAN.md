<DONE>
# Shell Optimization Plan - Use zsh (Fastest Shell)

**Date:** 2026-02-18  
**Priority:** P1  
**Status:** Planning  
**Issue:** Bash processes appearing, zsh commands slow, need optimization

## Problem Statement

1. **Bash processes in Activity Monitor** - Unnecessary bash processes running
2. **Slow zsh commands** - `chmod` and other commands seem slow
3. **Need optimization** - All terminal invocations should use zsh (or fastest possible shell)

## Performance Comparison

```bash
# Benchmark results:
zsh -c 'echo test'  0.00s user 0.00s system 39% cpu 0.012 total
bash -c 'echo test'  0.00s user 0.00s system 32% cpu 0.023 total

# zsh is ~2x faster than bash (0.012s vs 0.023s)
```

## Current Issues

### Issue 1: Bash Processes from Hooks

```bash
# Found bash processes:
bash /Users/kooshapari/.claude/hooks/task-completion-verifier.sh
bash /Users/kooshapari/.claude/hooks/quality-gate.sh
```

**Solution:** Update hooks to use zsh explicitly

### Issue 2: Subprocess Calls May Default to Bash

Thegent subprocess calls may not specify shell explicitly, defaulting to system default or bash.

**Solution:** Explicitly use zsh in all subprocess calls

## Implementation Strategy

### Phase 1: Detect Shell Usage

Find all subprocess calls that use shells:

```python
# Search for:
- subprocess.run(..., shell=True)
- subprocess.Popen(..., shell=True)
- subprocess.call(..., shell=True)
- Any shell=True without explicit executable
```

### Phase 2: Optimize Shell Selection

**Strategy:**

1. Detect fastest available shell (zsh > bash > sh)
2. Use zsh explicitly in all subprocess calls
3. Cache shell path to avoid repeated lookups

**Code Pattern:**

```python
import shutil
import os


def get_fastest_shell() -> str:
    """Get fastest available shell (zsh > bash > sh)."""
    # Check in order of preference
    for shell in ["/bin/zsh", "/usr/bin/zsh", "zsh"]:
        if shutil.which(shell):
            return shell
    for shell in ["/bin/bash", "/usr/bin/bash", "bash"]:
        if shutil.which(shell):
            return shell
    return "/bin/sh"  # Fallback


FASTEST_SHELL = get_fastest_shell()

# Use in subprocess calls:
subprocess.run(cmd, shell=True, executable=FASTEST_SHELL)
```

### Phase 3: Update Hook Scripts

Update `.claude/hooks/*.sh` to use zsh:

```bash
#!/bin/zsh
# Instead of: #!/bin/bash
```

### Phase 4: Optimize zsh Startup

**Issue:** zsh startup may be slow due to:

- Heavy `.zshrc` loading
- Plugin initialization
- Environment setup

**Solution:** Use `-c` flag for non-interactive commands (already done, but verify)

## Files to Modify

### 1. Core Subprocess Calls

- `thegent/src/thegent/agents/cliproxy_manager.py` - Proxy management
- `thegent/src/thegent/cli.py` - CLI commands
- `thegent/src/thegent/dex_main.py` - Dex commands
- `thegent/src/thegent/tools/terminal.py` - Terminal tools
- Any file using `subprocess.run(..., shell=True)`

### 2. Hook Scripts

- `~/.claude/hooks/task-completion-verifier.sh`
- `~/.claude/hooks/quality-gate.sh`
- Any other hook scripts

### 3. Configuration

- Add shell preference to config
- Cache shell path
- Add shell detection utility

## Implementation Code

### Shell Utility Module

```python
# thegent/src/thegent/utils/shell.py

import shutil
import os
from pathlib import Path
from typing import Optional

_FASTEST_SHELL: Optional[str] = None


def get_fastest_shell() -> str:
    """
    Get fastest available shell.
    Priority: zsh > bash > sh
    """
    global _FASTEST_SHELL

    if _FASTEST_SHELL:
        return _FASTEST_SHELL

    # Check zsh first (fastest)
    for zsh_path in ["/bin/zsh", "/usr/bin/zsh"]:
        if Path(zsh_path).exists():
            _FASTEST_SHELL = zsh_path
            return _FASTEST_SHELL

    # Check zsh via which
    zsh = shutil.which("zsh")
    if zsh:
        _FASTEST_SHELL = zsh
        return _FASTEST_SHELL

    # Fallback to bash
    for bash_path in ["/bin/bash", "/usr/bin/bash"]:
        if Path(bash_path).exists():
            _FASTEST_SHELL = bash_path
            return _FASTEST_SHELL

    bash = shutil.which("bash")
    if bash:
        _FASTEST_SHELL = bash
        return _FASTEST_SHELL

    # Final fallback
    _FASTEST_SHELL = "/bin/sh"
    return _FASTEST_SHELL


def run_shell_command(cmd: str, **kwargs) -> subprocess.CompletedProcess:
    """
    Run shell command using fastest available shell.

    Args:
        cmd: Command string to execute
        **kwargs: Additional subprocess.run arguments

    Returns:
        CompletedProcess result
    """
    import subprocess

    shell = kwargs.pop("executable", None) or get_fastest_shell()
    return subprocess.run(cmd, shell=True, executable=shell, **kwargs)
```

### Update Subprocess Calls

```python
# Before:
subprocess.run(cmd, shell=True)

# After:
from thegent.utils.shell import run_shell_command

run_shell_command(cmd)
# Or:
subprocess.run(cmd, shell=True, executable=get_fastest_shell())
```

## Configuration

### Environment Variable

```bash
# Override shell preference
THGENT_SHELL=/bin/zsh  # Force zsh
THGENT_SHELL=/bin/bash  # Force bash
```

### Config File

```yaml
# ~/.config/thegent/config.yaml
shell:
  preferred: "zsh" # zsh, bash, or auto
  path: "/bin/zsh" # Override path
  optimize_startup: true # Skip heavy .zshrc for non-interactive
```

## Performance Optimizations

### 1. Skip Heavy zshrc for Non-Interactive

```python
# Use zsh with minimal initialization
subprocess.run(
    cmd,
    shell=True,
    executable="/bin/zsh",
    env={**os.environ, "ZDOTDIR": "/dev/null"},  # Skip .zshrc
)
```

### 2. Cache Shell Path

Cache shell path lookup to avoid repeated `which` calls.

### 3. Use Direct Paths

Use direct paths (`/bin/zsh`) instead of `which` lookups when possible.

## Testing

### Benchmark Shell Performance

```bash
# Test shell startup time
time zsh -c 'echo test'
time bash -c 'echo test'
time sh -c 'echo test'

# Test with heavy .zshrc
time zsh -c 'echo test'  # With .zshrc
time ZDOTDIR=/dev/null zsh -c 'echo test'  # Without .zshrc
```

### Verify No Bash Processes

```bash
# After optimization, verify no bash processes
ps aux | grep bash | grep -v grep
# Should be minimal or zero
```

## Migration Path

1. **Phase 1:** Add shell utility module
2. **Phase 2:** Update core subprocess calls
3. **Phase 3:** Update hook scripts
4. **Phase 4:** Add configuration options
5. **Phase 5:** Optimize zsh startup

## Expected Benefits

- **Faster command execution:** ~2x faster (zsh vs bash)
- **Reduced bash processes:** Eliminate unnecessary bash usage
- **Better performance:** Optimized shell selection
- **Consistency:** All commands use same fast shell

## Next Steps

1. ✅ **Document:** Create optimization plan
2. ⏭️ **Implement:** Add shell utility module
3. ⏭️ **Update:** Modify subprocess calls
4. ⏭️ **Test:** Verify performance improvement
5. ⏭️ **Deploy:** Roll out optimization
