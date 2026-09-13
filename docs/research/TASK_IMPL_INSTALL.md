<DONE>
# Task: Consolidate os.environ in install.py

**Priority**: P3
**Complexity**: HIGH
**Estimated Time**: 15 minutes
**Risk**: HIGH (critical installer path; test on all platforms)

---

## Summary

Replace 5 occurrences of `os.environ` access in `src/thegent/install.py`:

1. Line 251: PATH mutation for installer
2. Line 309: SHELL detection
3. Line 397: SHELL detection
4. Line 437: SHELL detection
5. Line 1686: APPDATA detection (Windows)

---

## File Details

**File**: `src/thegent/install.py`
**Lines**: 251, 309, 397, 437, 1686

### Line 251: PATH Mutation

```python
# BEFORE
os.environ["PATH"] = f"{brew_path}:{os.environ.get('PATH', '')}"

# AFTER
# Avoid global mutation
env = os.environ.copy()
env["PATH"] = f"{brew_path}:{os.environ.get('PATH', '')}"
# Pass env dict to subprocess instead
```

### Lines 309, 397, 437: SHELL Detection

```python
# BEFORE (3x)
shell = os.environ.get("SHELL", "/bin/zsh")

# AFTER (3x)
shell = settings.shell_path  # Auto-detected from SHELL env var
```

### Line 1686: APPDATA Detection (Windows)

```python
# BEFORE
p = Path(os.environ.get("APPDATA", "")) / "Claude" / "claude_desktop_config.json"

# AFTER
if settings.appdata_path:
    p = settings.appdata_path / "Claude" / "claude_desktop_config.json"
else:
    p = Path.home() / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"
```

---

## Step-by-Step Instructions

### 1. Identify Function/Method Scope

- Find each occurrence and understand its context
- Line 251: Inside installer setup function (PATH for brew)
- Lines 309, 397, 437: Multiple shell detection calls
- Line 1686: Windows config path setup

### 2. Add Settings Parameter

If `settings` not already in function scope:

```python
def install_xyz(settings: ThegentSettings, ...):
    # Function body
```

### 3. Replace Each Occurrence

**Line 251 (PATH mutation)**:

```python
# Option A: Avoid mutation, use env dict for subprocess
env = os.environ.copy()
env["PATH"] = f"{brew_path}:{os.environ.get('PATH', '')}"
# Pass env to subprocess call that follows

# Option B: If PATH must be set for remainder of function
# Only do this if necessary; prefer Option A
# env_backup = os.environ.get('PATH')
# try:
#     os.environ["PATH"] = f"{brew_path}:{env_backup}"
#     # ... installer logic
# finally:
#     if env_backup:
#         os.environ["PATH"] = env_backup
```

**Lines 309, 397, 437 (SHELL detection)** - Straightforward:

```python
# BEFORE
shell = os.environ.get("SHELL", "/bin/zsh")

# AFTER
shell = settings.shell_path
```

**Line 1686 (APPDATA detection)** - Windows-specific:

```python
# BEFORE
p = Path(os.environ.get("APPDATA", "")) / "Claude" / "claude_desktop_config.json"

# AFTER
if settings.appdata_path:
    p = settings.appdata_path / "Claude" / "claude_desktop_config.json"
else:
    # Fallback for non-Windows or when APPDATA not set
    p = Path.home() / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"
```

### 4. Verify Settings Availability

- Check if settings is injected at function entry point
- Install.py may have an `install()` or `main()` function that creates settings
- Ensure settings is passed through call chain

### 5. Test (CRITICAL for installer)

- **macOS**: Verify shell detection works (`/bin/zsh` or `/bin/bash`)
- **Windows**: Verify APPDATA path resolution
- **Linux**: Verify shell detection works
- Run: `python3 -m py_compile src/thegent/install.py`
- Actual installer testing: `thegent install` on each platform

---

## Key Notes

1. **Installer Critical Path**: This is production-critical code. Test thoroughly on all platforms.

2. **PATH Mutation**: The global PATH mutation on line 251 affects all subsequent code. Prefer passing env dict to subprocess instead.

3. **Shell Detection**: Most important change - directly impacts user experience on different shells.

4. **Windows vs Unix**: APPDATA is Windows-only. Provide sensible fallback for other platforms.

5. **Settings Validators**: All env var detection is handled by ThegentSettings validators:
   - `shell_path` auto-detects from `SHELL`
   - `appdata_path` auto-detects from `APPDATA`
   - No manual env reading needed in install.py

---

## Verification

After completion:

```bash
# Should return ZERO matches
grep "os\.environ\|os\.getenv" src/thegent/install.py

# Syntax check
python3 -m py_compile src/thegent/install.py

# Test on all platforms
# macOS:
thegent install --dry-run
# Windows:
# (if available)
# Linux:
thegent install --dry-run
```

---

## Related Settings Fields

- `ThegentSettings.shell_path` (str, default="/bin/zsh"): Auto-detected from SHELL env var
- `ThegentSettings.appdata_path` (Path | None): Auto-detected from APPDATA env var
- `ThegentSettings.cliproxy_binary` (str): May be relevant for install setup

---

## Platform-Specific Considerations

| Platform | Env Var | Field        | Notes                             |
| -------- | ------- | ------------ | --------------------------------- |
| macOS    | SHELL   | shell_path   | Usually `/bin/zsh` or `/bin/bash` |
| Windows  | APPDATA | appdata_path | Required for Claude config paths  |
| Linux    | SHELL   | shell_path   | Usually `/bin/bash` or `/bin/zsh` |
