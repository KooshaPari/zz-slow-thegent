<DONE>
# Friction Points Log

> **Purpose**: Continuous log of friction points identified during agent workflows
> **Last Updated**: 2026-02-18

---

## How to Use

**Agents**: Log friction points using `log_friction()` or manually add entries below.

**Format**:

```markdown
## [task-id]

- **Category**: dx/ux/ax
- **Type**: verbosity/complexity/efficiency/etc
- **Location**: file/function/pattern
- **Description**: What friction was identified
- **Impact**: Time saved, complexity reduced, etc.
- **Solution**: Proposed fix
- **Priority**: P1 (blocking) or P2 (improvement)
- **Timestamp**: ISO timestamp
```

---

## Friction Points

### dx-improve-verbosity-batch-files-2026-02-18

- **Category**: DX
- **Type**: Verbosity
- **Location**: File reading operations
- **Description**: Multiple `read_file()` calls for similar operations could be batched
- **Impact**: Reduces tool calls by 50-70%, faster execution
- **Solution**: Use `batch_read_files()` helper from `scripts/batch_file_ops.py`
- **Priority**: P1
- **Timestamp**: 2026-02-18T00:00:00

---

### dx-improve-path-handling-2026-02-18

- **Category**: DX
- **Type**: Complexity
- **Location**: Path handling across all operations
- **Description**: Inconsistent path handling (relative vs absolute) causes errors
- **Impact**: Reduces path-related errors, improves consistency
- **Solution**: Use `normalize_path()` utility, always use absolute paths
- **Priority**: P1
- **Timestamp**: 2026-02-18T00:00:00

---

### dx-improve-file-reading-efficiency-2026-02-18

- **Category**: DX
- **Type**: Efficiency
- **Location**: Large file reading operations
- **Description**: Reading entire large files when only small sections needed
- **Impact**: 90%+ reduction in data transfer for large files
- **Solution**: Always use `read_file_optimized()` or `read_file_chunk()` from `thegent.utils.helpers`. Use `offset` and `limit`.
- **Status**: ✅ Implemented `read_file_optimized` and `read_file_lines` (efficient). Migrated CLI continuation and Session Watcher.
- **Priority**: P2
- **Timestamp**: 2026-02-18T00:00:00

---

### ax-improve-reusable-helpers-2026-02-18

- **Category**: AX
- **Type**: Reusability
- **Location**: Repetitive patterns across agents
- **Description**: Common patterns (file ops, path handling) should be reusable helpers
- **Impact**: Reduces code duplication, improves consistency
- **Solution**: Create helper library in `scripts/`, document in agent instructions
- **Priority**: P1
- **Timestamp**: 2026-02-18T00:00:00

---

### ux-improve-error-messages-2026-02-18

- **Category**: UX
- **Type**: Clarity
- **Location**: Error handling
- **Description**: Error messages not actionable, don't suggest fixes
- **Impact**: Faster debugging, clearer next steps
- **Solution**: Include suggested fixes, actionable next steps in error messages
- **Priority**: P2
- **Timestamp**: 2026-02-18T00:00:00

---

### ax-improve-workstream-operations-2026-02-18

- **Category**: AX
- **Type**: Automation
- **Location**: Work stream operations
- **Description**: Manual work stream operations (read, parse, update) could be automated
- **Impact**: Reduces manual steps by 80%, prevents errors
- **Solution**: Use `workstream_helper.py` for batch operations, auto-completion
- **Priority**: P1
- **Timestamp**: 2026-02-18T00:00:00

---

### dx-improve-python-env-wait-next-2026-02-18

- **Category**: DX
- **Type**: Environment
- **Location**: `thegent plan wait-next` command
- **Description**: Command fails due to Python environment issue (`attr` module)
- **Impact**: Cannot use native monitor→act loop command
- **Solution**: Fix Python environment or create alternative monitor command
- **Priority**: P1
- **Timestamp**: 2026-02-18T12:30:00

---

### dx-improve-rg-error-noise-2026-02-18

- **Category**: DX
- **Type**: Verbosity
- **Location**: `scripts/workstream_helper.py` output
- **Description**: `rg` errors appear in output (non-critical but noisy)
- **Impact**: Reduces output clarity
- **Solution**: Suppress `rg` errors or fix encoding issue (use `grep -v "rg: error"` as workaround)
- **Priority**: P2
- **Timestamp**: 2026-02-18T12:30:00

---

### ax-improve-search-decision-friction-2026-02-18

- **Category**: AX
- **Type**: Decision
- **Location**: `docgen-algolia-search` task
- **Description**: Need to decide Algolia (SaaS) vs Orama (OSS) — governance says "OSS and Free First"
- **Impact**: Decision needed before implementation
- **Solution**: Prefer Orama Search (OSS, self-hosted) per governance policy
- **Priority**: P1
- **Timestamp**: 2026-02-18T12:35:00

---

## Statistics

- **Total Friction Points**: 8
- **DX Friction**: 5
- **UX Friction**: 1
- **AX Friction**: 2
- **P1 Priority**: 5
- **P2 Priority**: 3

---

## See Also

- [DX_UX_AX_CONTINUOUS_IMPROVEMENT_SYSTEM.md](./DX_UX_AX_CONTINUOUS_IMPROVEMENT_SYSTEM.md) - System design
- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Improvement tasks

---

**Status**: 📝 **ACTIVE LOG** - Continuously updated
