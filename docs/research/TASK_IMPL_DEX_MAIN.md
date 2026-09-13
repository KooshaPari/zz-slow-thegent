<DONE>
# Task: Consolidate os.environ in dex_main.py

**Priority**: P3
**Complexity**: MEDIUM-HIGH
**Estimated Time**: 8 minutes
**Risk**: Medium (behavioral impact on subprocess setup)

---

## Summary

Replace 3 occurrences of `os.environ` access in `src/thegent/dex_main.py`:

1. Remove env mutation for THGENT_CLIPROXY_ADAPTER
2. Use settings for subprocess env setup
3. Use settings for cliproxy_backend_url

---

## File Details

**File**: `src/thegent/dex_main.py`
**Lines**: 173, 211, 219

### Line 173: Environment Mutation

```python
# BEFORE
os.environ["THGENT_CLIPROXY_ADAPTER"] = "1"

# AFTER
# Move to subprocess env setup (line 211)
# Pass via settings or explicit env dict
```

### Line 211: Subprocess Env Setup

```python
# BEFORE
env = os.environ.copy()

# AFTER
env = os.environ.copy()
env["THGENT_CLIPROXY_ADAPTER"] = "1"  # Set explicitly for subprocess
if settings.cliproxy_backend_url:
    env["THGENT_CLIPROXY_BACKEND_URL"] = settings.cliproxy_backend_url
```

### Line 219: PATH Access

```python
# BEFORE
path = os.environ.get("PATH", "")

# AFTER
path = os.environ.get("PATH", "")  # System var, read-only; keep as-is
# OR
# Store PATH in settings if frequently used
```

---

## Step-by-Step Instructions

### 1. Understand Current Behavior

- Line 173 mutates os.environ globally
- Line 211 copies os.environ for subprocess
- Line 219 reads PATH for subprocess search

### 2. Refactor Environment Mutation

**Remove line 173 global mutation**. Instead:

```python
# At line 211 (subprocess env setup):
env = os.environ.copy()
env["THGENT_CLIPROXY_ADAPTER"] = "1"  # Set for THIS subprocess only
```

### 3. Add Cliproxy Backend URL Support

At line 211, after cliproxy adapter setup:

```python
if settings.cliproxy_backend_url:
    env["THGENT_CLIPROXY_BACKEND_URL"] = settings.cliproxy_backend_url
```

### 4. Handle PATH Access

Option A (Recommended): Keep as-is (system env var, read-only)

```python
path = os.environ.get("PATH", "")
```

Option B: Thread through settings if needed later

```python
# Add to ThegentSettings if frequently used
# For now, keep reading from os.environ for system PATH
```

### 5. Verify Settings Parameter

- Ensure `settings` parameter is available in function scope
- If not, thread through function signature
- ThegentSettings already imported and used in dex_main.py

### 6. Test

- Verify DEX CLI still works: `thegent dex --help`
- Check that subprocess receives correct env vars
- Run: `python3 -m py_compile src/thegent/dex_main.py`

---

## Key Notes

1. **Environment Mutation**: Avoid global `os.environ` mutations when possible. Pass env vars explicitly via subprocess env dict.

2. **System Variables**: PATH is a system environment variable and should be read from os.environ (or settings). Keeping line 219 as-is is acceptable.

3. **Subprocess Isolation**: Passing env vars via subprocess env dict (line 211) isolates changes to that process only, preventing side effects.

4. **Settings Field**: `settings.cliproxy_backend_url` is new field added to ThegentSettings with default None.

---

## Verification

After completion:

```bash
# Should not match (except system PATH read)
grep "os\.environ\[\"THGENT" src/thegent/dex_main.py

# Syntax check
python3 -m py_compile src/thegent/dex_main.py

# DEX CLI should work
thegent dex --help
```

---

## Related Settings Fields

- `ThegentSettings.cliproxy_backend_url` (str | None): For proxy backend setup
- `ThegentSettings.cliproxy_adapter` (bool): Already exists; set to True globally if needed
