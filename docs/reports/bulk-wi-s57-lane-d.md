### [WL-8400]

**Title:** Preserve API heartbeat by separating heartbeat payload generation and scheduler dispatch
**Source:** [thegent/src/thegent/health/heartbeat.py:411]
**Acceptance checklist:**

- [ ] Separate heartbeat payload generation failures from scheduler dispatch failures.
- [ ] Keep dispatch metrics available during payload fallback.
- [ ] Add tests for payload and dispatch branch behavior.
      **Notes:** Helps detect infrastructure issues without dropping health flow.

### [WL-8401]

**Title:** Preserve prompt caching by separating token budget estimation and cache write
**Source:** [thegent/src/thegent/prompt/cache.py:367]
**Acceptance checklist:**

- [ ] Separate token budget estimation failures from cache write failures.
- [ ] Preserve prompt cache read behavior when writes fail.
- [ ] Add tests for estimation and cache-write branches.
      **Notes:** Keeps prompt optimization stable under high traffic.

### [WL-8402]

**Title:** Preserve notification dedup by separating fingerprint generation and dedup index lookup
**Source:** [thegent/src/thegent/notifications/dedup.py:299]
**Acceptance checklist:**

- [ ] Separate fingerprint generation failures from dedup index lookup failures.
- [ ] Preserve basic dedup flow when fingerprinting fails.
- [ ] Add tests for fingerprint and lookup branches.
      **Notes:** Reduces duplicate notifications during fingerprint subsystem flaps.

### [WL-8403]

**Title:** Preserve stream replay by separating cursor storage and replay chunking
**Source:** [thegent/src/thegent/stream/replay.py:444]
**Acceptance checklist:**

- [ ] Distinguish cursor persistence failures from replay chunk assembly failures.
- [ ] Preserve chunk replay progress with in-memory cursor fallback.
- [ ] Add tests for persistence and chunking branches.
      **Notes:** Improves recovery for intermittent cursor store outages.

### [WL-8404]

**Title:** Preserve artifact indexing by separating path normalization and index rebuild
**Source:** [thegent/src/thegent/artifacts/indexer.py:528]
**Acceptance checklist:**

- [ ] Separate path normalization failures from index rebuild operations.
- [ ] Preserve index state when rebuild cannot complete.
- [ ] Add tests for normalization and rebuild branch outcomes.
      **Notes:** Helps avoid expensive full rebuild on path parsing noise.

### [WL-8405]

**Title:** Preserve API contract validation by separating spec load and payload validation
**Source:** [thegent/src/thegent/api/contract.py:381]
**Acceptance checklist:**

- [ ] Separate API spec load failures from payload validation failures.
- [ ] Preserve strict payload checks with cached specs.
- [ ] Add tests for load and validation branches.
      **Notes:** Keeps API reliability under spec storage pressure.

### [WL-8406]

**Title:** Preserve event fanout by separating message batch partition and consumer wake logic
**Source:** [thegent/src/thegent/events/fanout.py:491]
**Acceptance checklist:**

- [ ] Separate message batch partition failures from consumer wake failures.
- [ ] Keep fanout available with fallback partitioning.
- [ ] Add tests for partition and wake branches.
      **Notes:** Improves throughput under partial consumer-side degradation.

### [WL-8407]

**Title:** Preserve CLI history persistence by separating command line normalization and storage append
**Source:** [thegent/src/thegent/cli/history.py:422]
**Acceptance checklist:**

- [ ] Separate history input normalization failures from storage append failures.
- [ ] Preserve in-memory history if append path is unavailable.
- [ ] Add tests for normalization and persistence branches.
      **Notes:** Helps command recall remain useful despite storage hiccups.

### [WL-8408]

**Title:** Preserve session token propagation by separating token source detection and forwarding
**Source:** [thegent/src/thegent/sessions/token_forward.py:358]
**Acceptance checklist:**

- [ ] Separate token source detection failures from forwarding failures.
- [ ] Preserve forwarding semantics with fallback token source.
- [ ] Add tests for detection and forwarding branch behavior.
      **Notes:** Reduces auth regressions during source metadata changes.

### [WL-8409]

**Title:** Preserve artifact compression by separating chunk boundary detection and compressor init
**Source:** [thegent/src/thegent/artifacts/compress.py:512]
**Acceptance checklist:**

- [ ] Separate compression chunk boundary failures from compressor initialization failures.
- [ ] Preserve streaming compression on boundary detection failures.
- [ ] Add tests for chunk and compressor initialization branches.
      **Notes:** Improves artifact upload consistency with large payloads.
