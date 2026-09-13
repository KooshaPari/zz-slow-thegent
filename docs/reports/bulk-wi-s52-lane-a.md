### [WL-8120]

**Title:** Split Playwright page-open failures from browser launch failures
**Source:** [thegent/src/thegent/doc_tools/playwright_recorder.py:233]
**Acceptance checklist:**

- [ ] Separate exception handling for browser launch vs new page navigation in recorder startup.
- [ ] Preserve current startup success behavior and logging semantics on success.
- [ ] Add tests for launch failure and navigation failure paths.
      **Notes:** Current catch-all hides where startup aborts.

### [WL-8121]

**Title:** Differentiate MCP borrow success-path parsing from transport-level errors
**Source:** [thegent/src/thegent/tools/borrow.py:271]
**Acceptance checklist:**

- [ ] Split JSON response parsing errors from transport timeout/connection errors.
- [ ] Preserve boolean return contract used by callers.
- [ ] Add tests for parse success, parse failure, and timeout.
      **Notes:** One broad branch currently loses actionable failure context.

### [WL-8122]

**Title:** Preserve watcher shared-memory fallback while separating import from runtime failures
**Source:** [thegent/src/thegent/native/watcher_daemon.py:107]
**Acceptance checklist:**

- [ ] Add explicit handling for missing optional dependency import.
- [ ] Handle shared-memory init failures separately from settings load issues.
- [ ] Add tests for import-only and runtime-initialization fallback.
      **Notes:** Keeps SHM deactivation behavior stable while improving diagnostics.

### [WL-8123]

**Title:** Separate multi-runtime bridge timeout vs process creation failures
**Source:** [thegent/src/thegent/infra/multi_runtime_bridge.py:149]
**Acceptance checklist:**

- [ ] Add distinct branches for bridge process spawn, connect timeout, and handshake failures.
- [ ] Preserve worker startup and cleanup contracts on failure.
- [ ] Add tests for each failure branch with explicit assertions.
      **Notes:** Enables faster triage for environment-specific failures.

### [WL-8124]

**Title:** Refine mesh dashboard status parsing with explicit manifest schema checks
**Source:** [thegent/src/thegent/mesh/cli.py:198]
**Acceptance checklist:**

- [ ] Validate manifest schema before dereferencing fields.
- [ ] Preserve `None`/offline status for missing or malformed manifests.
- [ ] Add tests for invalid schema and missing file scenarios.
      **Notes:** Prevents schema drift from causing uncaught parse failures.

### [WL-8125]

**Title:** Split FlashAgent dispatch result decoding from runtime execution failures
**Source:** [thegent/src/thegent/agents/sub_agent_dispatcher.py:355]
**Acceptance checklist:**

- [ ] Separate decode/type errors from runtime timeout and cancellation errors.
- [ ] Preserve external `DispatchError` behavior and caller contract.
- [ ] Add tests for each dispatch failure category.
      **Notes:** Keeps operational dashboards usable for incident forensics.

### [WL-8126]

**Title:** Distinguish cliproxy config bootstrap missing file from malformed content
**Source:** [thegent/src/thegent/agents/cliproxy_manager.py:389]
**Acceptance checklist:**

- [ ] Add separate branches for file-not-found and YAML parse failures.
- [ ] Keep first-run default config behavior unchanged.
- [ ] Add tests for no-file and invalid-YAML cases.
      **Notes:** Better recovery hints with unchanged startup defaults.

### [WL-8127]

**Title:** Preserve discovery when psutil missing while adding explicit fallback metadata
**Source:** [thegent/src/thegent/native/discovery_native.py:132]
**Acceptance checklist:**

- [ ] Keep empty-result return on dependency absence.
- [ ] Emit explicit branch marker for missing dependency fallback.
- [ ] Add tests for present dependency and missing dependency scenarios.
      **Notes:** Improves operator confidence without changing user-visible behavior.

### [WL-8128]

**Title:** Separate compositor output validation from compositor runtime failures
**Source:** [thegent/src/thegent/ui/compositor_manager.py:460]
**Acceptance checklist:**

- [ ] Distinguish bad panel payload shape from runtime render exceptions.
- [ ] Preserve fallback rendering output on either failure.
- [ ] Add tests for invalid payload and runtime crash cases.
      **Notes:** Faster debugging for UI refresh instability.

### [WL-8129]

**Title:** Remove redundant Claude CLI success assignment wrapper
**Source:** [thegent/src/thegent/doctor_dependencies.py:58]
**Acceptance checklist:**

- [ ] Delete no-op try/except path around deterministic assignment.
- [ ] Preserve dependency-detection return values and messages.
- [ ] Add tests for present and missing `claude` command paths.
      **Notes:** Reduces noise and preserves behavior.
