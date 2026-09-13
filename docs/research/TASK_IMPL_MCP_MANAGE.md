<DONE>
# Task: Consolidate os.environ in mcp_manage.py

**Priority**: P3
**Complexity**: MEDIUM
**Estimated Time**: 5 minutes
**Risk**: Low-Medium

---

## Summary

Replace 2 occurrences of `os.environ` access in `src/thegent/mcp_manage.py` with `ThegentSettings` dependency injection.

---

## File Details

**File**: `src/thegent/mcp_manage.py`
**Lines**: 166-167

```python
# BEFORE
if os.environ.get("VIRTUAL_ENV"):
    venv = Path(os.environ["VIRTUAL_ENV"])

# AFTER
if settings.virtual_env:
    venv = settings.virtual_env
```

---

## Step-by-Step Instructions

### 1. Identify the Function

Find the function containing lines 166-167. It should look like:

```python
def _build_virtualenv_hook(...):
    if os.environ.get("VIRTUAL_ENV"):
        venv = Path(os.environ["VIRTUAL_ENV"])
        # ... rest of function
```

### 2. Add Settings Parameter

Thread `ThegentSettings` through the function chain:

- Check if function is exported or called internally
- Add `settings: ThegentSettings` parameter to function signature
- Update all call sites to pass settings (or create at entry point)

### 3. Replace os.environ Access

```python
# BEFORE
if os.environ.get("VIRTUAL_ENV"):
    venv = Path(os.environ["VIRTUAL_ENV"])

# AFTER
if settings.virtual_env:
    venv = settings.virtual_env
```

### 4. Verify No Imports Needed

- `ThegentSettings` already imported at top of file
- `settings.virtual_env` auto-detects from `VIRTUAL_ENV` env var in validator
- No new imports needed

### 5. Test

- Verify function still detects virtual environment correctly
- Check that VIRTUAL_ENV env var is still read properly (via validator)
- Run: `python3 -m py_compile src/thegent/mcp_manage.py`

---

## Key Notes

1. **Virtual Env Auto-Detection**: The `ThegentSettings.virtual_env` field has a validator that reads from `os.environ["VIRTUAL_ENV"]` if not explicitly set. So the behavior is unchanged.

2. **Settings Injection**: ThegentSettings is already used in this file, so injecting it should be straightforward.

3. **Call Chain**: Check carefully where this function is called to ensure settings is available at all call sites.

---

## Verification

After completion, verify:

```bash
# Should not match this file (except if there are other usages)
grep "os\.environ\|os\.getenv" src/thegent/mcp_manage.py

# File should compile
python3 -m py_compile src/thegent/mcp_manage.py
```

---

## Related Settings Fields

- `ThegentSettings.virtual_env` (Path | None): Auto-detected from `VIRTUAL_ENV` env var
