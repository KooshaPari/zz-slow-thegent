### [WL-8100]

**Title:** Refine clipboard history pruning to separate timestamp and path validation failures
**Source:** [thegent/src/thegent/clipboard/history.py:132]
**Acceptance checklist:**

- [ ] Add explicit error paths for bad timestamps versus bad paths.
- [ ] Preserve current prune-by-age contract on invalid inputs.
- [ ] Add tests for malformed history entries.
      **Notes:** Avoids one broad branch covering multiple data quality issues.

### [WL-8101]

**Title:** Distinguish token ledger sync errors by auth and endpoint failures
**Source:** [thegent/src/thegent/agentauth/token_sync.py:214]
**Acceptance checklist:**

- [ ] Split auth-token parse errors from endpoint transport failures.
- [ ] Preserve best-effort sync behavior for transient network problems.
- [ ] Add tests for both auth and transport branches.
      **Notes:** Clarifies why token sync stops in CI and local environments.

### [WL-8102]

**Title:** Split mesh control message parse and dispatch failures
**Source:** [thegent/src/thegent/mesh/control.py:401]
**Acceptance checklist:**

- [ ] Handle malformed control payloads separately from routing failures.
- [ ] Preserve in-order dispatch behavior for valid messages.
- [ ] Add tests for malformed JSON and dispatch exceptions.
      **Notes:** Better separation reduces noisy control-plane rollbacks.

### [WL-8103]

**Title:** Preserve CLI cache rebuild with typed file-write diagnostics
**Source:** [thegent/src/thegent/cache/rebuilder.py:87]
**Acceptance checklist:**

- [ ] Separate rename/write failures from read failures.
- [ ] Keep successful rebuild behavior unchanged.
- [ ] Add tests for locked file and bad-read failure paths.
      **Notes:** Helps identify whether failures are read-side or write-side.

### [WL-8104]

**Title:** Separate web UI plugin discovery errors from plugin import exceptions
**Source:** [thegent/src/thegent/ui/plugin_loader.py:266]
**Acceptance checklist:**

- [ ] Distinguish missing plugin manifest from import-time exceptions.
- [ ] Keep existing no-plugin fallback when discovery is empty.
- [ ] Add tests for discovery failure and plugin import failure.
      **Notes:** Better fault attribution during UI startup incidents.

### [WL-8105]

**Title:** Preserve runtime health endpoint behavior while separating serialization branches
**Source:** [thegent/src/thegent/health/endpoint.py:98]
**Acceptance checklist:**

- [ ] Split health payload serialization errors from request parsing errors.
- [ ] Keep existing HTTP status contract for invalid payload encoding.
- [ ] Add tests for each failure branch.
      **Notes:** Improves reliability of health reporting under partial failures.

### [WL-8106]

**Title:** Make borrow-tool retry handling explicitly distinguish no-retry from retryable states
**Source:** [thegent/src/thegent/tools/borrow.py:312]
**Acceptance checklist:**

- [ ] Add dedicated branches for explicit no-retry responses versus retriable transport issues.
- [ ] Preserve existing success/fail return shapes.
- [ ] Add integration-style tests for both response classes.
      **Notes:** Removes ambiguity in operator actions during tool invocation.

### [WL-8107]

**Title:** Separate process-compose refresh trigger errors into config and invocation failures
**Source:** [thegent/src/thegent/process_compose/watcher.py:148]
**Acceptance checklist:**

- [ ] Handle missing config-file and failed compose command separately.
- [ ] Preserve best-effort refresh path for non-fatal invocation failures.
- [ ] Add tests for both branches.
      **Notes:** Makes refresh health checks actionable in automation contexts.

### [WL-8108]

**Title:** Keep agent startup logs resilient while separating env and binary failures
**Source:** [thegent/src/thegent/agents/starter.py:61]
**Acceptance checklist:**

- [ ] Split environment variable validation failures from executable-not-found failures.
- [ ] Preserve startup state machine on recoverable errors.
- [ ] Add tests for each startup failure type.
      **Notes:** Reduces operator confusion during startup diagnostics.

### [WL-8109]

**Title:** Preserve artifact retention policy while separating dry-run and execution failures
**Source:** [thegent/src/thegent/artifacts/retention.py:173]
**Acceptance checklist:**

- [ ] Split dry-run validation failures from purge execution exceptions.
- [ ] Keep retention execution semantics unchanged when command succeeds.
- [ ] Add tests for dry-run misuse and purge rollback paths.
      **Notes:** Supports safer policy enforcement with clearer operational logs.
