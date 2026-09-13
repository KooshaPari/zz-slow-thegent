### [WL-7930]

**Title:** Enforce deterministic shell tool borrowing order in mixed-runtime sessions
**Source:** [thegent/src/thegent/tools/borrow.py:88]
**Acceptance checklist:**

- [ ] Refactor borrow resolution to sort candidate tool providers by explicit priority before selection.
- [ ] Preserve existing successful borrow behavior for single-provider and no-provider paths.
- [ ] Add tests for equal-priority providers, missing priority metadata, and deterministic selection output.
      **Notes:** Non-deterministic provider choice causes flaky behavior when session runtimes change between invocations.

### [WL-7931]

**Title:** Split XML repair failure reporting between parse normalization and tag-balance reconciliation
**Source:** [thegent/src/thegent/tools/xml_repair.py:132]
**Acceptance checklist:**

- [ ] Separate repair-stage exceptions so parse-normalization and tag-reconciliation failures are emitted distinctly.
- [ ] Preserve valid-XML pass-through behavior and repaired output formatting invariants.
- [ ] Add tests for malformed entities, irreconcilable tag trees, and successful repair completion.
      **Notes:** Current error grouping obscures whether failures happen before or after structural reconciliation.

### [WL-7932]

**Title:** Isolate terminal capture faults across PTY attach and stream decode operations
**Source:** [thegent/src/thegent/tools/terminal_capture.py:174]
**Acceptance checklist:**

- [ ] Replace broad capture-path exception handling with explicit PTY-attach and stream-decode branches.
- [ ] Preserve successful capture chunk ordering and timestamp field semantics.
- [ ] Add tests for PTY attach failures, invalid byte-sequence decode errors, and successful capture sessions.
      **Notes:** Debugging capture regressions requires clear separation between transport and decode stages.

### [WL-7933]

**Title:** Validate shell config merge precedence across profile defaults and runtime overrides
**Source:** [thegent/src/thegent/tools/shell_config.py:61]
**Acceptance checklist:**

- [ ] Enforce explicit precedence rules when combining profile defaults with runtime override inputs.
- [ ] Preserve existing canonical key normalization and supported shell-name mapping behavior.
- [ ] Add tests for conflicting keys, unsupported shell targets, and successful merged config emission.
      **Notes:** Ambiguous precedence can silently alter shell execution behavior in automation flows.

### [WL-7934]

**Title:** Differentiate serializer failures between schema coercion and payload emission phases
**Source:** [thegent/src/thegent/serialization/serializers.py:205]
**Acceptance checklist:**

- [ ] Split serializer exception handling into schema-coercion and payload-emission failure categories.
- [ ] Preserve successful serialization field ordering and null-handling semantics.
- [ ] Add tests for invalid coercion input, emitter transport failures, and successful serialized payload output.
      **Notes:** Typed failure buckets improve triage for contract and transport issues.

### [WL-7935]

**Title:** Harden contract validation diagnostics for rule compilation versus input evaluation
**Source:** [thegent/src/thegent/contracts/validation.py:147]
**Acceptance checklist:**

- [ ] Separate validation pipeline diagnostics so rule-compilation and input-evaluation failures are reported independently.
- [ ] Preserve successful validation result shape and existing rule severity semantics.
- [ ] Add tests for invalid rule definitions, runtime evaluation errors, and successful validation passes.
      **Notes:** Validation telemetry should pinpoint whether rules or inputs are at fault.

### [WL-7936]

**Title:** Classify session manager restore errors by state snapshot load and runtime rebind stages
**Source:** [thegent/src/thegent/session/manager.py:219]
**Acceptance checklist:**

- [ ] Split restore-path exception handling into snapshot-load and runtime-rebind branches.
- [ ] Preserve successful restored session identity and active-runtime assignment behavior.
- [ ] Add tests for corrupt snapshot blobs, rebind contract mismatches, and successful session restore.
      **Notes:** Restore failures need stage-specific diagnostics to avoid repeated blind retries.

### [WL-7937]

**Title:** Enforce shell CLI argument conflict checks before execution plan expansion
**Source:** [thegent/src/thegent/shell_cli.py:96]
**Acceptance checklist:**

- [ ] Add explicit preflight conflict validation before execution plan expansion is invoked.
- [ ] Preserve successful argument parsing for non-conflicting flag combinations.
- [ ] Add tests for mutually exclusive flags, missing required companions, and successful execution plan generation.
      **Notes:** Early conflict detection reduces downstream plan-shaping errors and ambiguous CLI output.

### [WL-7938]

**Title:** Split fast file ops errors between path canonicalization and batched IO commit
**Source:** [thegent/src/thegent/infra/fast_file_ops.py:123]
**Acceptance checklist:**

- [ ] Replace catch-all operation failures with explicit path-canonicalization and batched-commit error branches.
- [ ] Preserve successful batched operation ordering and atomicity guarantees.
- [ ] Add tests for invalid path segments, partial commit interruptions, and successful batch writes.
      **Notes:** Distinct error classes help identify whether failures are input-shaping or persistence related.

### [WL-7939]

**Title:** Separate terminal keepalive faults across heartbeat schedule and transport write dispatch
**Source:** [thegent/src/thegent/infra/terminal_keepalive.py:78]
**Acceptance checklist:**

- [ ] Split keepalive failure handling into heartbeat-scheduling and transport-write dispatch stages.
- [ ] Preserve successful keepalive interval timing and retry window semantics.
- [ ] Add tests for scheduler initialization failures, write dispatch failures, and successful keepalive cycles.
      **Notes:** Keepalive regressions are easier to isolate when timer and transport errors are not conflated.
