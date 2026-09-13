### [WL-7990]

**Title:** Separate registry bootstrap failures between file discovery and schema hydration
**Source:** [thegent/src/thegent/registry/bootstrap.py:84]
**Acceptance checklist:**

- [ ] Replace catch-all bootstrap exceptions with explicit file-discovery and schema-hydration failure branches.
- [ ] Preserve successful registry load ordering and existing default namespace behavior.
- [ ] Add tests for missing manifest files, malformed schema payloads, and successful bootstrap completion.
      **Notes:** Stage-specific diagnostics shorten triage cycles when registry startup fails.

### [WL-7991]

**Title:** Enforce deterministic command alias resolution before executor dispatch
**Source:** [thegent/src/thegent/commands/alias_resolver.py:57]
**Acceptance checklist:**

- [ ] Sort alias candidates by explicit precedence rules before selecting a dispatch target.
- [ ] Preserve current behavior for direct command invocations without aliases.
- [ ] Add tests for duplicate aliases, precedence ties, and stable repeated-resolution output.
      **Notes:** Deterministic alias selection prevents inconsistent command routing across runs.

### [WL-7992]

**Title:** Split task graph expansion faults between node materialization and edge linking
**Source:** [thegent/src/thegent/task/graph_builder.py:133]
**Acceptance checklist:**

- [ ] Replace broad graph-build exception handling with explicit node-materialization and edge-linking branches.
- [ ] Preserve successful graph topology output for valid task definitions.
- [ ] Add tests for invalid node payloads, dangling dependency edges, and successful graph expansion.
      **Notes:** Distinct fault classes make dependency graph issues faster to isolate.

### [WL-7993]

**Title:** Validate session transcript chunk boundaries before persistence append
**Source:** [thegent/src/thegent/session/transcript_store.py:71]
**Acceptance checklist:**

- [ ] Add pre-append chunk validation for empty payloads, invalid offsets, and timestamp regressions.
- [ ] Preserve successful transcript ordering and existing append-only write semantics.
- [ ] Add tests for malformed chunks, out-of-order offsets, and successful chunk persistence.
      **Notes:** Boundary checks prevent silent transcript corruption during long-running sessions.

### [WL-7994]

**Title:** Differentiate provider handshake failures across auth negotiation and capability sync
**Source:** [thegent/src/thegent/providers/handshake.py:146]
**Acceptance checklist:**

- [ ] Split handshake failure handling into auth-negotiation and capability-sync error branches.
- [ ] Preserve successful provider readiness state transitions and metadata capture.
- [ ] Add tests for token negotiation failures, capability mismatch responses, and successful handshakes.
      **Notes:** Isolated handshake diagnostics improve recovery behavior for partially healthy providers.

### [WL-7995]

**Title:** Harden cache key normalization before multi-tenant namespace lookup
**Source:** [thegent/src/thegent/cache/keyspace.py:49]
**Acceptance checklist:**

- [ ] Normalize and validate cache keys prior to namespace lookup to reject ambiguous or unsafe segments.
- [ ] Preserve existing cache hit behavior for already-valid keys and namespaces.
- [ ] Add tests for mixed-case keys, invalid separators, and successful normalized lookups.
      **Notes:** Key normalization reduces cross-tenant collision risk and unstable cache behavior.

### [WL-7996]

**Title:** Isolate queue drain errors between dequeue iteration and completion callbacks
**Source:** [thegent/src/thegent/task_queue/drain.py:98]
**Acceptance checklist:**

- [ ] Replace generic drain-loop exceptions with explicit dequeue-iteration and completion-callback branches.
- [ ] Preserve successful drain ordering and idempotent completion semantics.
- [ ] Add tests for dequeue source faults, callback failures, and successful full-drain cycles.
      **Notes:** Separation clarifies whether failures originate in queue mechanics or handler logic.

### [WL-7997]

**Title:** Enforce explicit CLI flag conflict checks in report generation entrypoint
**Source:** [thegent/src/thegent/reports/cli.py:112]
**Acceptance checklist:**

- [ ] Add preflight validation for mutually exclusive flags before invoking report build routines.
- [ ] Preserve successful argument parsing and default report profile behavior for valid invocations.
- [ ] Add tests for conflicting flags, missing required companions, and successful generation paths.
      **Notes:** Early conflict detection avoids expensive no-op report runs with ambiguous output.

### [WL-7998]

**Title:** Separate tool invocation failures between argument coercion and runtime execution
**Source:** [thegent/src/thegent/tools/invoker.py:159]
**Acceptance checklist:**

- [ ] Split invocation failure handling into argument-coercion and runtime-execution categories.
- [ ] Preserve successful tool result serialization and existing stderr/stdout capture behavior.
- [ ] Add tests for invalid argument payloads, runtime exceptions, and successful tool execution.
      **Notes:** Typed failure boundaries improve observability for tool-call regressions.

### [WL-7999]

**Title:** Stabilize markdown table rewrite ordering in workstream completion updates
**Source:** [thegent/src/thegent/commands/workstream_update.py:203]
**Acceptance checklist:**

- [ ] Apply deterministic row ordering when rewriting BACKLOG tables after completion state updates.
- [ ] Preserve existing completion marker semantics and untouched non-BACKLOG sections.
- [ ] Add tests for repeated completion operations, mixed-status rows, and byte-stable table rewrites.
      **Notes:** Stable rewrites minimize noisy diffs and reduce merge conflict frequency.
