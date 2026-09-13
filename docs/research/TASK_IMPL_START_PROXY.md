<DONE>
# Task: Consolidate os.environ in start_proxy_with_adapter.py

**Priority**: P3
**Complexity**: MEDIUM
**Estimated Time**: 8 minutes
**Risk**: Medium (proxy startup behavior)

---

## Summary

Replace 5 occurrences of `os.environ` access in `scripts/start_proxy_with_adapter.py`:

1. Line 56: PATH lookup for binary search
2. Line 67: Environment copy for subprocess
3. Line 119: THGENT_DEBUG detection (field already exists!)
4. Line 120: THGENT_RELOAD detection (field already exists!)
5. Line 125: Set CLIPROXY backend URL

---

## File Details

**File**: `scripts/start_proxy_with_adapter.py`
**Lines**: 56, 67, 119, 120, 125

### Line 56: PATH Lookup

```python
# BEFORE
for segment in os.environ.get("PATH", "").split(":"):

# AFTER
path_str = os.environ.get("PATH", "")  # System var, keep as-is
for segment in path_str.split(":"):
# OR if PATH should be configurable, add to settings
```

### Line 67: Environment Copy

```python
# BEFORE
env = os.environ.copy()

# AFTER
env = os.environ.copy()  # Keep as-is - standard subprocess setup
```

### Line 119: THGENT_DEBUG

```python
# BEFORE
log_level = "debug" if os.environ.get("THGENT_DEBUG") == "1" else "info"

# AFTER
log_level = "debug" if settings.debug else "info"
```

### Line 120: THGENT_RELOAD

```python
# BEFORE
reload = os.environ.get("THGENT_RELOAD") == "1"

# AFTER
reload = settings.reload
```

### Line 125: Set Backend URL

```python
# BEFORE
os.environ["THGENT_CLIPROXY_BACKEND_URL"] = backend_url

# AFTER
if settings.cliproxy_backend_url:
    backend_url = settings.cliproxy_backend_url
else:
    backend_url = "http://127.0.0.1:8000"  # default
env["THGENT_CLIPROXY_BACKEND_URL"] = backend_url
```

---

## Step-by-Step Instructions

### 1. Check Current Structure

This is a script (not a module), so may need:

- Import ThegentSettings
- Create settings instance at entry point
- Or refactor to accept settings parameter

### 2. Add Settings Import and Instantiation

```python
from thegent.config import ThegentSettings


def main():
    settings = ThegentSettings()
    # ... rest of main
```

### 3. Replace Each Occurrence

**Line 56 (PATH lookup)**:
Keep as-is - system environment variable, read-only:

```python
for segment in os.environ.get("PATH", "").split(":"):
    # ... binary search logic
```

**Line 67 (env copy)**:
Keep as-is - standard subprocess setup:

```python
env = os.environ.copy()
```

**Line 119 (THGENT_DEBUG)**:

```python
# BEFORE
log_level = "debug" if os.environ.get("THGENT_DEBUG") == "1" else "info"

# AFTER
log_level = "debug" if settings.debug else "info"
```

**Line 120 (THGENT_RELOAD)**:

```python
# BEFORE
reload = os.environ.get("THGENT_RELOAD") == "1"

# AFTER
reload = settings.reload
```

**Line 125 (Backend URL)**:

```python
# BEFORE
os.environ["THGENT_CLIPROXY_BACKEND_URL"] = backend_url

# AFTER
if settings.cliproxy_backend_url:
    backend_url = settings.cliproxy_backend_url
# Pass to subprocess via env dict
env["THGENT_CLIPROXY_BACKEND_URL"] = backend_url
```

### 4. Verify Settings Field Availability

- `settings.debug`: ✅ Already exists in ThegentSettings
- `settings.reload`: ✅ Already exists in ThegentSettings
- `settings.cliproxy_backend_url`: ✅ Added as part of this consolidation

### 5. Test

- Verify script still starts proxy correctly
- Check debug/reload flags work: `THGENT_DEBUG=1 start_proxy_with_adapter.py`
- Run: `python3 -m py_compile scripts/start_proxy_with_adapter.py`

---

## Key Notes

1. **Settings Fields Already Exist**: `debug` and `reload` are already in ThegentSettings, so changes are straightforward.

2. **System Variables**: PATH is system environment and should be kept as-is (read from os.environ).

3. **Backend URL**: New field added to ThegentSettings; use via `settings.cliproxy_backend_url`.

4. **Script vs Module**: This is a script, so may need to instantiate ThegentSettings. Check entry point (usually `if __name__ == "__main__":`).

5. **Environment Dict**: Pass env vars to subprocess via env dict, not global os.environ mutations.

---

## Verification

After completion:

```bash
# Should return ZERO matches
grep "os\.environ\[\"THGENT" scripts/start_proxy_with_adapter.py

# Syntax check
python3 -m py_compile scripts/start_proxy_with_adapter.py

# Test script execution
python scripts/start_proxy_with_adapter.py --help
```

---

## Related Settings Fields

- `ThegentSettings.debug` (bool, default=False): Debug logging flag (THGENT_DEBUG=1)
- `ThegentSettings.reload` (bool, default=False): Auto-reload flag (THGENT_RELOAD=1)
- `ThegentSettings.cliproxy_backend_url` (str | None): Backend URL for proxy (THGENT_CLIPROXY_BACKEND_URL)
