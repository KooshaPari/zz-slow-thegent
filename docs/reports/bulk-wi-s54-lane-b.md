### [WL-8230]

**Title:** Split control-plane auth config and token validation failures
**Source:** [thegent/src/thegent/control_plane/server.py:418]
**Acceptance checklist:**

- [ ] Separate invalid token parsing from auth handshake failures.
- [ ] Preserve auth failure response contract.
- [ ] Add tests for token parse and handshake failures.
      **Notes:** Reduces ambiguity in control-plane security incidents.

### [WL-8231]

**Title:** Preserve dashboard rendering while separating state decode and render crashes
**Source:** [thegent/src/thegent/mesh/cli.py:288]
**Acceptance checklist:**

- [ ] Distinguish state payload decode errors from render exceptions.
- [ ] Keep stale-state fallback render behavior on decode errors.
- [ ] Add tests for decode and render failures.
      **Notes:** Prevents full dashboard failure on isolated decode issues.

### [WL-8232]

**Title:** Preserve queue scaling decisions while separating metric fetch and policy eval
**Source:** [thegent/src/thegent/queue/scaler.py:222]
**Acceptance checklist:**

- [ ] Separate metrics fetch exceptions from policy evaluation exceptions.
- [ ] Preserve scaling fallback when metric fetch fails.
- [ ] Add tests for each failure branch.
      **Notes:** Reduces blast radius of transient metrics issues.

### [WL-8233]

**Title:** Preserve borrower proxy handling while splitting proxy config load and call failures
**Source:** [thegent/src/thegent/tools/borrow.py:627]
**Acceptance checklist:**

- [ ] Handle missing/malformed proxy config separately from proxy call failures.
- [ ] Preserve borrow flow when call errors are retryable.
- [ ] Add tests for malformed config and proxy transport errors.
      **Notes:** Enables faster classification of connectivity issues.

### [WL-8234]

**Title:** Preserve artifact uploader by separating endpoint selection and send failures
**Source:** [thegent/src/thegent/artifacts/uploader.py:401]
**Acceptance checklist:**

- [ ] Split endpoint selection resolution from network send exceptions.
- [ ] Preserve retry strategy for send failures.
- [ ] Add tests for bad endpoint config and network timeouts.
      **Notes:** Prevents endpoint misselection from hiding send failures.

### [WL-8235]

**Title:** Preserve shell completion cache while isolating stale-state and serialization errors
**Source:** [thegent/src/thegent/shell_cli.py:742]
**Acceptance checklist:**

- [ ] Add separate handling for stale cache entries and serialization exceptions.
- [ ] Keep completion output available with fallback rebuild.
- [ ] Add tests for stale and corrupt cache cases.
      **Notes:** Improves CLI responsiveness under cache drift.

### [WL-8236]

**Title:** Preserve settings migration by separating parse and migration execution failures
**Source:** [thegent/src/thegent/config/settings.py:352]
**Acceptance checklist:**

- [ ] Split migration file parse errors from patch execution failures.
- [ ] Keep existing migration rollback behavior.
- [ ] Add tests for invalid migration format and execution exceptions.
      **Notes:** Improves startup resilience and diagnosability.

### [WL-8237]

**Title:** Preserve agent startup telemetry while separating process spawn and handshake failures
**Source:** [thegent/src/thegent/agents/starter.py:152]
**Acceptance checklist:**

- [ ] Add explicit branch for process spawn failures.
- [ ] Add explicit branch for runtime handshake failures.
- [ ] Add tests for each branch.
      **Notes:** Removes uncertainty in startup failure triage.

### [WL-8238]

**Title:** Preserve queue persistence while separating write contention and corrupted payloads
**Source:** [thegent/src/thegent/queue/state.py:242]
**Acceptance checklist:**

- [ ] Separate lock/contention failures from corrupted payload decoding.
- [ ] Preserve queue operation on payload corruption with fallback.
- [ ] Add tests for lock contention and corrupt payload.
      **Notes:** Improves queue reliability under mixed storage faults.

### [WL-8239]

**Title:** Preserve artifact collector safety while separating metadata parse and collection IO
**Source:** [thegent/src/thegent/artifacts/collector.py:301]
**Acceptance checklist:**

- [ ] Separate metadata decode failures from filesystem read/write errors.
- [ ] Preserve collector loop with tolerant handling for each case.
- [ ] Add tests for invalid metadata and IO errors.
      **Notes:** Reduces full-collector drops on partial failures.
