### [WL-7560]

**Title:** Make queue watch interruption handling observable instead of silently swallowing keyboard interrupts
**Source:** [thegent/src/thegent/ux/queue_tui.py:53]
**Acceptance checklist:**

- [ ] Replace bare `pass` in `QueueTUI.watch` with explicit interruption handling that leaves a traceable message or state.
- [ ] Preserve current behavior of exiting cleanly on `KeyboardInterrupt`.
- [ ] Add a focused test that verifies interruption does not crash and is surfaced deterministically.
      **Notes:** Line 53 currently suppresses interruption context with `pass`.

### [WL-7561]

**Title:** Preserve truncation-path diagnostics when recorder result serialization fails
**Source:** [thegent/src/thegent/trace/recorder.py:328]
**Acceptance checklist:**

- [ ] Replace silent serialization failure handling in `_truncate_result` with explicit, bounded diagnostics.
- [ ] Preserve current fallback behavior that returns the original result when truncation serialization cannot be computed.
- [ ] Add tests for non-serializable payloads and large serializable payload truncation.
      **Notes:** Line 328 currently ignores `TypeError`/`ValueError` with `pass`.

### [WL-7562]

**Title:** Surface shell hook read failures in mise diagnostics without hiding permission and decode issues
**Source:** [thegent/src/thegent/install.py:549]
**Acceptance checklist:**

- [ ] Replace broad exception suppression in shell hook scanning with typed exception handling and actionable messages.
- [ ] Preserve current non-fatal warning posture when no hook is found.
- [ ] Add tests for unreadable hook files and malformed file content.
      **Notes:** Line 549 currently suppresses all hook-file read errors.

### [WL-7563]

**Title:** Implement real test-indicator discovery in gardening checks instead of no-op pattern iteration
**Source:** [thegent/src/thegent/sitback/gardening.py:114]
**Acceptance checklist:**

- [ ] Replace the no-op loop body with concrete filesystem checks for declared indicator patterns.
- [ ] Preserve existing return schema for `check_test_failures`.
- [ ] Add tests for indicator-present and indicator-absent project states.
      **Notes:** Line 114 uses `pass`, so declared patterns are never evaluated.

### [WL-7564]

**Title:** Expose keepalive newline write failures for terminal health visibility
**Source:** [thegent/src/thegent/ux/keepalive.py:159]
**Acceptance checklist:**

- [ ] Replace silent IO suppression in `_write_newline` with explicit, low-noise diagnostics.
- [ ] Preserve non-throwing behavior for transient stdout issues.
- [ ] Add tests that simulate stdout write/flush failures.
      **Notes:** Line 159 currently swallows write failures with `pass`.

### [WL-7565]

**Title:** Make KPI finance metric dependency failures explicit while preserving dashboard continuity
**Source:** [thegent/src/thegent/ux/kpis.py:100]
**Acceptance checklist:**

- [ ] Replace blanket `except` suppression around `CostAggregator` import/use with typed handling and visible diagnostics.
- [ ] Preserve KPI generation when finance metrics are unavailable.
- [ ] Add tests for missing/errored cost aggregation path.
      **Notes:** Line 100 currently hides finance metric load failures.

### [WL-7566]

**Title:** Distinguish lockfile race conditions from true read failures in shared MCP startup coordination
**Source:** [thegent/src/thegent/shared_mcp_manager.py:103]
**Acceptance checklist:**

- [ ] Replace silent `FileNotFoundError` suppression with explicit race-aware handling and traceable logging.
- [ ] Preserve successful startup path when lockfile disappears between checks.
- [ ] Add tests covering lockfile removal races during startup.
      **Notes:** Line 103 currently uses `pass`, making race behavior opaque.

### [WL-7567]

**Title:** Surface ps-shim inspection read errors during doctor checks
**Source:** [thegent/src/thegent/doctor.py:333]
**Acceptance checklist:**

- [ ] Replace silent `OSError` suppression in ps-shim content inspection with explicit diagnostics.
- [ ] Preserve existing pass/fail outcome semantics for harmful shim detection.
- [ ] Add tests for unreadable shim files and valid harmful shim signatures.
      **Notes:** Line 333 currently drops ps-shim read errors with no visibility.

### [WL-7568]

**Title:** Preserve directory size scan observability when filesystem traversal raises top-level access errors
**Source:** [thegent/src/thegent/infra/fast_file_ops.py:205]
**Acceptance checklist:**

- [ ] Replace top-level traversal suppression with typed handling that records skipped-directory diagnostics.
- [ ] Preserve current behavior of returning accumulated size when partial traversal succeeds.
- [ ] Add tests for permission-denied directories and mixed-readable trees.
      **Notes:** Line 205 currently suppresses traversal errors via `pass`.

### [WL-7569]

**Title:** Make corrupt lease payload handling explicit in file coordination lease claims
**Source:** [thegent/src/thegent/coordination/file_coordination.py:53]
**Acceptance checklist:**

- [ ] Replace silent `IndexError`/`ValueError` handling in lease parsing with explicit invalid-lease remediation.
- [ ] Preserve existing lease claim success path for valid active leases.
- [ ] Add tests for malformed lease files and expired lease reclamation.
      **Notes:** Line 53 currently suppresses malformed lease parse errors with `pass`.
