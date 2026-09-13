### [WL-7330]

**Title:** Classify native circuit-breaker SHM bootstrap failures before fallback selection
**Source:** [thegent/src/thegent/native/state_shm.py:212]
**Acceptance checklist:**

- [ ] Replace broad native SHM initialization exception handling with explicit filesystem, dependency, and mmap initialization failure branches.
- [ ] Preserve deterministic pure-Python fallback activation when native bootstrap fails.
- [ ] Add tests for successful native bootstrap, missing native module, and unwritable SHM parent directory.
      **Notes:** The current catch-all warning obscures whether native bootstrap failed due to environment setup, binary availability, or path permissions.

### [WL-7331]

**Title:** Preserve typed diagnostics for native record-failure write fallback transitions
**Source:** [thegent/src/thegent/native/state_shm.py:237]
**Acceptance checklist:**

- [ ] Replace broad native write exception handling with explicit transport, encoding, and state-write failure categories.
- [ ] Preserve fallback write continuity when native record writes fail.
- [ ] Add tests covering successful native writes, native write exceptions, and fallback store continuity.
      **Notes:** Flattened warning output reduces operator visibility into whether failures are transient runtime errors or persistent backend faults.

### [WL-7332]

**Title:** Separate native open-state read faults from valid closed-circuit outcomes
**Source:** [thegent/src/thegent/native/state_shm.py:267]
**Acceptance checklist:**

- [ ] Replace broad native `is_open` exception handling with explicit native call, decode, and coercion failure branches.
- [ ] Preserve fallback open-state evaluation semantics after native read failures.
- [ ] Add tests for successful native read, native read failure with fallback, and stable closed-state behavior.
      **Notes:** Current catch-all handling makes native read failures indistinguishable from legitimate non-open circuit states.

### [WL-7333]

**Title:** Bound health-score native write failures with actionable error classes
**Source:** [thegent/src/thegent/native/state_shm.py:290]
**Acceptance checklist:**

- [ ] Replace broad health-score write exception handling with explicit invocation, validation, and transport failure categories.
- [ ] Preserve no-op behavior when native interface is unavailable.
- [ ] Add tests for valid writes, invalid score values, and native write failures.
      **Notes:** Debug-only catch-all logging currently hides actionable root causes for score persistence failures.

### [WL-7334]

**Title:** Distinguish native health-score read errors from legitimate zero-score results
**Source:** [thegent/src/thegent/native/state_shm.py:298]
**Acceptance checklist:**

- [ ] Replace broad health-score read exception handling with explicit native call and type-conversion failure branches.
- [ ] Preserve deterministic fallback return behavior when native reads fail.
- [ ] Add tests for successful reads, conversion failures, and fallback zero-return behavior.
      **Notes:** Returning `0.0` for all failures conflates instrumentation faults with true degraded health state.

### [WL-7335]

**Title:** Classify XP tracker native bootstrap failures independently from fallback startup
**Source:** [thegent/src/thegent/native/state_shm.py:331]
**Acceptance checklist:**

- [ ] Replace broad XP native init exception handling with explicit dependency, path-creation, and interface-init failure categories.
- [ ] Preserve fallback XP store startup behavior after native init failures.
- [ ] Add tests for successful native init, missing native backend, and invalid SHM location.
      **Notes:** One-path warning handling currently hides whether XP bootstrap failures are environmental, permission-related, or binary-related.

### [WL-7336]

**Title:** Preserve tmux fallback probe diagnostics for subprocess command failures
**Source:** [thegent/src/thegent/native/discovery_native.py:59]
**Acceptance checklist:**

- [ ] Replace broad fallback session probe exception suppression with explicit subprocess launch, timeout, and parse failure classes.
- [ ] Preserve empty-list return contract when fallback probing cannot complete.
- [ ] Add tests for successful tmux parsing, timeout failures, and malformed probe output.
      **Notes:** Silent fallback probe failures reduce visibility when discovery degrades outside native mode.

### [WL-7337]

**Title:** Distinguish optional psutil import absence from runtime import faults in process discovery
**Source:** [thegent/src/thegent/native/discovery_native.py:77]
**Acceptance checklist:**

- [ ] Replace broad psutil import suppression with explicit module-missing and import-runtime failure branches.
- [ ] Preserve deterministic empty-result behavior when process scan dependencies are unavailable.
- [ ] Add tests for psutil-available scans, missing-psutil environments, and import-time execution failures.
      **Notes:** Current catch-all handling masks dependency availability issues versus import-side runtime faults.

### [WL-7338]

**Title:** Separate invalid regex pattern failures from process-scan execution outcomes
**Source:** [thegent/src/thegent/native/discovery_native.py:83]
**Acceptance checklist:**

- [ ] Introduce explicit invalid-regex diagnostics instead of generic early empty-return behavior.
- [ ] Preserve current scan behavior for valid patterns and default pattern fallback.
- [ ] Add tests for valid custom patterns, invalid regex input, and default pattern operation.
      **Notes:** Returning an empty list for invalid regex silently hides user input errors during discovery filtering.

### [WL-7339]

**Title:** Classify native discovery command execution failures before fallback process enumeration
**Source:** [thegent/src/thegent/native/discovery_native.py:143]
**Acceptance checklist:**

- [ ] Replace broad native command exception handling with explicit timeout, invocation, and transport failure classes.
- [ ] Preserve fallback-based discovery behavior when native command execution fails.
- [ ] Add tests for successful native command execution, timeout handling, and launch-time failures.
      **Notes:** Collapsing native execution failures into `None` weakens diagnosis when binary-backed discovery regresses.
