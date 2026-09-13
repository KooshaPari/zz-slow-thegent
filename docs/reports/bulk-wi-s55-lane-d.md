### [WL-8300]

**Title:** Keep command dispatcher stable by splitting registration parse and route registration failures
**Source:** [thegent/src/thegent/mesh/control.py:672]
**Acceptance checklist:**

- [ ] Distinguish route schema parse failures from registration runtime failures.
- [ ] Preserve dispatcher for valid routes.
- [ ] Add tests for parse and registration branches.
      **Notes:** Reduces accidental global dispatch outages.

### [WL-8301]

**Title:** Preserve clipboard sync behavior while separating key-rotation and transport exceptions
**Source:** [thegent/src/thegent/clipboard/history.py:458]
**Acceptance checklist:**

- [ ] Split key-rotation failures from transport sync failures.
- [ ] Preserve sync loop with fallback on key issues.
- [ ] Add tests for key and transport failure modes.
      **Notes:** Improves resilience across crypto key rollovers.

### [WL-8302]

**Title:** Preserve queue claim metrics while separating scan and commit failures
**Source:** [thegent/src/thegent/queue/claim.py:491]
**Acceptance checklist:**

- [ ] Separate claim scan exceptions from commit persistence exceptions.
- [ ] Keep queue metrics available when commit fails.
- [ ] Add tests for scan and commit failures.
      **Notes:** Improves partial recovery behavior under storage load.

### [WL-8303]

**Title:** Preserve process-compose restart behavior by separating status check and command failures
**Source:** [thegent/src/thegent/process_compose/watcher.py:338]
**Acceptance checklist:**

- [ ] Handle status-check failures separately from restart command failures.
- [ ] Keep restart scheduling intact on check failures.
- [ ] Add tests for status and command branches.
      **Notes:** Easier troubleshooting during compose restarts.

### [WL-8304]

**Title:** Preserve health endpoint timeout handling by separating request parse and timeout enforcement
**Source:** [thegent/src/thegent/health/endpoint.py:392]
**Acceptance checklist:**

- [ ] Split request parse failures from timeout enforcement exceptions.
- [ ] Keep stable timeout response contract.
- [ ] Add tests for parse and timeout branches.
      **Notes:** Better behavior under malicious or slow clients.

### [WL-8305]

**Title:** Preserve prompt cache sync by separating key normalization and persistence failures
**Source:** [thegent/src/thegent/prompts.py:381]
**Acceptance checklist:**

- [ ] Split prompt key normalization errors from persistence failures.
- [ ] Keep cache availability on normalization failures.
- [ ] Add tests for both error types.
      **Notes:** Improves prompt cache robustness.

### [WL-8306]

**Title:** Preserve artifact collect reporting by separating file list and file read errors
**Source:** [thegent/src/thegent/artifacts/collector.py:449]
**Acceptance checklist:**

- [ ] Separate directory listing failures from file read failures.
- [ ] Keep reporting results for successfully read entries.
- [ ] Add tests for list failure and read failure cases.
      **Notes:** Helps recover partial artifact scans.

### [WL-8307]

**Title:** Preserve scheduler startup while separating task discovery and worker registration errors
**Source:** [thegent/src/thegent/orchestration/scheduler.py:662]
**Acceptance checklist:**

- [ ] Split task-discovery failures from worker registration failures.
- [ ] Preserve startup with graceful degradation where possible.
- [ ] Add tests for discovery and registration branches.
      **Notes:** Keeps scheduler resilient during partial startup regressions.

### [WL-8308]

**Title:** Preserve borrow request validation while separating schema and runtime send failures
**Source:** [thegent/src/thegent/tools/borrow.py:822]
**Acceptance checklist:**

- [ ] Split request schema validation failures from runtime send failures.
- [ ] Preserve standardized error responses.
- [ ] Add tests for both branches.
      **Notes:** Increases precision for borrow incident debugging.

### [WL-8309]

**Title:** Preserve retry policy fallback by separating env source and parser failures
**Source:** [thegent/src/thegent/retry/strategy.py:352]
**Acceptance checklist:**

- [ ] Separate config source resolution failures from parser failures.
- [ ] Keep retry defaults when source is unavailable.
- [ ] Add tests for each fallback branch.
      **Notes:** Prevents retries from disabling due to non-critical config sourcing.
