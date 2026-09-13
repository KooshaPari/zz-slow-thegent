# CLI Tests Root Cause Analysis

## Executive Summary

The WL-124 refactoring split large CLI modules into smaller ones, but broke the test patching infrastructure. Tests fail because they patch functions at locations that no longer match where functions are actually called from.

## Root Cause: Python Import & Patching Mechanics

### How Python Imports Work

```python
# In plan_dag_cmds.py
from thegent.cli.commands.dag_impl_ops import dag_recover_impl

# This creates a LOCAL reference in plan_dag_cmds module
def dag_recover_cmd(...):
    dag_recover_impl(...)  # Calls LOCAL reference
```

### How Test Patching Works

```python
# Test patches at the module where function is DEFINED
@patch("thegent.cli.commands.dag_impl_ops._dag_path", return_value=...)
# NOT where it's CALLED from
```

### The Problem

- **Before WL-124**: Functions were in `impl.py`, tests patched `thegent.cli._dag_path`
- **After WL-124**: Functions moved to `dag_impl_ops.py`, tests still patch old locations
- **Result**: Patches don't intercept the calls because they're patching the wrong module

## Failure Categories

### Category 1: dag_recover_cmd tests (5 failures)

- **Test patches**: `thegent.cli._dag_path` / `thegent.cli.commands.dag_impl_ops._dag_path`
- **Command calls**: `dag_recover_impl()` directly (local import)
- **Fix needed**: Command must call via `thegent.cli.dag_recover_impl()` or similar

### Category 2: dag_run_cmd tests (3 failures)

- **Test patches**: `thegent.cli._dag_path`
- **Command calls**: `dag_run_impl()` directly
- **Same issue as Category 1**

### Category 3: dag_sync_cmd ambiguous_cwd (1 failure)

- **Test patches**: `thegent.cli._resolve_cwd`
- **Command/impl calls**: Uses lazy import from `_cli_shared`
- **Issue**: Patch location mismatch

### Category 4: Escalate tests (2 failures)

- **Root cause**: Tests patch `services.governance` but commands import from `impl`

### Category 5: DataProtection tests (2 failures)

- **Root cause**: `data_protection_cmd` doesn't exist in exports

### Category 6: SessionContractHealth tests (1 failure)

- **Root cause**: Mock assertion failures on helper functions

### Category 7: SerializeHealthTrend test (1 failure)

- **Root cause**: Different issue, needs investigation

## Solutions

### Solution A: Fix Commands to Call via Namespace (Recommended)

Make commands call functions through `thegent.cli` namespace so tests can patch them:

```python
# Instead of:
from thegent.cli.commands.dag_impl_ops import dag_recover_impl
def dag_recover_cmd(...):
    dag_recover_impl(...)  # Local call - can't patch!

# Do:
def dag_recover_cmd(...):
    from thegent.cli import dag_recover_impl
    dag_recover_impl(...)  # Can patch thegent.cli.dag_recover_impl
```

### Solution B: Fix All Test Patches

Update every test to patch the correct module where functions are defined:

- `_dag_path` → `thegent.cli.commands.dag_impl_ops._dag_path`
- `dag_run_impl` → `thegent.cli.commands.dag_impl_ops.dag_run_impl`
- etc.

**Problem**: This is fragile and breaks with any refactoring.

### Solution C: Hybrid Approach

1. Fix commands that delegate (like `dag_cancel_cmd`) to use namespace calls
2. Fix lazy imports in `_cli_shared` to point to correct modules
3. Accept some test failures as known issues until full rewrite

## Current Status

- **Working tests**: 95 passed
- **Broken tests**: 15 failing
- **Root cause**: WL-124 module split without updating import/patch patterns

## Recommendation

**Solution A** is the cleanest long-term fix but requires changes to multiple command files. Given time constraints, recommend:

1. Document known issues in GitHub issue
2. Focus on fixing critical test failures only
3. Leave remaining 15 as technical debt for proper namespace refactor

## Files Affected

- `src/thegent/cli/commands/plan_dag_cmds.py`
- `src/thegent/cli/commands/_cli_shared.py`
- `src/thegent/cli/commands/dag_impl_ops.py`
- `tests/test_unit_cli_commands_b.py`
