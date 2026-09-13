### [WL-8610]

**Title:** Preserve queue checkpointing by separating checkpoint ID parse and checkpoint persistence
**Source:** [thegent/src/thegent/queue/checkpoint_writer.py:333]
**Acceptance checklist:**

- [ ] Separate checkpoint ID parse failures from persistence failures.
- [ ] Preserve checkpoint continuity with parse fallback.
- [ ] Add tests for ID parse and persistence branches.
      **Notes:** Improves queue reliability when checkpoint metadata is inconsistent.

### [WL-8611]

**Title:** Preserve config diff sync by separating diff parse and diff apply
**Source:** [thegent/src/thegent/config/diff_sync.py:512]
**Acceptance checklist:**

- [ ] Separate config diff parse failures from diff application failures.
- [ ] Preserve diff apply fallback semantics.
- [ ] Add tests for parse and apply branch failures.
      **Notes:** Improves config synchronization under drifted diff formats.

### [WL-8612]

**Title:** Preserve command context binding by separating context schema parse and context merge
**Source:** [thegent/src/thegent/commands/context_manager.py:451]
**Acceptance checklist:**

- [ ] Separate command context schema failures from context merge failures.
- [ ] Preserve context merge with schema fallback.
- [ ] Add tests for schema and merge branch behavior.
      **Notes:** Reduces command failures from one malformed context payload.

### [WL-8613]

**Title:** Preserve route resolution by separating route expression parsing and resolution map lookup
**Source:** [thegent/src/thegent/routing/resolver.py:589]
**Acceptance checklist:**

- [ ] Separate route expression parse failures from map lookup failures.
- [ ] Preserve resolution fallback on parse errors.
- [ ] Add tests for parse and lookup branches.
      **Notes:** Keeps navigation functional with partial route grammar issues.

### [WL-8614]

**Title:** Preserve artifact cache indexing by separating file metadata parse and index enqueue
**Source:** [thegent/src/thegent/artifacts/cache_index.py:378]
**Acceptance checklist:**

- [ ] Separate file metadata parse failures from index enqueue failures.
- [ ] Preserve indexing pipeline with metadata fallback.
- [ ] Add tests for parse and enqueue branches.
      **Notes:** Prevents index backlog growth from malformed file metadata.

### [WL-8615]

**Title:** Preserve sync scheduler by separating schedule parse and schedule persistence
**Source:** [thegent/src/thegent/sync/scheduler_config.py:512]
**Acceptance checklist:**

- [ ] Separate schedule parse failures from schedule persistence failures.
- [ ] Preserve scheduling defaults with parse fallback.
- [ ] Add tests for parse and persistence branches.
      **Notes:** Maintains sync cadence under schedule schema changes.

### [WL-8616]

**Title:** Preserve artifact retrieval by separating artifact key parse and artifact lookup
**Source:** [thegent/src/thegent/artifacts/retrieval.py:331]
**Acceptance checklist:**

- [ ] Separate artifact key parse failures from artifact lookup failures.
- [ ] Preserve retrieval attempts with key fallback parsing.
- [ ] Add tests for key and lookup branches.
      **Notes:** Reduces retrieval breakages when one key format drifts.

### [WL-8617]

**Title:** Preserve command retry telemetry by separating retry reason extraction and telemetry write
**Source:** [thegent/src/thegent/commands/retry_telemetry.py:478]
**Acceptance checklist:**

- [ ] Separate retry reason extraction failures from telemetry write failures.
- [ ] Preserve retry logging with reason fallback.
- [ ] Add tests for reason extraction and telemetry write branches.
      **Notes:** Improves reliability of retry analytics during schema irregularities.

### [WL-8618]

**Title:** Preserve policy enforcement logs by separating policy hit parse and log format adaptation
**Source:** [thegent/src/thegent/policies/enforce_logs.py:501]
**Acceptance checklist:**

- [ ] Separate policy hit parse failures from log format adaptation failures.
- [ ] Preserve enforcement logs with adaptive fallback format.
- [ ] Add tests for parse and format adaptation branches.
      **Notes:** Keeps enforcement visibility during log schema migrations.

### [WL-8619]

**Title:** Preserve artifact lifecycle by separating lifecycle event parse and lifecycle transition
**Source:** [thegent/src/thegent/artifacts/lifecycle.py:441]
**Acceptance checklist:**

- [ ] Separate lifecycle event parse failures from transition execution failures.
- [ ] Preserve lifecycle transitions with parse fallback.
- [ ] Add tests for event parse and transition branch failures.
      **Notes:** Improves lifecycle consistency under event format changes.
