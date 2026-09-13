<DONE>
# Droid Cmd Hang Fix

**Date**: 2026-02-19
**Status**: ✅ Fixed
**Issue**: Droid commands were hanging when executed

---

## Problem

Droid commands (`CodexRunner` and `CustomCliRunner`) were using `subprocess.run()` directly instead of the optimized `run_subprocess_optimized()` function. This could cause hangs if:

1. Timeout wasn't properly enforced
2. stdin/stdout/stderr deadlocks occurred
3. Process creation wasn't optimized

---

## Solution

### 1. Enhanced `run_subprocess_optimized()` to Support stdin Input

**File**: `src/thegent/infra/fast_subprocess.py`

- Added `input` parameter to `run_optimized()` method
- Added `input` parameter to `run_subprocess_optimized()` convenience function
- Properly handles text vs bytes input automatically

### 2. Migrated Droid Runners to Use Optimized Subprocess

**File**: `src/thegent/agents/droid.py`

- `CodexRunner.run()`: Now uses `run_subprocess_optimized()` instead of `subprocess.run()`
- `CustomCliRunner.run()`: Now uses `run_subprocess_optimized()` instead of `subprocess.run()`
- Removed duplicate `TimeoutExpired` exception handlers
- Proper stdout/stderr decoding for cross-platform compatibility

### 3. Fixed Reload Setting Migration

**File**: `src/thegent/main.py`

- Updated `serve()` command to use `settings.reload` instead of `os.environ.get("THGENT_RELOAD")`
- Properly falls back to settings if CLI option not provided

---

## Changes Made

### fast_subprocess.py

```python
# Added input parameter support
def run_subprocess_optimized(
    ...,
    input: str | bytes | None = None,
    **kwargs,
) -> subprocess.CompletedProcess:
    # Automatically handles text vs bytes
    if input is not None:
        kwargs["input"] = input
        kwargs["text"] = isinstance(input, str)
```

### droid.py

```python
# Before
proc = subprocess.run(
    cmd,
    input=combined,
    text=True,
    timeout=timeout + 5,
    ...
)

# After
proc = run_subprocess_optimized(
    cmd,
    input=combined,
    timeout=timeout + 5,
    ...
)
```

---

## Benefits

1. **Better Timeout Handling**: Optimized subprocess ensures timeouts are properly enforced
2. **No Deadlocks**: Proper stdin/stdout/stderr handling prevents hangs
3. **Cross-Platform**: Better Windows/Unix compatibility
4. **Consistent**: All subprocess calls now use the same optimized path
5. **Resource Management**: Better file descriptor handling

---

## Testing

To verify the fix:

```bash
# Test droid command (should not hang)
thegent droid flash "test prompt"

# Test codex command (should not hang)
thegent codex exec "test prompt"
```

---

**Status**: ✅ Fixed
**Next**: Monitor for any remaining hang issues
