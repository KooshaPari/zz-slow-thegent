<DONE>
# Friction Points Log - 2026-02-18

## Issue 2: WORK_STREAM.md Inconsistency

**Context**: `thegent plan do-next` returns "No pending items found" but BACKLOG has many unclaimed P2 items.

**Root Cause**:

- Agents completed P1 items (flash-swarm, free-swarm) and added to COMPLETED section
- BACKLOG still lists P1 items as available
- `thegent plan do-next` logic unclear - may be filtering by CLAIMED only, or confused by duplicate entries

**Evidence**:

```
BACKLOG:
| research-hook-rust-phase3 | Make ...gent-hooks default... | P1 | ... |
| research-hook-rust-phase4 | Native Rust hooks... | P2 | research-hook-rust-phase3 |

COMPLETED:
| research-hook-rust-phase3 | free-swarm | 2026-02-18T08:14:46.310287+00:00 |
```

**Impact**:

- Dependent P2 items (research-hook-rust-phase4) remain blocked
- P2 items with no dependencies (research-library-cache, etc.) not picked up
- Work stream stuck despite available work

**Fix Applied**:

- Cleaned up CLAIMED section (removed 5 completed flash-1 through flash-5 items)
- P2 items now should be discoverable

**Friction Type**: project
**Severity**: High
**Detection Method**: Work stream stuck, manual investigation required

## Issue 3: Missing Imports in install.py (moved from Issue 1)

**Context**: Running `thegent install` failed with `ImportError: cannot import name 'get_bundle_manifest_path' from 'thegent.install'`

**Root Cause**: `main.py` was importing functions from `install.py` that didn't exist:

- `get_bundle_manifest_path`
- `list_bundle_names`
- `validate_bundle_manifest`
- Missing `bundle_conflict_policy` parameter in `run_install()`

**Impact**:

- User-facing CLI error
- No indication of which functions were missing
- Required manual file exploration to understand the issue

**Fix Applied**:

1. Added `get_bundle_manifest_path(bundle_manifest=None)` with optional param
2. Added `list_bundle_names(bundle_manifest=None)`
3. Added `validate_bundle_manifest(bundle_manifest=None)`
4. Added `bundle_conflict_policy` parameter to `run_install()`

**Friction Type**: project
**Severity**: Medium
**Detection Method**: Runtime import error

## DX Improvements Identified

1. **Type Checking Gap**: pyright/mypy would have caught this at development time
   - Suggestion: Add pre-commit hook for type checking on changed files

2. **Import Validation**: No automated check that imported functions exist in source modules
   - Suggestion: Add CI step to verify all imports resolve

3. **Error Messages**: ImportError doesn't specify which module was being imported from
   - Current: `cannot import name 'X' from 'Y'`
   - Better: `main.py line N tries to import X from thegent.install but X is not defined in install.py`

4. **API Documentation Gap**: No clear API contract for install module
   - Suggestion: Add function signatures to docstrings or use autodoc

## Issue 3: RG/Grep Config Error

**Context**: Error `rg: error parsing flag -E: grep config error: unknown encoding: _proxy=|CURSOR_SANDBOX|...`

**Root Cause**: Unknown - likely shell alias or function wrapping rg/grep, or malformed config file

**Evidence**: Pattern `_proxy=|CURSOR_SANDBOX|SUDO_ASKPASS|CURSOR_ASKPASS` suggests environment variable filtering

**Impact**:

- Blocks search operations in some contexts
- Unclear source of error (environment-specific)
- Hard to reproduce consistently

**Fix Applied**:

1. Created `scripts/diagnose-rg-error.sh` - Diagnosis script to identify source:
   - Checks shell aliases for rg/grep
   - Checks shell functions
   - Checks environment variables
   - Tests rg and grep directly
   - Lists config files (.ripgreprc, .grep, etc.)

2. Created `scripts/safe-grep.sh` - Safe wrapper that bypasses aliases:
   - Uses `command -v` to get system binary paths
   - Allows choosing between rg and grep
   - Avoids shell alias/config interference

**Usage**:

```bash
# Run diagnosis
./scripts/diagnose-rg-error.sh

# Use safe grep/rg in scripts
source scripts/safe-grep.sh  # Then use 'safe-grep rg' or 'safe-grep grep'
```

**Friction Type**: environment
**Severity**: Medium
**Detection Method**: User-reported error in terminal output
**Status**: Workaround provided, root cause not identified (environment-specific)

## Related Work Items

- `research-library-retry` - Library-first migration (tenacity) for retry patterns
- `research-library-cache` - Library-first migration (cachetools) for caching patterns ✅ COMPLETED

## Status

Logged for future improvement. Workarounds provided. No immediate action required beyond this documentation.
