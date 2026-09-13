### [WL-8190]

**Title:** Preserve agent bridge startup while separating config validation and process spawn
**Source:** [thegent/src/thegent/infra/multi_runtime_bridge.py:201]
**Acceptance checklist:**

- [ ] Split config validation failures from spawn/create-runtime failures.
- [ ] Preserve bridge lifecycle behavior on spawn retries.
- [ ] Add tests for invalid config and spawn failures.
      **Notes:** Makes startup incidents easier to trace.

### [WL-8191]

**Title:** Preserve summary rendering while separating payload decode and template rendering failures
**Source:** [thegent/src/thegent/summary.py:412]
**Acceptance checklist:**

- [ ] Distinguish payload decoding failures from template rendering errors.
- [ ] Keep summary generation path for recoverable decode issues.
- [ ] Add tests for malformed summary payload and render exceptions.
      **Notes:** Helps isolate data integrity issues from rendering engine failures.

### [WL-8192]

**Title:** Preserve command execution behavior while separating shell parse and action failures
**Source:** [thegent/src/thegent/shell_cli.py:631]
**Acceptance checklist:**

- [ ] Separate parser-level exceptions from action invocation failures.
- [ ] Preserve return contract for successful action invocations.
- [ ] Add tests for parse errors and action failures.
      **Notes:** Avoids one broad error path across CLI interactions.

### [WL-8193]

**Title:** Preserve clipboard history sync with explicit JSON encoding failure branch
**Source:** [thegent/src/thegent/clipboard/history.py:278]
**Acceptance checklist:**

- [ ] Add explicit handling for encoding exceptions during history sync.
- [ ] Preserve non-blocking behavior for non-encoding-related sync errors.
- [ ] Add tests for encoding exceptions and fallback behavior.
      **Notes:** Improves robustness in mixed-encoding environments.

### [WL-8194]

**Title:** Preserve process-compose refresh while separating compose config and invocation failures
**Source:** [thegent/src/thegent/process_compose/watcher.py:191]
**Acceptance checklist:**

- [ ] Handle compose config parse failures separately from command invocation exceptions.
- [ ] Preserve retry behavior on transient invocation failures.
- [ ] Add tests for invalid config and invocation exceptions.
      **Notes:** Clearer signal when refresh failures are configuration-driven.

### [WL-8195]

**Title:** Separate mesh state parse and process lookup failures
**Source:** [thegent/src/thegent/mesh/control.py:515]
**Acceptance checklist:**

- [ ] Add branch for malformed mesh state payloads vs process lookup misses.
- [ ] Keep dashboard state handling stable for lookup misses.
- [ ] Add tests for malformed payload and stale process entries.
      **Notes:** Helps distinguish wire-level issues from lifecycle issues.

### [WL-8196]

**Title:** Preserve retry scheduling by separating strategy parse and timer scheduling errors
**Source:** [thegent/src/thegent/retry/strategy.py:172]
**Acceptance checklist:**

- [ ] Split retry strategy parser errors from scheduler timer setup errors.
- [ ] Keep fallback strategy behavior unchanged on parser errors.
- [ ] Add tests for bad strategy config and timer exceptions.
      **Notes:** Makes scheduler behavior deterministic under malformed config.

### [WL-8197]

**Title:** Preserve artifact collector when metadata field missing versus decode fails
**Source:** [thegent/src/thegent/artifacts/collector.py:233]
**Acceptance checklist:**

- [ ] Separate missing metadata field handling from invalid metadata decoding.
- [ ] Preserve collection flow while skipping invalid items only.
- [ ] Add tests for missing fields and invalid JSON metadata.
      **Notes:** Prevents collector halts when schema is partially corrupt.

### [WL-8198]

**Title:** Preserve startup config merge while separating YAML parse from schema validation
**Source:** [thegent/src/thegent/config/settings.py:273]
**Acceptance checklist:**

- [ ] Distinguish raw YAML parse errors from schema validation failures.
- [ ] Keep previous defaults for schema validation failures.
- [ ] Add tests for malformed YAML and schema mismatches.
      **Notes:** Improves startup clarity and stability.

### [WL-8199]

**Title:** Preserve queue state fetch while separating transport and payload failures
**Source:** [thegent/src/thegent/queue/state.py:112]
**Acceptance checklist:**

- [ ] Separate transport exceptions from malformed state payload handling.
- [ ] Preserve state polling behavior for payload-only failures.
- [ ] Add tests for transport loss and malformed payloads.
      **Notes:** Supports resilience in high-churn queue environments.
