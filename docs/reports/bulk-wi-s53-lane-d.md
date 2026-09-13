### [WL-8200]

**Title:** Preserve agent startup logs while separating dependency import from process invocation
**Source:** [thegent/src/thegent/agents/starter.py:114]
**Acceptance checklist:**

- [ ] Split optional dependency import failures from subprocess invocation failures.
- [ ] Preserve startup logging and retry messages.
- [ ] Add tests for missing dependency and invocation errors.
      **Notes:** Helps distinguish environment and command errors.

### [WL-8201]

**Title:** Preserve borrow connectivity while separating proxy config parse and proxy call failures
**Source:** [thegent/src/thegent/tools/borrow.py:510]
**Acceptance checklist:**

- [ ] Separate invalid proxy config parsing from proxy request failures.
- [ ] Preserve borrow result behavior on proxy transport errors.
- [ ] Add tests for invalid proxy config and proxy response failures.
      **Notes:** Clarifies where network path failures originate.

### [WL-8202]

**Title:** Preserve cache cleanup by separating stale entry scan and deletion failures
**Source:** [thegent/src/thegent/cache/rebuilder.py:168]
**Acceptance checklist:**

- [ ] Isolate stale entry detection failures from deletion failures.
- [ ] Keep cleanup retries on deletable entries.
- [ ] Add tests for stale scan and delete errors.
      **Notes:** Improves cache cleanup observability.

### [WL-8203]

**Title:** Preserve control-plane status endpoints by splitting request parse and auth check failures
**Source:** [thegent/src/thegent/control_plane/server.py:378]
**Acceptance checklist:**

- [ ] Distinguish malformed request parse from auth failure branches.
- [ ] Keep status endpoint contract stable for both branches.
- [ ] Add tests for malformed requests and auth errors.
      **Notes:** Supports faster diagnosis of control-plane incidents.

### [WL-8204]

**Title:** Separate mesh CLI manifest decode and dashboard render failures
**Source:** [thegent/src/thegent/mesh/cli.py:252]
**Acceptance checklist:**

- [ ] Handle decode errors separately from dashboard render exceptions.
- [ ] Preserve stale-state fallback output when decode fails.
- [ ] Add tests for decode failures and render failures.
      **Notes:** Prevents full dashboard blanking from bad manifest data.

### [WL-8205]

**Title:** Preserve shell history prune while separating parse and file-IO failures
**Source:** [thegent/src/thegent/clipboard/history.py:308]
**Acceptance checklist:**

- [ ] Distinguish prune input parse failures from history file I/O failures.
- [ ] Keep prune scheduling and best-effort behavior.
- [ ] Add tests for malformed prune config and read-only store paths.
      **Notes:** Reduces silent history management failures.

### [WL-8206]

**Title:** Preserve artifact upload fallback by separating endpoint selection from upload execution
**Source:** [thegent/src/thegent/artifacts/uploader.py:362]
**Acceptance checklist:**

- [ ] Split endpoint selection or fallback logic from upload execution.
- [ ] Keep retry policy for execution failures intact.
- [ ] Add tests for endpoint selection failures and upload errors.
      **Notes:** Improves predictability during endpoint-side migrations.

### [WL-8207]

**Title:** Preserve health endpoint output while separating formatter and transport exceptions
**Source:** [thegent/src/thegent/health/endpoint.py:201]
**Acceptance checklist:**

- [ ] Handle formatter exceptions separately from transport send exceptions.
- [ ] Maintain health endpoint status and payload contract.
- [ ] Add tests for formatter and transport failures.
      **Notes:** Better incident response for health check degradation.

### [WL-8208]

**Title:** Preserve session bootstrap when command mapping is invalid
**Source:** [thegent/src/thegent/session/bootstrap.py:302]
**Acceptance checklist:**

- [ ] Separate command mapping parse failures from command execution exceptions.
- [ ] Keep bootstrap fallback behavior on mapping parse issues.
- [ ] Add tests for missing mappings and execution failures.
      **Notes:** Improves diagnostic quality in bootstrap automation.

### [WL-8209]

**Title:** Preserve queue state persistence while separating write contention and validation failures
**Source:** [thegent/src/thegent/queue/state.py:162]
**Acceptance checklist:**

- [ ] Distinguish write lock contention from queue state validation failures.
- [ ] Preserve read path and retry behavior.
- [ ] Add tests for contention and validation errors.
      **Notes:** Supports robust state management under concurrency.
