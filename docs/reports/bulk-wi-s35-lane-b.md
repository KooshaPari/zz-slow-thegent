### [WL-7280]

**Title:** Classify native SHM initialization failures before fallback activation in circuit-breaker store
**Source:** [thegent/src/thegent/native/state_shm.py:212]
**Acceptance checklist:**

- [ ] Replace broad native init exception handling with explicit filesystem, import, and mmap initialization failure branches.
- [ ] Preserve pure-Python fallback activation when native SHM cannot be initialized.
- [ ] Add tests for successful native initialization, missing native dependency, and invalid SHM path permissions.
      **Notes:** Current fallback activation path collapses distinct init failures into one warning, reducing operator triage precision.

### [WL-7281]

**Title:** Preserve typed failure diagnostics for circuit-breaker native record writes
**Source:** [thegent/src/thegent/native/state_shm.py:237]
**Acceptance checklist:**

- [ ] Replace broad write-path exception handling with explicit native transport, serialization, and state-write failure classes.
- [ ] Preserve fallback write behavior after native write failures.
- [ ] Add tests for successful native record writes, native write failures, and fallback store continuity.
      **Notes:** Generic native write warnings obscure whether failures are transient runtime faults or structural state-store issues.

### [WL-7282]

**Title:** Differentiate native circuit-open read failures from valid closed-circuit states
**Source:** [thegent/src/thegent/native/state_shm.py:267]
**Acceptance checklist:**

- [ ] Replace broad native read exception handling with explicit native call, decode, and value-coercion failure branches.
- [ ] Preserve fallback-based open-state evaluation semantics when native reads fail.
- [ ] Add tests for successful native open-state reads, native read failure with fallback, and stable closed-state behavior.
      **Notes:** Current error flattening can make native read faults look indistinguishable from legitimate non-open states.

### [WL-7283]

**Title:** Surface health-score write failure classes in native SHM scoring path
**Source:** [thegent/src/thegent/native/state_shm.py:290]
**Acceptance checklist:**

- [ ] Replace broad health-score write exception handling with explicit native invocation and range-validation error categories.
- [ ] Preserve no-op fallback semantics when native interface is unavailable.
- [ ] Add tests for valid native score writes, out-of-range score input handling, and native write failures.
      **Notes:** Current debug-only catch-all path hides actionable causes for health score persistence failures.

### [WL-7284]

**Title:** Distinguish native health-score read faults from legitimate zero-score returns
**Source:** [thegent/src/thegent/native/state_shm.py:298]
**Acceptance checklist:**

- [ ] Replace broad health-score read exception handling with explicit native call and conversion failure categories.
- [ ] Preserve deterministic fallback return behavior when native reads fail.
- [ ] Add tests for successful native score reads, conversion failures, and fallback zero-return behavior.
      **Notes:** Returning `0.0` for all failures currently conflates real degraded health with instrumentation faults.

### [WL-7285]

**Title:** Classify XP tracker native initialization failures separately from fallback bootstrap
**Source:** [thegent/src/thegent/native/state_shm.py:331]
**Acceptance checklist:**

- [ ] Replace broad XP native init exception handling with explicit dependency, path-creation, and interface-init failure classes.
- [ ] Preserve fallback XP store startup behavior when native init fails.
- [ ] Add tests for native XP init success, missing native backend, and invalid SHM location.
      **Notes:** One-path warning handling currently obscures whether XP persistence failures are environmental or binary-related.

### [WL-7286]

**Title:** Preserve tmux session fallback probe diagnostics for subprocess invocation failures
**Source:** [thegent/src/thegent/native/discovery_native.py:59]
**Acceptance checklist:**

- [ ] Replace broad fallback session probe exception suppression with explicit subprocess launch, timeout, and output-parse failure classes.
- [ ] Preserve empty-list return contract when fallback probing cannot complete.
- [ ] Add tests for successful tmux session parsing, subprocess timeout, and malformed probe output.
      **Notes:** Silent fallback failures reduce observability for session discovery regressions in non-native mode.

### [WL-7287]

**Title:** Distinguish optional psutil import failures from process enumeration runtime faults
**Source:** [thegent/src/thegent/native/discovery_native.py:77]
**Acceptance checklist:**

- [ ] Replace broad psutil import suppression with explicit module-missing and import-runtime failure categories.
- [ ] Preserve deterministic empty-result behavior when process scanning dependencies are unavailable.
- [ ] Add tests for psutil-available scanning, missing-psutil environments, and import-time runtime errors.
      **Notes:** Current import catch-all hides package availability versus import-side execution issues.

### [WL-7288]

**Title:** Separate per-process inspection faults from global process discovery outcomes
**Source:** [thegent/src/thegent/native/discovery_native.py:111]
**Acceptance checklist:**

- [ ] Replace broad per-process exception suppression with bounded categories for access-denied, zombie, and data-shape errors.
- [ ] Preserve continued scanning across remaining processes after per-process failures.
- [ ] Add tests for complete scan success, mixed per-process failures, and continued result collection.
      **Notes:** Per-process exception flattening currently masks recurring fault types during process inventory collection.

### [WL-7289]

**Title:** Classify native discovery command execution failures before fallback selection
**Source:** [thegent/src/thegent/native/discovery_native.py:143]
**Acceptance checklist:**

- [ ] Replace broad native command execution exception handling with explicit timeout, invocation, and transport failure classes.
- [ ] Preserve existing fallback invocation behavior when native command execution fails.
- [ ] Add tests for successful native command execution, timeout failure path, and command-launch failures.
      **Notes:** Collapsing native execution faults into `None` weakens diagnosis when binary-backed discovery regresses.
