# Backwards Compatibility & Legacy Code Audit

**Date:** February 19, 2026
**Status:** Initial Audit Complete
**Next Action:** Removal Plan Execution

---

## 🎯 Audit Scope

**Objective:** Identify all backwards compatibility, legacy, fallback, and deprecated patterns that should be removed given zero user debt.

**Methodology:**

- Pattern search: `deprecated`, `legacy`, `backward`, `compat`, `fallback`
- Directory analysis: `cli/legacy/`, `*_legacy.py`, `*_deprecated.py`
- Import analysis: Backward compat shims
- Backup file detection: `*.backup`, `.env-backup-*`

---

## 📊 Findings Summary

| Category                     | Count    | Status | Priority |
| ---------------------------- | -------- | ------ | -------- |
| **Legacy Directories**       | 1        | Found  | P1       |
| **Deprecated Files**         | 3+       | Found  | P1       |
| **Backward Compat Patterns** | 5+       | Found  | P1       |
| **Import Fallbacks**         | 2+       | Found  | P2       |
| **Backup Files**             | 10+      | Found  | P3       |
| **Archive Directories**      | Multiple | Found  | P3       |

---

## 🔍 Detailed Findings

### 1. Legacy CLI Directory ⚠️ **P1 - REMOVE**

**Location:** `src/thegent/cli/legacy/`

**Files Found:**

- `cli_legacy.py`
- `cli_impl.py`
- `cli_sync.py`
- `cli_teammates.py`
- `cli_swarm.py`
- `cli_linkcheck.py`
- `cli_initiative.py`
- `cli_git.py`
- `cli_document_queue.py`
- `cli_custom.py`
- `cli_crew.py`
- `cli_concurrency.py`
- `cli_commands_shared_servers.py`
- `__init__.py`

**Status:**

- ✅ Already migrated to use `ThegentSettings` (no `os.environ` fallbacks)
- ⚠️ Still exists as separate directory
- ⚠️ May have callers still importing from `cli.legacy`

**Action:**

1. Find all imports: `grep -r "from.*cli.legacy\|import.*cli.legacy" src/`
2. Update callers to use `cli.apps` or `cli.commands`
3. Delete `cli/legacy/` directory entirely
4. Update tests

**Rationale:** No user debt = no need for legacy CLI

---

### 2. Deprecated Tool Stubs (atoms-mcp-prod) ⚠️ **P1 - REMOVE**

**Locations:**

- `atoms-mcp-prod/src/atoms_mcp/tools/compliance_verification.py`
- `atoms-mcp-prod/src/atoms_mcp/tools/duplicate_detection.py`
- `atoms-mcp-prod/src/atoms_mcp/tools/entity_resolver.py`
- `atoms-mcp-prod/src/atoms_mcp/tools/admin.py`
- `atoms-mcp-prod/src/atoms_mcp/tools/context.py`

**Pattern:**

```python
"""Tool - DEPRECATED.

This module is deprecated. Use tools.entity_modules.operations instead.
"""

import warnings
from .entity_modules.operations import EntityOperations

warnings.warn("...", DeprecationWarning)

# Re-export for backward compatibility
ComplianceVerificationTool = EntityOperations
```

**Status:**

- ⚠️ Backward-compat stubs with deprecation warnings
- ⚠️ Functionality integrated into canonical implementations
- ⚠️ Still imported by test files (76+ test files)

**Action:**

1. Update all test files to import from canonical location
2. Remove stub files entirely
3. Remove deprecation warnings (no longer needed)

**Rationale:** Zero user debt = immediate removal, no deprecation period

---

### 3. Import Fallbacks ⚠️ **P2 - REMOVE**

**Pattern Found:**

```python
# Import cosine_similarity with fallback
try:
    from ..infrastructure.utils import cosine_similarity
except ImportError:
    try:
        from utils import cosine_similarity
    except ImportError:
        # Fallback implementation
        import math
        def cosine_similarity(vec1, vec2):
            # ... implementation
```

**Locations:**

- `atoms-mcp-prod/src/atoms_mcp/tools/compliance_verification.py` (lines 13-29)

**Action:**

1. Fix import paths (ensure dependencies are correct)
2. Remove fallback implementations
3. Use single canonical import path

**Rationale:** Dependencies should be managed, not worked around

---

### 4. Backward Compat Re-exports ⚠️ **P1 - REMOVE**

**Pattern Found:**

```python
# Re-export for backward compatibility
ComplianceVerificationTool = EntityOperations
```

**Locations:**

- Multiple deprecated tool stubs

**Action:**

1. Remove re-exports
2. Update all callers to use canonical names
3. Remove backward compat comments

**Rationale:** No backward compatibility needed

---

### 5. Backup Files ⚠️ **P3 - REMOVE**

**Patterns Found:**

- `*.backup` files
- `.env-backup-*` directories
- `*.backup.*` timestamped files

**Locations:**

- `thegent/crates/Cargo.toml.backup`
- `thegent/test_clode/claude-config/.claude.json.backup.*` (multiple)
- `thegent/dummy_config/.claude.json.backup.*` (multiple)
- `trace/src/tracertm/api/main.py.backup`
- `atoms-mcp-prod/src/atoms_mcp/tools/entity.py.backup`
- `trace/.env-backup-20260130/` (directory)
- `trace/frontend/apps/web/public/specs/openapi.json.backup.*`

**Action:**

1. Delete all `*.backup` files
2. Delete `.env-backup-*` directories
3. Add `*.backup` to `.gitignore`
4. Document git-based backup policy

**Rationale:** Git provides version history, backups are redundant

---

### 6. Archive Directories ⚠️ **P3 - EVALUATE**

**Locations:**

- `trace/ARCHIVE/` - Large directory with historical code
- `archive/` directories in various projects

**Status:**

- ✅ Historical reference (potentially valuable)
- ⚠️ Clutters main codebase
- ⚠️ May contain deprecated code

**Action:**

1. **EVALUATE** each archive directory
2. **MOVE** to separate repo or `.git/archive/` if valuable
3. **DELETE** if contains deprecated code
4. Document archive policy

**Rationale:** Historical context valuable, but shouldn't clutter main codebase

---

### 7. Deprecation Warnings ⚠️ **P1 - REMOVE**

**Pattern Found:**

```python
warnings.warn(
    "tools.compliance_verification is deprecated. Use ... instead.",
    DeprecationWarning,
    stacklevel=2,
)
```

**Locations:**

- Deprecated tool stubs
- Potentially other deprecated code

**Action:**

1. Remove deprecation warnings
2. Remove deprecated code entirely
3. No need for warnings if code is deleted

**Rationale:** No deprecation period needed if no users

---

## 📋 Removal Plan (With Parity Verification)

### Phase 1: Immediate (Week 1)

**Priority 1: Legacy CLI**

- [ ] **PARITY CHECK:** Verify `cli/apps/` has all features from `cli/legacy/`
  - [ ] List all functions/commands in `cli/legacy/`
  - [ ] Verify each exists in `cli/apps/` or `cli/commands/`
  - [ ] Document any differences
- [ ] **MIGRATION CHECK:** Verify all callers migrated
  - [ ] Find all imports: `grep -r "cli.legacy\|cli/legacy" src/ tests/`
  - [ ] Update callers to `cli.apps` or `cli.commands`
  - [ ] Verify no remaining imports
- [ ] **TEST CHECK:** Run parity tests
  - [ ] Create parity test comparing old vs new
  - [ ] Run tests with both implementations
  - [ ] Verify outputs match
- [ ] **ONLY AFTER PARITY VERIFIED:** Delete `src/thegent/cli/legacy/` directory
- [ ] Update tests
- [ ] Update documentation

**Priority 2: Deprecated Stubs**

- [ ] **PARITY CHECK:** Verify canonical implementations have all features
  - [ ] List all features in deprecated stubs
  - [ ] Verify each exists in canonical implementations
  - [ ] Document any differences
- [ ] **MIGRATION CHECK:** Verify all test files migrated
  - [ ] Find all test imports: `grep -r "compliance_verification\|duplicate_detection\|entity_resolver" tests/`
  - [ ] Update test files to canonical imports
  - [ ] Verify no remaining imports
- [ ] **TEST CHECK:** Run tests with canonical implementations
  - [ ] Run full test suite
  - [ ] Verify no functionality lost
- [ ] **ONLY AFTER PARITY VERIFIED:** Delete stub files:
  - `atoms-mcp-prod/src/atoms_mcp/tools/compliance_verification.py`
  - `atoms-mcp-prod/src/atoms_mcp/tools/duplicate_detection.py`
  - `atoms-mcp-prod/src/atoms_mcp/tools/entity_resolver.py`
  - `atoms-mcp-prod/src/atoms_mcp/tools/admin.py`
  - `atoms-mcp-prod/src/atoms_mcp/tools/context.py`
- [ ] Remove deprecation warnings

**Priority 3: Backup Files**

- [ ] Find all backups: `find . -name "*.backup" -o -name ".env-backup-*"`
- [ ] Delete backup files
- [ ] Add `*.backup` to `.gitignore`
- [ ] Document git-based backup policy

### Phase 2: Short-Term (Weeks 2-3)

**Import Fallbacks:**

- [ ] Fix import paths in `compliance_verification.py`
- [ ] Remove fallback implementations
- [ ] Ensure dependencies are correct

**Backward Compat Re-exports:**

- [ ] Find all re-exports: `grep -r "backward compat\|re-export" src/`
- [ ] Update callers to canonical names
- [ ] Remove re-exports

**Archive Evaluation:**

- [ ] Audit `trace/ARCHIVE/` contents
- [ ] Move valuable archives to separate repo
- [ ] Delete deprecated code from archives

### Phase 3: Ongoing

**Pattern Prevention:**

- [ ] Add CI checks for deprecated patterns
- [ ] Add linting rules for fallbacks
- [ ] Document removal process

---

## 🔍 Detection Commands

### Find Legacy Code

```bash
# Find legacy directories
find . -type d -name "legacy" -not -path "*/\.*" -not -path "*/node_modules/*"

# Find deprecated files
find . -name "*deprecated*" -o -name "*legacy*" -not -path "*/\.*"

# Find backward compat patterns
grep -r "backward\|backwards\|compat" --include="*.py" src/ | grep -v "__pycache__"
```

### Find Backup Files

```bash
# Find backup files
find . -name "*.backup" -not -path "*/\.*" -not -path "*/node_modules/*"

# Find backup directories
find . -type d -name "*backup*" -not -path "*/\.*"

# Find timestamped backups
find . -name "*.backup.*" -not -path "*/\.*"
```

### Find Import Fallbacks

```bash
# Find try/except import patterns
grep -r "try:.*import\|except.*import" --include="*.py" src/ | grep -v "__pycache__"

# Find fallback implementations
grep -r "fallback\|Fallback" --include="*.py" src/ | grep -v "__pycache__"
```

### Find Deprecation Warnings

```bash
# Find deprecation warnings
grep -r "DeprecationWarning\|deprecated" --include="*.py" src/ | grep -v "__pycache__"
```

---

## ✅ Verification Checklist

**Before Removal (Parity Verification):**

- [ ] Parity verification completed
- [ ] Feature comparison documented
- [ ] All callers migrated
- [ ] Parity tests pass
- [ ] Migration completeness verified
- [ ] Approval obtained

**After Removal:**

- [ ] No `cli/legacy/` directory exists
- [ ] No deprecated tool stubs exist
- [ ] No `*.backup` files in repo
- [ ] No import fallbacks remain
- [ ] No backward compat re-exports
- [ ] All tests pass
- [ ] No broken imports
- [ ] Documentation updated
- [ ] **REGRESSION CHECK:** No functionality lost
- [ ] **REGRESSION CHECK:** Performance acceptable

---

## 📊 Metrics

**Before Removal:**

- Legacy directories: 1
- Deprecated files: 5+
- Backup files: 10+
- Import fallbacks: 2+

**Target (After Removal):**

- Legacy directories: 0
- Deprecated files: 0
- Backup files: 0
- Import fallbacks: 0 (except performance)

---

**Status:** Audit Complete
**Next Step:** Execute Phase 1 Removal Plan
**Owner:** Architecture Team
