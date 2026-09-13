### [WL-7480]

**Title:** Narrow Playwright browser launch failure handling to setup-stage-specific exceptions
**Source:** [thegent/src/thegent/doc_tools/playwright_recorder.py:217]
**Acceptance checklist:**

- [ ] Replace broad launch exception catch with explicit failure branches for Playwright startup, context creation, and page initialization.
- [ ] Preserve existing error logging while including failing setup stage metadata.
- [ ] Add tests for successful launch and each setup-stage failure path.
      **Notes:** A single catch-all hides whether failure occurred at browser start, context setup, or page creation.

### [WL-7481]

**Title:** Classify MCP reachability probe failures instead of returning a single false state
**Source:** [thegent/src/thegent/tools/borrow.py:238]
**Acceptance checklist:**

- [ ] Replace broad reachability exception handling with explicit timeout, connection, and HTTP protocol failure branches.
- [ ] Preserve the boolean public contract while adding structured diagnostics for callers.
- [ ] Add tests for HTTP 200 success, timeout, and connection-refused behavior.
      **Notes:** The current blanket `False` return masks why an MCP endpoint is unreachable.

### [WL-7482]

**Title:** Split watcher shared-memory bootstrap errors into import, config, and path-initialization categories
**Source:** [thegent/src/thegent/native/watcher_daemon.py:100]
**Acceptance checklist:**

- [ ] Replace broad CircuitBreaker bootstrap exception handling with typed failure categories for dependency import, settings load, and SHM initialization.
- [ ] Preserve fallback to non-SHM mode when SHM initialization is unavailable.
- [ ] Add tests for successful SHM setup and each fallback class.
      **Notes:** Current debug logging captures the exception text but does not classify failure mode for remediation.

### [WL-7483]

**Title:** Remove redundant worker startup catch-and-reraise in multi-runtime bridge
**Source:** [thegent/src/thegent/infra/multi_runtime_bridge.py:127]
**Acceptance checklist:**

- [ ] Eliminate no-op exception wrapper around worker subprocess creation or replace it with value-added context.
- [ ] Preserve active worker registration and heartbeat initialization behavior on success.
- [ ] Add tests that assert enriched error context on startup failure.
      **Notes:** `except Exception: raise` adds no behavior and obscures the intended error boundary.

### [WL-7484]

**Title:** Differentiate mesh manifest parse errors from process-state lookup failures in dashboard rendering
**Source:** [thegent/src/thegent/mesh/cli.py:181]
**Acceptance checklist:**

- [ ] Split broad manifest processing exception handling into explicit file I/O, YAML parse, and process-inspection branches.
- [ ] Preserve current dashboard behavior for offline or zombie agents.
- [ ] Add tests for malformed manifests, missing files, and non-running PIDs.
      **Notes:** Returning `None` for all failure classes drops root-cause signal during live mesh triage.

### [WL-7485]

**Title:** Classify FlashAgent dispatch failures before wrapping into DispatchError
**Source:** [thegent/src/thegent/agents/sub_agent_dispatcher.py:339]
**Acceptance checklist:**

- [ ] Replace broad FlashAgent execution catch with typed timeout, cancellation, and runtime failure handling.
- [ ] Preserve existing DispatchError surface for callers while enriching failure metadata.
- [ ] Add tests for successful flash dispatch, timeout failure, and unexpected runtime exception.
      **Notes:** A single wrapped error message makes it hard to separate transient timeout from hard execution faults.

### [WL-7486]

**Title:** Surface cliproxy config-parse corruption separately from first-run empty-config fallback
**Source:** [thegent/src/thegent/agents/cliproxy_manager.py:403]
**Acceptance checklist:**

- [ ] Replace broad config load suppression with explicit YAML parse and filesystem read failure branches.
- [ ] Preserve default config bootstrap when no config file exists.
- [ ] Add tests for valid config load, malformed YAML recovery, and unreadable config file behavior.
      **Notes:** Treating all load errors as empty config can silently discard valid but temporarily unreadable user configuration.

### [WL-7487]

**Title:** Add explicit diagnostics when discovery fallback cannot import psutil
**Source:** [thegent/src/thegent/native/discovery_native.py:140]
**Acceptance checklist:**

- [ ] Replace silent import fallback with structured metadata indicating missing `psutil` dependency.
- [ ] Preserve empty-process-list fallback contract when discovery dependencies are absent.
- [ ] Add tests for installed `psutil` path and missing-dependency fallback diagnostics.
      **Notes:** Returning an empty list without dependency context can be misread as “no processes matched.”

### [WL-7488]

**Title:** Harden compositor slot rendering error boundary with typed failure telemetry
**Source:** [thegent/src/thegent/ui/compositor_manager.py:447]
**Acceptance checklist:**

- [ ] Replace broad render catch with explicit categories for compositor runtime failure and output-shape violations.
- [ ] Preserve user-facing fallback content to keep compositor output resilient.
- [ ] Add tests for normal render output, renderer exception, and invalid panel output payload.
      **Notes:** Current generic fallback string protects UX but loses structured error detail needed for debugging repeated render faults.

### [WL-7489]

**Title:** Remove dead exception branch in Claude CLI dependency check and enforce deterministic status assignment
**Source:** [thegent/src/thegent/doctor_dependencies.py:42]
**Acceptance checklist:**

- [ ] Eliminate unreachable/duplicate try-except around static Claude path assignment.
- [ ] Preserve current success and failure messages for Claude CLI presence detection.
- [ ] Add tests validating behavior for installed and missing `claude` binary states.
      **Notes:** The current `try/except` block cannot fail meaningfully and obscures the actual decision path.
