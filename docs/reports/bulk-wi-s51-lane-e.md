### [WL-8110]

**Title:** Improve project bootstrap user guidance on invalid command combinations
**Source:** [thegent/src/thegent/session/bootstrap.py:130]
**Acceptance checklist:**

- [ ] Split argument conflict checks from environment setup errors.
- [ ] Preserve existing bootstrap exit codes.
- [ ] Add tests for conflicting flags and env failures.
      **Notes:** Better user-facing guidance with unchanged control-flow contract.

### [WL-8111]

**Title:** Separate conversation dumper parse failures from storage failures
**Source:** [thegent/src/thegent/session/conversation_dumper.py:163]
**Acceptance checklist:**

- [ ] Add explicit handling for corrupted JSON blobs and storage write failures.
- [ ] Preserve successful dump behavior for valid inputs.
- [ ] Add tests for invalid dumps and write-permission failures.
      **Notes:** Reduces ambiguity in conversation export incidents.

### [WL-8112]

**Title:** Isolate MCP borrow config validation from runtime borrow invocation errors
**Source:** [thegent/src/thegent/tools/borrow.py:356]
**Acceptance checklist:**

- [ ] Add schema validation errors separate from invocation transport errors.
- [ ] Keep borrow return structure for callers.
- [ ] Add tests for invalid config and transport timeout scenarios.
      **Notes:** Helps distinguish setup issues from runtime connectivity.

### [WL-8113]

**Title:** Keep sync-state watcher fallback when file locks block writes
**Source:** [thegent/src/thegent/native/watcher_daemon.py:207]
**Acceptance checklist:**

- [ ] Add explicit lock-conflict branch and backoff path.
- [ ] Preserve existing read path for lock contention windows.
- [ ] Add tests for lock contention and successful retry cases.
      **Notes:** Improves stability when multiple processes touch state simultaneously.

### [WL-8114]

**Title:** Distinguish queue claim stale-lock from ownership-check failures
**Source:** [thegent/src/thegent/queue/claim.py:311]
**Acceptance checklist:**

- [ ] Split stale lock detection from lock ownership mismatch handling.
- [ ] Preserve existing claim semantics on successful lock validation.
- [ ] Add tests for both lock failure kinds.
      **Notes:** Makes queue recovery behavior easier to reason about.

### [WL-8115]

**Title:** Preserve workflow orchestration status on partial control plane failures
**Source:** [thegent/src/thegent/control_plane/server.py:276]
**Acceptance checklist:**

- [ ] Separate control plane unmarshal errors from dispatch routing errors.
- [ ] Keep running-workflows unaffected by unrelated control events.
- [ ] Add tests for route miss and malformed control payloads.
      **Notes:** Prevents unrelated plane failures from masking orchestration status.

### [WL-8116]

**Title:** Separate shell history write failures from command parse failures
**Source:** [thegent/src/thegent/shell_cli.py:388]
**Acceptance checklist:**

- [ ] Add explicit branches for CLI parse and write-to-history exceptions.
- [ ] Preserve command execution path when history write fails.
- [ ] Add tests for non-writable history and invalid command input.
      **Notes:** Improves user trust by allowing execution despite local history issues.

### [WL-8117]

**Title:** Keep prompt caching behavior while isolating serialization failures
**Source:** [thegent/src/thegent/prompts.py:205]
**Acceptance checklist:**

- [ ] Split cache write failures from prompt template parse failures.
- [ ] Preserve cache-miss fallback behavior.
- [ ] Add tests for corrupted cache and write errors.
      **Notes:** Reduces hidden regressions in repeated prompt generation.

### [WL-8118]

**Title:** Preserve task planner output contract while classifying template expansion failures
**Source:** [thegent/src/thegent/planner/task_planner.py:417]
**Acceptance checklist:**

- [ ] Differentiate missing variable interpolation from syntax errors in expansion.
- [ ] Keep planner output defaults on recoverable interpolation issues.
- [ ] Add tests for each expansion failure branch.
      **Notes:** Enhances diagnostics for task template reliability.

### [WL-8119]

**Title:** Separate artifact upload failures into network and payload-structure failures
**Source:** [thegent/src/thegent/artifacts/uploader.py:256]
**Acceptance checklist:**

- [ ] Handle network timeout/retry separately from payload schema errors.
- [ ] Preserve uploader contract and retry policy for transient network failures.
- [ ] Add tests for timeout, schema, and success cases.
      **Notes:** More precise recovery strategy for artifact sync automation.
