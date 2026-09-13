### [WL-8160]

**Title:** Separate queue state staleness checks from update persistence failures
**Source:** [thegent/src/thegent/queue/state.py:61]
**Acceptance checklist:**

- [ ] Distinguish stale-state detection failures from state-write failures.
- [ ] Preserve enqueue/dequeue behavior when persistence fails.
- [ ] Add tests for stale metadata and persistence exceptions.
      **Notes:** Maintains throughput during intermittent persistence failures.

### [WL-8161]

**Title:** Preserve session bootstrap behavior while separating environment validation stages
**Source:** [thegent/src/thegent/session/bootstrap.py:205]
**Acceptance checklist:**

- [ ] Split required-environment checks from optional env defaults.
- [ ] Preserve bootstrap defaults on optional checks.
- [ ] Add tests for missing required env and invalid optional env.
      **Notes:** Improves error clarity without reducing bootstrap resilience.

### [WL-8162]

**Title:** Separate task planner graph validation from execution order calculation errors
**Source:** [thegent/src/thegent/planner/dag.py:472]
**Acceptance checklist:**

- [ ] Add explicit branches for graph schema validation and topological calculation failures.
- [ ] Preserve planner output contract on recoverable failures.
- [ ] Add tests for schema violations and topological edge failures.
      **Notes:** Supports faster root-cause in pipeline authoring issues.

### [WL-8163]

**Title:** Preserve borrow command dispatch while splitting config lookup from runtime command failures
**Source:** [thegent/src/thegent/tools/borrow.py:418]
**Acceptance checklist:**

- [ ] Handle missing config and malformed config separately from command execution failures.
- [ ] Keep dispatch return structures unchanged.
- [ ] Add tests for config-missing and runtime exceptions.
      **Notes:** Better separates setup failures from tool run failures.

### [WL-8164]

**Title:** Preserve artifact retention safety while separating retention predicate and deletion failures
**Source:** [thegent/src/thegent/artifacts/retention.py:212]
**Acceptance checklist:**

- [ ] Split predicate evaluation errors from deletion operation exceptions.
- [ ] Preserve all retention records when predicate cannot be evaluated.
- [ ] Add tests for predicate errors and delete exceptions.
      **Notes:** Helps avoid unintended data retention drift.

### [WL-8165]

**Title:** Preserve startup metrics behavior while separating metric serialization from transport send
**Source:** [thegent/src/thegent/telemetry/metrics_sink.py:112]
**Acceptance checklist:**

- [ ] Distinguish serialization failures from send-time transport failures.
- [ ] Preserve local metric cache behavior on transient transport issues.
- [ ] Add tests for invalid metric payload and send errors.
      **Notes:** Keeps telemetry useful during partial system degradation.

### [WL-8166]

**Title:** Separate mesh state refresh parse errors from state update failures
**Source:** [thegent/src/thegent/mesh/control.py:468]
**Acceptance checklist:**

- [ ] Handle malformed mesh state payloads distinctly from state write failures.
- [ ] Preserve dashboard stale-state fallback for parse errors.
- [ ] Add tests for malformed state and write failures.
      **Notes:** Improves resilience of mesh status updates.

### [WL-8167]

**Title:** Preserve shell completion behavior while separating parser and cache errors
**Source:** [thegent/src/thegent/shell_cli.py:556]
**Acceptance checklist:**

- [ ] Isolate parser grammar failures from completion cache read/write issues.
- [ ] Keep completion fallback when parser errors occur.
- [ ] Add tests for parser exceptions and cache IO failures.
      **Notes:** Reduces completion regressions from unrelated parser anomalies.

### [WL-8168]

**Title:** Keep clipboard history export robust with explicit encoding error handling
**Source:** [thegent/src/thegent/clipboard/history.py:212]
**Acceptance checklist:**

- [ ] Distinguish file encoding errors from history format errors.
- [ ] Preserve export behavior with fallback encoding when possible.
- [ ] Add tests for bad encoding and malformed history blobs.
      **Notes:** Prevents dropped exports due to locale/env differences.

### [WL-8169]

**Title:** Preserve conversation metadata extraction while splitting metadata parse and parse-time lookup
**Source:** [thegent/src/thegent/session/conversation_dumper.py:289]
**Acceptance checklist:**

- [ ] Separate metadata JSON parse errors from lookup of referenced keys.
- [ ] Keep metadata extraction output contract on recoverable lookup failures.
- [ ] Add tests for malformed metadata and missing key lookups.
      **Notes:** Improves diagnostics for conversation export pipelines.
