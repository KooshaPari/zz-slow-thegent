### [WL-6960]

**Title:** Make L2 cache initialization failures explicit instead of silently disabling disk cache
**Source:** [thegent/src/thegent/cache/multi_level.py:67]
**Acceptance checklist:**

- [ ] Replace blanket exception suppression around diskcache directory/cache initialization with typed error handling.
- [ ] Preserve L1-only fallback behavior while recording bounded diagnostics when L2 setup fails.
- [ ] Add tests for successful L2 startup, directory creation failure, and cache open failure paths.
      **Notes:** Line 67 currently swallows all exceptions and silently drops to L1-only mode, hiding storage initialization regressions.

### [WL-6961]

**Title:** Differentiate handler failure classes in A2A message routing
**Source:** [thegent/src/thegent/protocols/a2a.py:166]
**Acceptance checklist:**

- [ ] Replace broad exception catching in per-handler invocation with typed failure classification.
- [ ] Keep routing resilient across handlers while preserving structured error context for failed handlers.
- [ ] Add tests for successful handler execution, recoverable handler failure, and repeated failure visibility.
      **Notes:** Line 166 catches every exception type, obscuring whether failures are user-handler bugs, contract errors, or runtime faults.

### [WL-6962]

**Title:** Remove redundant broad catch/re-raise in worker startup path
**Source:** [thegent/src/thegent/infra/multi_runtime_bridge.py:127]
**Acceptance checklist:**

- [ ] Eliminate the no-op broad `except`/`raise` block around worker subprocess startup.
- [ ] Keep startup error propagation behavior unchanged and explicit.
- [ ] Add/adjust tests to assert startup failures surface with original exception context.
      **Notes:** Line 127 currently catches all exceptions only to re-raise, adding noise without additional handling value.

### [WL-6963]

**Title:** Narrow failover triggers in runtime dispatch startup
**Source:** [thegent/src/thegent/infra/multi_runtime_bridge.py:154]
**Acceptance checklist:**

- [ ] Replace blanket startup exception catch with typed conditions that should trigger runtime failover.
- [ ] Preserve intended PyPy/CPython fallback for supported startup faults only.
- [ ] Add tests covering fallback-on-startup-failure and non-fallback propagation for unrelated errors.
      **Notes:** Line 154 catches all exceptions and can incorrectly route unrelated bugs into cross-runtime fallback.

### [WL-6964]

**Title:** Expose worker shutdown termination failure causes
**Source:** [thegent/src/thegent/infra/multi_runtime_bridge.py:180]
**Acceptance checklist:**

- [ ] Replace broad termination exception catch with typed terminate/wait timeout handling.
- [ ] Preserve best-effort kill fallback while surfacing explicit termination diagnostics.
- [ ] Add tests for graceful terminate, timeout then kill, and kill-failure reporting.
      **Notes:** Line 180 collapses all shutdown errors into one path and can hide process lifecycle failures.

### [WL-6965]

**Title:** Distinguish Nix version probe failures from path-based heuristics
**Source:** [thegent/src/thegent/doctor_shell_nix.py:148]
**Acceptance checklist:**

- [ ] Replace broad exception branch in Nix version probe with typed subprocess and decode handling.
- [ ] Preserve heuristic fallback messaging while identifying probe-failure reasons.
- [ ] Add tests for successful version probe, timeout path, and subprocess execution failure.
      **Notes:** Line 148 captures all exceptions and can report optimistic "Found Nix" states without exposing command probe failure.

### [WL-6966]

**Title:** Preserve flake file check failure details in Nix doctor output
**Source:** [thegent/src/thegent/doctor_shell_nix.py:190]
**Acceptance checklist:**

- [ ] Replace blanket exception handling around flake existence checks with typed IO/permission handling.
- [ ] Keep user-facing fail state while surfacing specific filesystem failure categories.
- [ ] Add tests for existing flake, missing flake under Nix path, and permission-denied checks.
      **Notes:** Line 190 catches all exceptions and collapses distinct filesystem failures into one generic permission message.

### [WL-6967]

**Title:** Surface native parser extraction failures before Python fallback
**Source:** [thegent/src/thegent/contracts/parser.py:224]
**Acceptance checklist:**

- [ ] Replace broad exception suppression around native tag extraction with typed parser/runtime failure handling.
- [ ] Preserve Python parser fallback while recording bounded diagnostics for native extraction failures.
- [ ] Add tests for successful native extraction, native failure fallback, and malformed input handling parity.
      **Notes:** Line 224 currently swallows all native parser errors, making fallback-trigger causes invisible during parser troubleshooting.

### [WL-6968]

**Title:** Make calibration load corruption visible instead of resetting silently
**Source:** [thegent/src/thegent/ux/calibration.py:42]
**Acceptance checklist:**

- [ ] Replace blanket JSON load exception handling with typed parse/read failure handling.
- [ ] Preserve empty-map fallback for unusable calibration files while surfacing corruption/read diagnostics.
- [ ] Add tests for valid calibration, malformed JSON, and unreadable calibration file paths.
      **Notes:** Line 42 swallows all load failures and silently resets bias state, masking persistence and data-corruption issues.

### [WL-6969]

**Title:** Differentiate unsupported compression from decompression faults in probe helper
**Source:** [thegent/src/thegent/infra/fast_compression.py:108]
**Acceptance checklist:**

- [ ] Replace blanket exception handling in `_try_decompress` with typed decompression and method-validation handling.
- [ ] Preserve `None` probe semantics for recoverable mismatches while surfacing non-recoverable faults.
- [ ] Add tests for valid decompress, wrong-method probe miss, and corrupted payload failure behavior.
      **Notes:** Line 108 catches every exception type and can hide real decompressor bugs behind generic probe miss behavior.
