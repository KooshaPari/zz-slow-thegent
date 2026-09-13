### [WL-8590]

**Title:** Preserve sync audit by separating audit source parse and audit sink formatting
**Source:** [thegent/src/thegent/sync/audit.py:412]
**Acceptance checklist:**

- [ ] Separate sync audit source parsing failures from sink formatting failures.
- [ ] Preserve audit emission with source fallback.
- [ ] Add tests for parsing and formatting branches.
      **Notes:** Helps keep audit continuity despite occasional source schema shifts.

### [WL-8591]

**Title:** Preserve queue backpressure control by separating backlog detection and release signaling
**Source:** [thegent/src/thegent/queue/backpressure.py:501]
**Acceptance checklist:**

- [ ] Separate backlog detection failures from release signaling failures.
- [ ] Preserve release signaling fallback under detection failures.
- [ ] Add tests for detection and release branches.
      **Notes:** Improves stability under bursty queue load.

### [WL-8592]

**Title:** Preserve command completion by separating completion key normalization and completion filter
**Source:** [thegent/src/thegent/cli/completion_filter.py:333]
**Acceptance checklist:**

- [ ] Separate completion key normalization failures from completion filter failures.
- [ ] Preserve completion list fallback when normalization fails.
- [ ] Add tests for normalization and filter branches.
      **Notes:** Keeps completion behavior consistent as key formats evolve.

### [WL-8593]

**Title:** Preserve policy rollout by separating policy package parse and rollout engine
**Source:** [thegent/src/thegent/policies/rollout.py:589]
**Acceptance checklist:**

- [ ] Separate policy package parse failures from rollout engine failures.
- [ ] Preserve rollout engine behavior with package fallback.
- [ ] Add tests for parse and rollout branches.
      **Notes:** Reduces policy rollout risk under packaging drift.

### [WL-8594]

**Title:** Preserve artifact upload retries by separating retry policy parse and retry scheduler
**Source:** [thegent/src/thegent/artifacts/retry_upload.py:359]
**Acceptance checklist:**

- [ ] Separate retry policy parse failures from retry scheduler failures.
- [ ] Preserve retry scheduling defaults on parse issues.
- [ ] Add tests for policy and scheduler branches.
      **Notes:** Prevents upload retry stalls under malformed policy payloads.

### [WL-8595]

**Title:** Preserve session lock by separating lock key derivation and lock acquisition
**Source:** [thegent/src/thegent/session/lock.py:522]
**Acceptance checklist:**

- [ ] Separate lock key derivation failures from lock acquisition failures.
- [ ] Preserve lock acquisition fallbacks with derived defaults.
- [ ] Add tests for derivation and acquisition branches.
      **Notes:** Improves session consistency in multi-process contention.

### [WL-8596]

**Title:** Preserve artifact metadata sync by separating metadata parser and metadata writer
**Source:** [thegent/src/thegent/artifacts/metadata_sync.py:478]
**Acceptance checklist:**

- [ ] Separate metadata parser failures from metadata writer failures.
- [ ] Preserve metadata writes with parser fallback behavior.
- [ ] Add tests for parser and writer branches.
      **Notes:** Helps metadata sync remain operational under format drift.

### [WL-8597]

**Title:** Preserve CLI completion fallback by separating fallback source and completion render
**Source:** [thegent/src/thegent/cli/completion_fallback.py:447]
**Acceptance checklist:**

- [ ] Separate fallback source failures from render failures.
- [ ] Preserve completion output with render fallback.
- [ ] Add tests for fallback source and render branches.
      **Notes:** Maintains command help behavior during one-source regressions.

### [WL-8598]

**Title:** Preserve health check scheduling by separating schedule parse and timer setup
**Source:** [thegent/src/thegent/health/scheduler.py:331]
**Acceptance checklist:**

- [ ] Separate health schedule parse failures from timer setup failures.
- [ ] Preserve health checks with timer defaults.
- [ ] Add tests for parse and timer setup branch failures.
      **Notes:** Keeps periodic health polling active under schedule format changes.

### [WL-8599]

**Title:** Preserve stream processor by separating event deserialize and state mutation
**Source:** [thegent/src/thegent/stream/processor.py:512]
**Acceptance checklist:**

- [ ] Separate stream event deserialization failures from state mutation failures.
- [ ] Preserve stream continuity with safe mutation fallback.
- [ ] Add tests for deserialize and mutation branches.
      **Notes:** Improves resilience to malformed stream messages.
