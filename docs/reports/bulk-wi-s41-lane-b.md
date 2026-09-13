### [WL-7580]

**Title:** Split conversation text dump failure handling into render and write stages
**Source:** [thegent/src/thegent/session/conversation_dumper.py:342]
**Acceptance checklist:**

- [ ] Replace the broad conversation text dump exception catch with explicit markdown-render and filesystem-write failure branches.
- [ ] Preserve existing artifact naming and logging fields while adding stage-specific failure metadata.
- [ ] Add tests covering successful text dump, render-time failure, and disk-write failure.
      **Notes:** A single catch-all currently obscures whether failure happened during content generation or persistence.

### [WL-7581]

**Title:** Classify watcher event-loop callback failures instead of generic warning-only suppression
**Source:** [thegent/src/thegent/native/watcher_daemon.py:207]
**Acceptance checklist:**

- [ ] Replace broad callback exception handling with typed categories for callback contract errors and runtime execution errors.
- [ ] Preserve watcher loop continuity so one callback failure does not terminate the daemon.
- [ ] Add tests for normal callback execution, contract violation, and runtime exception isolation.
      **Notes:** Generic suppression keeps the loop alive but drops actionable diagnostics for recurring callback faults.

### [WL-7582]

**Title:** Differentiate shared-memory state flush serialization and transport failures
**Source:** [thegent/src/thegent/native/state_shm.py:267]
**Acceptance checklist:**

- [ ] Replace blanket flush exception handling with explicit serialization-error and shared-memory-transport-error branches.
- [ ] Preserve non-fatal behavior that keeps the watcher process running when a flush fails.
- [ ] Add tests for successful flush, serialization failure, and SHM write failure.
      **Notes:** Collapsing all flush faults into one path makes it difficult to prioritize remediation work.

### [WL-7583]

**Title:** Make summary rendering failures explicit between template assembly and output formatting
**Source:** [thegent/src/thegent/summary.py:319]
**Acceptance checklist:**

- [ ] Replace generic summary render exception handling with explicit template-assembly and output-formatting failure paths.
- [ ] Preserve existing successful summary output shape and call signature.
- [ ] Add tests for normal summary generation and one failure case per render stage.
      **Notes:** Current broad handling masks where rendering breaks and slows root-cause isolation.

### [WL-7584]

**Title:** Tighten execution preflight error boundary for command preparation failures
**Source:** [thegent/src/thegent/execution.py:528]
**Acceptance checklist:**

- [ ] Replace broad preflight exception catch with explicit argument-normalization, environment-resolution, and subprocess-preparation branches.
- [ ] Preserve existing failure propagation behavior for callers while enriching error context.
- [ ] Add tests for successful preflight plus each explicit failure branch.
      **Notes:** One generic preflight failure path currently hides which setup stage is broken.

### [WL-7585]

**Title:** Separate prompt-template load failures from interpolation failures in prompt assembly
**Source:** [thegent/src/thegent/prompts.py:206]
**Acceptance checklist:**

- [ ] Replace broad prompt assembly exception handling with distinct template-load and variable-interpolation failure categories.
- [ ] Preserve current prompt assembly API and successful output semantics.
- [ ] Add tests for valid template assembly, missing template source, and interpolation key errors.
      **Notes:** Conflated errors make it hard to determine whether data or template assets caused prompt assembly failure.

### [WL-7586]

**Title:** Classify shell CLI command dispatch failures before wrapping user-facing errors
**Source:** [thegent/src/thegent/shell_cli.py:342]
**Acceptance checklist:**

- [ ] Replace broad command dispatch catch with explicit parser-validation, command-execution, and response-render failure branches.
- [ ] Preserve current CLI exit-code contract for success and failure cases.
- [ ] Add tests for successful dispatch, invalid command input, and execution-time failure.
      **Notes:** A single wrapped exception path reduces operator visibility into the true dispatch failure stage.

### [WL-7587]

**Title:** Split borrow-tool network probe errors into timeout, connection, and protocol classes
**Source:** [thegent/src/thegent/tools/borrow.py:238]
**Acceptance checklist:**

- [ ] Replace catch-all probe exception handling with explicit timeout, connection refusal, and protocol error branches.
- [ ] Preserve existing boolean reachability contract for upstream callers.
- [ ] Add tests for successful probe, timeout behavior, and connection-refused behavior.
      **Notes:** Returning a generic unreachable state for all failures hides useful retry and triage signals.

### [WL-7588]

**Title:** Differentiate compositor panel render failures from panel payload contract violations
**Source:** [thegent/src/thegent/ui/compositor_manager.py:447]
**Acceptance checklist:**

- [ ] Replace broad panel render exception handling with separate renderer-runtime and payload-shape validation branches.
- [ ] Preserve user-facing fallback panel output behavior when render fails.
- [ ] Add tests for successful panel rendering, renderer crash, and invalid payload handling.
      **Notes:** The current single fallback protects UX but drops structured signals needed for repeated incident diagnosis.

### [WL-7589]

**Title:** Remove dead exception wrapper in Claude dependency status assignment path
**Source:** [thegent/src/thegent/doctor_dependencies.py:42]
**Acceptance checklist:**

- [ ] Eliminate redundant try-except around deterministic Claude binary status assignment.
- [ ] Preserve existing dependency-check output fields and status semantics.
- [ ] Add tests for both Claude-present and Claude-missing environments.
      **Notes:** The no-op wrapper adds noise and obscures the true decision boundary for dependency status.
