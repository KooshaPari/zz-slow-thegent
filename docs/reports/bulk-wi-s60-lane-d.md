### [WL-8550]

**Title:** Preserve CLI completion by separating command source inventory and completion rendering
**Source:** [thegent/src/thegent/shell_cli/complete.py:511]
**Acceptance checklist:**

- [ ] Separate command source inventory failures from completion rendering failures.
- [ ] Preserve completion fallback for source inventory errors.
- [ ] Add tests for inventory and rendering branches.
      **Notes:** Keeps completion reliable with partial source discovery issues.

### [WL-8551]

**Title:** Preserve artifact manifest signing by separating signer selection and signature creation
**Source:** [thegent/src/thegent/artifacts/signing.py:333]
**Acceptance checklist:**

- [ ] Separate signer selection failures from signature creation failures.
- [ ] Preserve signature pipeline with fallback signer selection.
- [ ] Add tests for signer selection and signature branches.
      **Notes:** Improves artifact integrity flow during signer outages.

### [WL-8552]

**Title:** Preserve queue priority balancing by separating priority compute and queue reorder
**Source:** [thegent/src/thegent/queue/priority.py:447]
**Acceptance checklist:**

- [ ] Separate priority computation failures from queue reorder failures.
- [ ] Preserve queue processing on priority compute fallback.
- [ ] Add tests for compute and reorder branches.
      **Notes:** Maintains fairness when priority data is noisy.

### [WL-8553]

**Title:** Preserve session export by separating export selector and content serializer
**Source:** [thegent/src/thegent/session/exporter.py:589]
**Acceptance checklist:**

- [ ] Separate export selector failures from content serializer failures.
- [ ] Preserve export output with selector fallback behavior.
- [ ] Add tests for selector and serializer branches.
      **Notes:** Keeps session portability available despite selector regressions.

### [WL-8554]

**Title:** Preserve policy checks by separating policy compile and runtime check execution
**Source:** [thegent/src/thegent/policies/checker.py:378]
**Acceptance checklist:**

- [ ] Separate policy compile failures from runtime check execution failures.
- [ ] Preserve runtime checks with compile fallback.
- [ ] Add tests for compile and execution branches.
      **Notes:** Prevents runtime lockups from one policy compiler issue.

### [WL-8555]

**Title:** Preserve event fanout health by separating fanout list parse and fanout dispatch
**Source:** [thegent/src/thegent/events/fanout_health.py:399]
**Acceptance checklist:**

- [ ] Separate fanout list parse failures from fanout dispatch failures.
- [ ] Preserve dispatch attempt with list fallback.
- [ ] Add tests for parse and dispatch branch handling.
      **Notes:** Improves event throughput while isolating parse defects.

### [WL-8556]

**Title:** Preserve queue metrics by separating counter read and counter publish
**Source:** [thegent/src/thegent/queue/metrics_publisher.py:412]
**Acceptance checklist:**

- [ ] Separate queue counter read failures from counter publish failures.
- [ ] Preserve publish attempts with read fallback.
- [ ] Add tests for read and publish branches.
      **Notes:** Keeps queue observability usable under backend noise.

### [WL-8557]

**Title:** Preserve config precedence by separating env precedence parse and precedence merge
**Source:** [thegent/src/thegent/config/precedence.py:512]
**Acceptance checklist:**

- [ ] Separate precedence parse failures from precedence merge failures.
- [ ] Preserve environment-level precedence on merge issues.
- [ ] Add tests for parse and merge branches.
      **Notes:** Stabilizes config behavior under mixed precedence formats.

### [WL-8558]

**Title:** Preserve artifact transfer by separating transfer intent and transfer execution
**Source:** [thegent/src/thegent/artifacts/transfer.py:531]
**Acceptance checklist:**

- [ ] Separate transfer intent parsing failures from transfer execution failures.
- [ ] Preserve transfer execution on intent parsing fallback.
- [ ] Add tests for intent and execution branch behavior.
      **Notes:** Improves resilience for cross-system artifact moves.

### [WL-8559]

**Title:** Preserve API pagination by separating page token decode and page fetch
**Source:** [thegent/src/thegent/api/pagination.py:355]
**Acceptance checklist:**

- [ ] Separate page token decode failures from page fetch failures.
- [ ] Preserve previous pages on decode failures.
- [ ] Add tests for decode and fetch branches.
      **Notes:** Keeps data sync flows stable when token formats evolve.
