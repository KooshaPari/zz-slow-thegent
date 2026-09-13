### [WL-7530]

**Title:** Split Playwright recorder launch failures by setup stage with explicit diagnostics
**Source:** [thegent/src/thegent/doc_tools/playwright_recorder.py:217]
**Acceptance checklist:**

- [ ] Replace broad launch exception handling with stage-specific failures for browser start, context creation, and page initialization.
- [ ] Preserve existing recorder startup behavior and logging while adding deterministic setup-stage metadata.
- [ ] Add tests for successful initialization plus one failure case per setup stage.
      **Notes:** A single launch catch-all obscures where startup actually failed, which slows incident triage.

### [WL-7531]

**Title:** Classify MCP reachability probe failures instead of collapsing all errors to false
**Source:** [thegent/src/thegent/tools/borrow.py:238]
**Acceptance checklist:**

- [ ] Replace blanket probe exception handling with explicit timeout, connection, and protocol failure branches.
- [ ] Preserve the current boolean return contract for callers.
- [ ] Add tests for HTTP success, timeout failure, and connection-refused behavior.
      **Notes:** Returning only `False` for all exceptions drops actionable information about why reachability failed.

### [WL-7532]

**Title:** Separate watcher shared-memory bootstrap failures into import, config, and initialization categories
**Source:** [thegent/src/thegent/native/watcher_daemon.py:100]
**Acceptance checklist:**

- [ ] Replace broad CircuitBreakerShm bootstrap exception handling with typed dependency-import, settings-resolution, and SHM-init paths.
- [ ] Preserve non-fatal fallback behavior when SHM is unavailable.
- [ ] Add tests for successful SHM bootstrap and each typed fallback class.
      **Notes:** Current debug-only catch-all makes degraded watcher mode hard to reason about during operational debugging.

### [WL-7533]

**Title:** Remove no-op worker startup exception wrapper in multi-runtime bridge
**Source:** [thegent/src/thegent/infra/multi_runtime_bridge.py:127]
**Acceptance checklist:**

- [ ] Eliminate or replace the bare catch-and-reraise with value-added context that improves failure attribution.
- [ ] Preserve worker registration, heartbeat setup, and log-forwarder creation semantics on success.
- [ ] Add tests that verify enriched startup-failure context.
      **Notes:** `except Exception: raise` adds no behavior and weakens clarity around the intended boundary.

### [WL-7534]

**Title:** Differentiate mesh dashboard manifest and process-inspection failure modes
**Source:** [thegent/src/thegent/mesh/cli.py:181]
**Acceptance checklist:**

- [ ] Split broad dashboard exception handling into explicit manifest-read, parse, and process-inspection branches.
- [ ] Preserve offline/zombie status behavior for known non-running PIDs.
- [ ] Add tests for malformed manifests, missing mesh files, and process lookup failures.
      **Notes:** Collapsing all dashboard errors to `None` removes root-cause visibility for mesh troubleshooting.

### [WL-7535]

**Title:** Classify FlashAgent runtime failures before wrapping in DispatchError
**Source:** [thegent/src/thegent/agents/sub_agent_dispatcher.py:339]
**Acceptance checklist:**

- [ ] Replace broad FlashAgent exception wrapping with typed timeout, cancellation, and runtime-error handling.
- [ ] Preserve the `DispatchError` external surface for callers.
- [ ] Add tests for successful flash dispatch plus representative typed failure paths.
      **Notes:** A single wrapped message makes transient and hard failures indistinguishable during dispatch debugging.

### [WL-7536]

**Title:** Distinguish cliproxy config corruption from missing-config bootstrap paths
**Source:** [thegent/src/thegent/agents/cliproxy_manager.py:403]
**Acceptance checklist:**

- [ ] Replace broad config-load suppression with explicit file-read and YAML-parse failure handling.
- [ ] Preserve first-run default bootstrapping when no config exists.
- [ ] Add tests for valid config load, malformed YAML input, and unreadable config files.
      **Notes:** Treating every load failure as empty config risks hiding recoverable user-config issues.

### [WL-7537]

**Title:** Add explicit missing-dependency diagnostics to native discovery psutil fallback
**Source:** [thegent/src/thegent/native/discovery_native.py:140]
**Acceptance checklist:**

- [ ] Replace silent `psutil` import fallback with structured diagnostics while preserving current fallback contract.
- [ ] Preserve empty-result behavior when discovery dependencies are unavailable.
- [ ] Add tests for installed-dependency and missing-dependency paths.
      **Notes:** Returning an empty process list without dependency context can be misread as a healthy zero-match outcome.

### [WL-7538]

**Title:** Harden compositor slot render boundary with typed error telemetry
**Source:** [thegent/src/thegent/ui/compositor_manager.py:447]
**Acceptance checklist:**

- [ ] Replace broad render catch with explicit compositor-runtime and output-shape failure categories.
- [ ] Preserve user-facing fallback output for render failures.
- [ ] Add tests for normal render output, compositor exceptions, and invalid panel payloads.
      **Notes:** Current generic fallback protects UX but removes structured diagnostics needed for repeated render incidents.

### [WL-7539]

**Title:** Remove redundant try-except around deterministic Claude CLI success assignment
**Source:** [thegent/src/thegent/doctor_dependencies.py:42]
**Acceptance checklist:**

- [ ] Delete the dead catch-and-duplicate assignment path around static success assignment.
- [ ] Preserve current pass/fail messaging for Claude CLI detection.
- [ ] Add tests for both installed and missing `claude` binary scenarios.
      **Notes:** The current wrapper cannot fail meaningfully and obscures the actual status decision flow.
