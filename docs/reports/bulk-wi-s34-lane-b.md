### [WL-7230]

**Title:** Classify archive copy failures in conversation dump export path
**Source:** [thegent/src/thegent/session/conversation_dumper.py:163]
**Acceptance checklist:**

- [ ] Replace broad copy-path exception handling with typed filesystem and permission failure branches.
- [ ] Preserve current export flow while emitting deterministic diagnostics for copy failures.
- [ ] Add tests for successful export copy, missing source artifact, and permission-denied destination.
      **Notes:** Current catch-all handling obscures whether export failures are caused by source availability, destination permissions, or transient I/O issues.

### [WL-7231]

**Title:** Surface JSON payload write failure classes during conversation persistence
**Source:** [thegent/src/thegent/session/conversation_dumper.py:215]
**Acceptance checklist:**

- [ ] Replace generic write exception handling with explicit serialization and filesystem error categories.
- [ ] Preserve non-corrupt write guarantees while reporting bounded diagnostics.
- [ ] Add tests for successful JSON write, serialization failure, and disk write failure.
      **Notes:** Undifferentiated persistence failures reduce triage quality for conversation export regressions.

### [WL-7232]

**Title:** Distinguish metadata extraction failures from absent optional fields in dump flow
**Source:** [thegent/src/thegent/session/conversation_dumper.py:342]
**Acceptance checklist:**

- [ ] Replace broad metadata extraction exception handling with typed parse and schema failure branches.
- [ ] Preserve tolerant handling of optional metadata fields while reporting malformed payloads.
- [ ] Add tests for full metadata extraction, missing optional fields, and malformed metadata structures.
      **Notes:** Treating all metadata failures identically makes malformed input and legitimate sparsity look the same.

### [WL-7233]

**Title:** Preserve structured parse diagnostics for malformed assistant output chunks
**Source:** [thegent/src/thegent/output_parser.py:277]
**Acceptance checklist:**

- [ ] Replace generic parse suppression with typed decode and schema validation failure categories.
- [ ] Preserve parser resilience for mixed valid/invalid chunks.
- [ ] Add tests for fully valid chunk streams, malformed chunk payloads, and partially valid streams.
      **Notes:** Current catch-all parsing behavior hides upstream formatting regressions in assistant output streams.

### [WL-7234]

**Title:** Separate final output normalization faults from expected empty-output conditions
**Source:** [thegent/src/thegent/output_parser.py:550]
**Acceptance checklist:**

- [ ] Replace blanket exception handling in normalization with typed coercion and structure-check errors.
- [ ] Preserve expected behavior for legitimately empty outputs.
- [ ] Add tests for valid normalized output, structurally invalid payloads, and empty output handling.
      **Notes:** Generic exception handling currently conflates malformed output with intentional empty responses.

### [WL-7235]

**Title:** Classify shell bootstrap initialization failures in CLI entry setup
**Source:** [thegent/src/thegent/shell_cli.py:138]
**Acceptance checklist:**

- [ ] Replace broad bootstrap exception handling with typed environment, dependency, and runtime init failure branches.
- [ ] Preserve fail-fast startup behavior with actionable error messaging.
- [ ] Add tests for successful bootstrap, missing dependency, and invalid runtime configuration.
      **Notes:** Current catch-all startup handling weakens error quality for first-hop CLI failures.

### [WL-7236]

**Title:** Differentiate shell command dispatch errors from argument-validation failures
**Source:** [thegent/src/thegent/shell_cli.py:176]
**Acceptance checklist:**

- [ ] Replace blanket dispatch exception handling with explicit argument, routing, and execution failure categories.
- [ ] Preserve existing command dispatch semantics for successful routes.
- [ ] Add tests for valid dispatch, invalid arguments, and command runtime failures.
      **Notes:** Collapsing dispatch failures into one path obscures whether issues originate at parse-time or run-time.

### [WL-7237]

**Title:** Preserve subprocess launch diagnostics for shell execution pathway
**Source:** [thegent/src/thegent/shell_cli.py:220]
**Acceptance checklist:**

- [ ] Replace broad subprocess exception handling with typed launch, timeout, and exit-state diagnostics.
- [ ] Preserve current subprocess invocation contract and return semantics.
- [ ] Add tests for successful subprocess execution, launch failure, and timeout scenarios.
      **Notes:** Current exception flattening hides actionable subprocess failure context during shell operations.

### [WL-7238]

**Title:** Expose provider calibration fallback causes without masking scoring degradation
**Source:** [thegent/src/thegent/ux/calibration.py:42]
**Acceptance checklist:**

- [ ] Replace generic calibration exception handling with typed read, parse, and value-range failure classes.
- [ ] Preserve fallback calibration behavior while emitting bounded degraded-state diagnostics.
- [ ] Add tests for valid calibration load, malformed calibration data, and out-of-range factor values.
      **Notes:** Catch-all fallback logic can hide silent calibration drift and ranking quality regressions.

### [WL-7239]

**Title:** Differentiate cache warmup partial failures from full pre-warm completion
**Source:** [thegent/src/thegent/cache/pre_warmer.py:170]
**Acceptance checklist:**

- [ ] Replace broad warmup exception handling with typed backend, network, and serialization failure branches.
- [ ] Preserve resilient warmup continuation across independent cache entries.
- [ ] Add tests for full warmup success, per-entry failures, and mixed success/failure warmup runs.
      **Notes:** Undifferentiated warmup exceptions obscure whether cache readiness is partially degraded or fully unavailable.
