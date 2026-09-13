### [WL-7250]

**Title:** Preserve tmux session fallback command failures as explicit diagnostics instead of empty-list suppression
**Source:** [thegent/src/thegent/native/discovery_native.py:59]
**Acceptance checklist:**

- [ ] Replace catch-all exception handling in `_fallback_sessions` with typed subprocess and parse-failure branches.
- [ ] Preserve current list return contract for valid no-session tmux output.
- [ ] Add tests for successful session parsing, tmux command failure, and malformed row handling.
      **Notes:** Silent fallback suppression can hide tmux transport failures during discovery triage.

### [WL-7251]

**Title:** Distinguish missing `psutil` dependency from generic process fallback failures
**Source:** [thegent/src/thegent/native/discovery_native.py:77]
**Acceptance checklist:**

- [ ] Replace broad import suppression in `_fallback_processes` with explicit dependency-missing diagnostics.
- [ ] Preserve empty-result behavior when scans legitimately return no matching processes.
- [ ] Add tests for installed `psutil`, missing `psutil`, and dependency-load edge cases.
      **Notes:** Treating all import failures as empty results obscures environment drift.

### [WL-7252]

**Title:** Surface invalid regex compilation errors in fallback process discovery with bounded error metadata
**Source:** [thegent/src/thegent/native/discovery_native.py:83]
**Acceptance checklist:**

- [ ] Replace silent `re.error` fallback with typed pattern-validation reporting.
- [ ] Preserve safe no-result behavior for invalid caller-supplied patterns.
- [ ] Add tests for valid pattern matches, invalid regex patterns, and default-pattern fallback.
      **Notes:** Hidden regex failures reduce confidence in pattern-based process audits.

### [WL-7253]

**Title:** Classify per-process iteration failures during `psutil` fallback scans without dropping visibility
**Source:** [thegent/src/thegent/native/discovery_native.py:111]
**Acceptance checklist:**

- [ ] Replace catch-all per-process suppression with bounded exception classification and counters.
- [ ] Preserve continued iteration for unaffected processes.
- [ ] Add tests for healthy iteration, transient access failures, and malformed process payloads.
      **Notes:** Silent per-row drops can under-report active agent processes.

### [WL-7254]

**Title:** Differentiate native discovery command timeout from transport/runtime failures in binary execution path
**Source:** [thegent/src/thegent/native/discovery_native.py:142]
**Acceptance checklist:**

- [ ] Split `_run` timeout handling from generic execution failures with distinct diagnostic states.
- [ ] Preserve fallback-to-Python behavior when native calls are unavailable.
- [ ] Add tests for successful native calls, timeout expiry, and subprocess launch errors.
      **Notes:** Collapsing timeout and execution faults hinders incident root-cause analysis.

### [WL-7255]

**Title:** Preserve non-zero native discovery exit diagnostics before falling back to Python collectors
**Source:** [thegent/src/thegent/native/discovery_native.py:147]
**Acceptance checklist:**

- [ ] Emit structured metadata for non-zero return codes in discovery binary calls.
- [ ] Preserve current fallback behavior to `_fallback_sessions`, `_fallback_tools`, and `_fallback_processes`.
- [ ] Add tests for zero-exit JSON output, non-zero exits, and mixed-fallback scenarios.
      **Notes:** Returning `None` without exit context masks native-binary regressions.

### [WL-7256]

**Title:** Preserve zmx probe failure categories when backend availability auto-detection fails
**Source:** [thegent/src/thegent/session/zmx_backend.py:249]
**Acceptance checklist:**

- [ ] Replace collapsed probe exception handling with typed `OSError` and timeout diagnostics.
- [ ] Preserve `False` availability contract for unsupported environments.
- [ ] Add tests for successful probe, binary missing, and probe timeout behavior.
      **Notes:** Probe ambiguity makes backend-selection failures difficult to audit.

### [WL-7257]

**Title:** Distinguish `zmx list` command failures from true empty-session states in plain-text fallback
**Source:** [thegent/src/thegent/session/zmx_backend.py:299]
**Acceptance checklist:**

- [ ] Refine `_list_sessions` fallback to classify command execution failure versus empty output.
- [ ] Preserve plain-text parsing path for versions lacking JSON support.
- [ ] Add tests for command success with no sessions, command failure, and non-empty fallback parsing.
      **Notes:** Conflating command failure with empty output can misreport active sessions.

### [WL-7258]

**Title:** Surface directory size-walk permission failures instead of silently undercounting totals
**Source:** [thegent/src/thegent/infra/fast_file_ops.py:163]
**Acceptance checklist:**

- [ ] Replace broad directory-walk exception suppression in `get_size` with bounded permission and I/O diagnostics.
- [ ] Preserve best-effort aggregate sizing for readable portions of directory trees.
- [ ] Add tests for fully readable trees, partial permission denial, and disappearing-file races.
      **Notes:** Silent walk suppression can produce misleading size metrics for operator decisions.

### [WL-7259]

**Title:** Record slot-level compositor render failure context before returning generic panel fallback text
**Source:** [thegent/src/thegent/ui/compositor_manager.py:447]
**Acceptance checklist:**

- [ ] Replace broad render exception boundary behavior with typed failure metadata capture per slot.
- [ ] Preserve stable fallback rendering string contract for failed slots.
- [ ] Add tests for healthy renders, deterministic slot failure isolation, and repeated-failure suppression.
      **Notes:** Generic render fallbacks without context limit debuggability of UI degradation paths.
