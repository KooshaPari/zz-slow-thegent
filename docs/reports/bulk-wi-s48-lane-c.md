### [WL-7940]

**Title:** Emit explicit parse diagnostics for malformed workstream backlog tables
**Source:** [thegent/src/thegent/commands/workstream.py:96]
**Acceptance checklist:**

- [ ] Refactor backlog parsing to return typed parse errors with row and column context instead of generic failure strings.
- [ ] Preserve successful parsing behavior for valid tables and existing completion command pathways.
- [ ] Add tests for missing header separators, malformed rows, and successful table parse execution.
      **Notes:** Targeted diagnostics reduce triage time when manual edits break BACKLOG structure.

### [WL-7941]

**Title:** Enforce deterministic task file discovery ordering before sync aggregation
**Source:** [thegent/src/thegent/task/sync.py:39]
**Acceptance checklist:**

- [ ] Sort discovered task files by canonical path prior to per-file parse and merge operations.
- [ ] Preserve successful task merge semantics for duplicate-safe task identifiers.
- [ ] Add tests that run sync repeatedly on identical inputs and assert byte-stable backlog output ordering.
      **Notes:** Non-deterministic discovery order causes unstable diffs in generated report artifacts.

### [WL-7942]

**Title:** Validate dependency graph cycles before queue insertion scheduling
**Source:** [thegent/src/thegent/task_queue/scheduler.py:118]
**Acceptance checklist:**

- [ ] Add cycle detection preflight that rejects insertions introducing circular dependencies.
- [ ] Preserve existing scheduling behavior for acyclic dependency graphs and independent tasks.
- [ ] Add tests for single-node self-cycle, multi-node cycle, and valid DAG scheduling acceptance.
      **Notes:** Early cycle rejection prevents stuck queues and opaque downstream scheduling failures.

### [WL-7943]

**Title:** Separate session launch failures between config hydration and runtime boot
**Source:** [thegent/src/thegent/session/launcher.py:72]
**Acceptance checklist:**

- [ ] Split launch exception handling into config-hydration errors and runtime-boot errors with distinct error types.
- [ ] Preserve successful session launch metadata emission and runtime identifier assignment.
- [ ] Add tests for invalid config payloads, runtime boot command failures, and successful launch completion.
      **Notes:** Stage-specific launch errors improve operator response when sessions fail to start.

### [WL-7944]

**Title:** Harden YAML frontmatter key normalization in task template rendering
**Source:** [thegent/src/thegent/task/template.py:54]
**Acceptance checklist:**

- [ ] Normalize and validate required frontmatter keys before template interpolation occurs.
- [ ] Preserve existing rendering output for already-valid template metadata.
- [ ] Add tests for missing required keys, mixed-case key aliases, and successful normalized rendering output.
      **Notes:** Key normalization prevents subtle template drift across manually authored task definitions.

### [WL-7945]

**Title:** Isolate MCP registry load errors from runtime capability negotiation
**Source:** [thegent/src/thegent/mcp/registry.py:143]
**Acceptance checklist:**

- [ ] Split registry initialization failures into file-load errors and capability-negotiation errors.
- [ ] Preserve successful provider registration behavior and existing capability match semantics.
- [ ] Add tests for missing registry entries, unsupported capability declarations, and successful registry startup.
      **Notes:** Distinct error boundaries make MCP startup regressions easier to localize and fix.

### [WL-7946]

**Title:** Enforce stable claim ordering in workstream assignment operations
**Source:** [thegent/src/thegent/commands/claim.py:121]
**Acceptance checklist:**

- [ ] Apply deterministic ordering when selecting claimable rows for lane-targeted assignment runs.
- [ ] Preserve existing claim conflict detection and already-claimed row protections.
- [ ] Add tests for mixed-status rows, repeated claim invocations, and stable assignment ordering.
      **Notes:** Stable claim order prevents cross-lane contention and inconsistent assignment outcomes.

### [WL-7947]

**Title:** Differentiate trace sink failures across buffer flush and filesystem commit
**Source:** [thegent/src/thegent/trace/sink.py:87]
**Acceptance checklist:**

- [ ] Replace broad sink write exception handling with explicit buffer-flush and file-commit error branches.
- [ ] Preserve successful trace event ordering and timestamp serialization behavior.
- [ ] Add tests for flush-time exceptions, commit-time write failures, and successful sink persistence.
      **Notes:** Trace durability bugs are easier to diagnose when flush and commit failures are separated.

### [WL-7948]

**Title:** Validate shell command tokenization boundaries before process spawn
**Source:** [thegent/src/thegent/shell/runner.py:109]
**Acceptance checklist:**

- [ ] Add pre-spawn token boundary validation that rejects empty, null, and unsafe token sequences.
- [ ] Preserve successful command execution for valid token arrays and environment inheritance rules.
- [ ] Add tests for empty command inputs, malformed quoting splits, and successful spawn execution.
      **Notes:** Token boundary validation avoids ambiguous shell behavior and hard-to-debug spawn errors.

### [WL-7949]

**Title:** Split transport retry failures between backoff scheduling and dispatch execution
**Source:** [thegent/src/thegent/infra/retry_transport.py:66]
**Acceptance checklist:**

- [ ] Separate retry pipeline failure handling into backoff-schedule errors and dispatch-execution errors.
- [ ] Preserve successful retry attempt accounting and maximum-attempt cutoff behavior.
- [ ] Add tests for scheduler initialization faults, dispatch failure propagation, and successful retry completion.
      **Notes:** Retry telemetry should reveal whether failure occurs in timing control or actual transport dispatch.
