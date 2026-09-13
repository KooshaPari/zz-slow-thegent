### [WL-7680]

**Title:** Separate remote compute client creation failures from request execution failures
**Source:** [thegent/src/thegent/research/remote_compute.py:60]
**Acceptance checklist:**

- [ ] Replace broad remote compute exception capture with explicit client-init and request-execution branches.
- [ ] Preserve successful remote compute result handling and output shape.
- [ ] Add tests for client construction failure, request transport failure, and successful execution.
      **Notes:** Line 60 currently collapses distinct remote compute failure classes into one generic error path.

### [WL-7681]

**Title:** Preserve endpoint probe diagnostics by classifying health-check transport and decode errors
**Source:** [thegent/src/thegent/research/remote_compute.py:102]
**Acceptance checklist:**

- [ ] Replace catch-all endpoint probe handling with explicit timeout, connection, and response-decode branches.
- [ ] Preserve current healthy-endpoint fast path behavior.
- [ ] Add tests for timeout probes, malformed probe payloads, and healthy responses.
      **Notes:** Line 102 currently emits a single failure shape for unrelated endpoint probe issues.

### [WL-7682]

**Title:** Keep conversation dump export failures typed across JSON serialization and file I/O stages
**Source:** [thegent/src/thegent/session/conversation_dumper.py:163]
**Acceptance checklist:**

- [ ] Replace broad dump exception handling with explicit serialization and file-write failure branches.
- [ ] Preserve successful conversation export file content and naming behavior.
- [ ] Add tests for non-serializable payloads, write-permission errors, and successful exports.
      **Notes:** Line 163 currently masks whether dump failures come from payload encoding or filesystem writes.

### [WL-7683]

**Title:** Split transcript copy failures between source-read and destination-write operations
**Source:** [thegent/src/thegent/session/conversation_dumper.py:215]
**Acceptance checklist:**

- [ ] Replace generic transcript copy exception handling with explicit source-read and destination-write diagnostics.
- [ ] Preserve copy continuation behavior for valid transcript files.
- [ ] Add tests for missing source transcripts, unwritable destination paths, and successful copy operations.
      **Notes:** Line 215 currently reports one broad failure mode across different transcript copy stages.

### [WL-7684]

**Title:** Preserve archive generation observability by separating compression and manifest-write failures
**Source:** [thegent/src/thegent/session/conversation_dumper.py:342]
**Acceptance checklist:**

- [ ] Replace broad archive error handling with explicit compression and manifest-write failure categories.
- [ ] Preserve successful archive output structure and metadata contract.
- [ ] Add tests for compression failures, manifest write failures, and successful archive generation.
      **Notes:** Line 342 currently funnels heterogeneous archive failures through one generic handler.

### [WL-7685]

**Title:** Classify terminal pane bootstrap failures before fallback rendering kicks in
**Source:** [thegent/src/thegent/compositor/terminal_pane.py:83]
**Acceptance checklist:**

- [ ] Replace broad pane bootstrap exception handling with explicit PTY setup, layout-init, and render-init branches.
- [ ] Preserve successful terminal pane initialization behavior.
- [ ] Add tests for PTY setup failure, layout initialization failure, and successful bootstrap.
      **Notes:** Line 83 currently hides which bootstrap stage failed during terminal pane startup.

### [WL-7686]

**Title:** Differentiate pane resize path failures from redraw failures in terminal compositor loop
**Source:** [thegent/src/thegent/compositor/terminal_pane.py:105]
**Acceptance checklist:**

- [ ] Replace catch-all resize-loop handling with explicit resize-operation and redraw-operation diagnostics.
- [ ] Preserve normal resize and redraw behavior under healthy conditions.
- [ ] Add tests for resize syscall failure, redraw exception, and successful resize cycle.
      **Notes:** Line 105 currently conflates resize and redraw failures into one broad error class.

### [WL-7687]

**Title:** Keep session-state recovery diagnostics explicit for parse, schema, and persistence failures
**Source:** [thegent/src/thegent/compositor/session_state.py:52]
**Acceptance checklist:**

- [ ] Replace generic session-state recovery catch with explicit parse, schema-shape, and persistence-write branches.
- [ ] Preserve successful session-state restore behavior and defaults.
- [ ] Add tests for malformed state payloads, invalid schema content, and successful restoration.
      **Notes:** Line 52 currently suppresses root-cause detail across multiple recovery failure stages.

### [WL-7688]

**Title:** Maintain typed error paths for session-state checkpoint updates under concurrent writes
**Source:** [thegent/src/thegent/compositor/session_state.py:73]
**Acceptance checklist:**

- [ ] Replace broad checkpoint update exception handling with explicit lock-acquisition, merge, and write failure branches.
- [ ] Preserve current checkpoint success semantics for non-contentious writes.
- [ ] Add tests for lock contention failures, merge conflicts, and successful checkpoint updates.
      **Notes:** Line 73 currently obscures whether checkpoint update failures stem from contention or persistence logic.

### [WL-7689]

**Title:** Surface cache pre-warm outcome failures by splitting probe, transform, and emit stages
**Source:** [thegent/src/thegent/cache/pre_warmer.py:170]
**Acceptance checklist:**

- [ ] Replace broad pre-warm exception handling with explicit probe-read, transform, and cache-emit branches.
- [ ] Preserve successful pre-warm flow and existing result counters.
- [ ] Add tests for probe source failure, transform failure, and successful pre-warm execution.
      **Notes:** Line 170 currently collapses multiple pre-warm pipeline failures into one generic message.
