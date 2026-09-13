### [WL-7890]

**Title:** Separate provider selection failures between capability filtering and priority ranking phases
**Source:** [thegent/src/thegent/providers/selector.py:92]
**Acceptance checklist:**

- [ ] Replace generic selection failure handling with explicit capability-filter and priority-ranking branches.
- [ ] Preserve successful provider ordering and tie-break semantics for valid candidate sets.
- [ ] Add tests for empty capability matches, ranking comparator failures, and successful provider selection.
      **Notes:** Line 92 is in selector flow where merged failure paths obscure whether filtering or ranking failed.

### [WL-7891]

**Title:** Enforce structured config decode errors for missing keys versus invalid value types
**Source:** [thegent/src/thegent/config/decode.py:61]
**Acceptance checklist:**

- [ ] Replace catch-all config decode failures with explicit missing-key and invalid-type error branches.
- [ ] Preserve successful decode output schema and default-value behavior for valid payloads.
- [ ] Add tests for missing required keys, wrong value types, and successful config decode.
      **Notes:** Line 61 is in decode entry where typed failures should identify shape versus type defects.

### [WL-7892]

**Title:** Split transcript streaming faults between chunk read and emitter flush stages
**Source:** [thegent/src/thegent/session/transcript_stream.py:144]
**Acceptance checklist:**

- [ ] Replace broad stream exceptions with explicit chunk-read and emitter-flush branches.
- [ ] Preserve successful transcript chunk ordering and final flush semantics.
- [ ] Add tests for read interruption, flush write errors, and successful streaming completion.
      **Notes:** Line 144 is in stream loop where combined errors hide read-path versus flush-path failures.

### [WL-7893]

**Title:** Differentiate command execution failures across argument binding and subprocess launch paths
**Source:** [thegent/src/thegent/commands/executor.py:128]
**Acceptance checklist:**

- [ ] Replace generic execution error handling with explicit argument-binding and subprocess-launch branches.
- [ ] Preserve successful command invocation payload and exit-code propagation behavior.
- [ ] Add tests for invalid argument mapping, launch failures, and successful command execution.
      **Notes:** Line 128 is in execution path where diagnostics should reveal binding defects versus launch failures.

### [WL-7894]

**Title:** Classify cache eviction faults between candidate scoring and storage delete operations
**Source:** [thegent/src/thegent/cache/eviction.py:173]
**Acceptance checklist:**

- [ ] Replace catch-all eviction failures with explicit candidate-scoring and storage-delete branches.
- [ ] Preserve successful eviction ordering and retained-entry integrity.
- [ ] Add tests for scorer errors, delete write failures, and successful eviction cycles.
      **Notes:** Line 173 is in eviction control flow where merged errors block targeted remediation.

### [WL-7895]

**Title:** Separate MCP tool manifest validation errors between schema checks and permission checks
**Source:** [thegent/src/thegent/mcp/tool_manifest.py:107]
**Acceptance checklist:**

- [ ] Replace broad manifest validation failures with explicit schema-validation and permission-validation branches.
- [ ] Preserve successful manifest load output and tool visibility mapping.
- [ ] Add tests for malformed schema fields, denied permission scopes, and successful manifest validation.
      **Notes:** Line 107 is in manifest validation where typed failures should isolate structural and policy defects.

### [WL-7896]

**Title:** Split worktree sync failures between fetch reconciliation and patch apply stages
**Source:** [thegent/src/thegent/worktree/sync.py:189]
**Acceptance checklist:**

- [ ] Replace generic sync failure handling with explicit fetch-reconciliation and patch-apply branches.
- [ ] Preserve successful sync ordering and resulting tree cleanliness guarantees.
- [ ] Add tests for divergent fetch states, patch apply conflicts, and successful sync runs.
      **Notes:** Line 189 is in sync flow where diagnosis needs clear transport-versus-apply fault boundaries.

### [WL-7897]

**Title:** Differentiate metrics emission errors for serialization versus transport publish phases
**Source:** [thegent/src/thegent/monitoring/metrics_emitter.py:76]
**Acceptance checklist:**

- [ ] Replace catch-all emitter exceptions with explicit metric-serialization and transport-publish branches.
- [ ] Preserve successful metric name, label, and value emission semantics.
- [ ] Add tests for serialization failures, publish transport errors, and successful metric emission.
      **Notes:** Line 76 is in metrics output path where collapsed errors prevent rapid root-cause isolation.

### [WL-7898]

**Title:** Enforce session lock acquisition timeouts with separate queue wait and lock write error types
**Source:** [thegent/src/thegent/session/locks.py:134]
**Acceptance checklist:**

- [ ] Replace broad lock acquisition failures with explicit queue-wait-timeout and lock-write-error branches.
- [ ] Preserve successful lock ownership metadata and renewal behavior.
- [ ] Add tests for wait timeout, persistence write failure, and successful lock acquisition.
      **Notes:** Line 134 is in lock acquisition where typed outcomes are needed for contention diagnostics.

### [WL-7899]

**Title:** Classify report export failures between template render and artifact persist stages
**Source:** [thegent/src/thegent/reports/export.py:158]
**Acceptance checklist:**

- [ ] Replace generic export failures with explicit template-render and artifact-persist branches.
- [ ] Preserve successful export artifact naming and metadata emission behavior.
- [ ] Add tests for render exceptions, persist write failures, and successful export completion.
      **Notes:** Line 158 is in export pipeline where bundled errors mask whether rendering or persistence failed.
