### [WL-7650]

**Title:** Add strict schema validation for plan event payloads before enqueue
**Source:** [thegent/src/thegent/orchestration/event_queue.py:52]
**Acceptance checklist:**

- [ ] Validate required plan event fields and types at queue ingress.
- [ ] Reject invalid payloads with explicit error messages and event identifiers.
- [ ] Add tests for valid events, missing fields, and type mismatches.
      **Notes:** Current enqueue accepts loosely-shaped payloads, which can fail later in harder-to-diagnose paths.

### [WL-7651]

**Title:** Prevent duplicate prompt IDs from being inserted into persistent queue storage
**Source:** [thegent/src/thegent/queue/storage.py:118]
**Acceptance checklist:**

- [ ] Enforce prompt ID uniqueness at write time with deterministic conflict handling.
- [ ] Preserve existing queue order semantics for non-conflicting inserts.
- [ ] Add tests for duplicate insert attempts and normal multi-item writes.
      **Notes:** Duplicate prompt IDs create ambiguous dequeue behavior and can break replay determinism.

### [WL-7652]

**Title:** Make queue lock acquisition failures visible with bounded retry diagnostics
**Source:** [thegent/src/thegent/queue/locking.py:67]
**Acceptance checklist:**

- [ ] Emit structured diagnostics on each lock retry attempt with wait duration.
- [ ] Fail with explicit lock-timeout context after max retries are exhausted.
- [ ] Add tests for immediate lock success and retry timeout paths.
      **Notes:** Silent lock contention obscures throughput issues and leads to operator confusion during incidents.

### [WL-7653]

**Title:** Normalize runtime dispatch contract to require explicit runtime capability declaration
**Source:** [thegent/src/thegent/infra/runtime_dispatcher.py:91]
**Acceptance checklist:**

- [ ] Require runtime capability metadata before task dispatch is attempted.
- [ ] Return a typed dispatch error when capability declaration is absent.
- [ ] Add tests for declared capabilities, missing metadata, and incompatible runtime selections.
      **Notes:** Implicit capability assumptions permit late-stage failures after costly task setup.

### [WL-7654]

**Title:** Add stale-process eviction telemetry to process registry sweep cycle
**Source:** [thegent/src/thegent/infra/process_registry.py:143]
**Acceptance checklist:**

- [ ] Track count and age distribution of evicted stale process entries.
- [ ] Log sweep outcomes with registry path and elapsed sweep time.
- [ ] Add tests that verify stale entry eviction and telemetry emission.
      **Notes:** Registry cleanup currently removes stale rows without enough observability for tuning thresholds.

### [WL-7655]

**Title:** Harden project registry reads against partial JSON writes with explicit corruption signaling
**Source:** [thegent/src/thegent/registry/project_registry.py:74]
**Acceptance checklist:**

- [ ] Detect truncated or malformed JSON registry files during load.
- [ ] Raise a clear corruption error that includes file path and parse offset.
- [ ] Add tests for valid files, truncated writes, and malformed JSON payloads.
      **Notes:** Partial writes can surface as generic parse exceptions that do not provide actionable remediation details.

### [WL-7656]

**Title:** Enforce deterministic command registration order in CLI registry bootstrap
**Source:** [thegent/src/thegent/commands/registry.py:39]
**Acceptance checklist:**

- [ ] Sort command registration inputs using a stable deterministic key.
- [ ] Keep command resolution behavior unchanged for existing command names.
- [ ] Add tests asserting stable registry ordering across repeated boots.
      **Notes:** Non-deterministic registration order can produce flaky help output and command shadowing bugs.

### [WL-7657]

**Title:** Add health check dependency breakdown so degraded state identifies failing subsystem
**Source:** [thegent/src/thegent/monitoring/health_check.py:128]
**Acceptance checklist:**

- [ ] Include per-subsystem status details in health check response payloads.
- [ ] Preserve existing top-level healthy/degraded indicators for compatibility.
- [ ] Add tests for fully healthy, partially degraded, and fully failed subsystem matrices.
      **Notes:** Single aggregate health status is insufficient for triage when multiple dependencies are involved.

### [WL-7658]

**Title:** Guarantee MCP server startup emits socket readiness only after bind/listen success
**Source:** [thegent/src/thegent/mcp_server.py:211]
**Acceptance checklist:**

- [ ] Emit readiness signal only after socket bind and listen complete successfully.
- [ ] Propagate startup failures with explicit port and bind error details.
- [ ] Add tests for successful startup and port-conflict failure behavior.
      **Notes:** Premature readiness signaling can cause clients to connect before the server is actually accepting requests.

### [WL-7659]

**Title:** Track dropped shared MCP lockfile updates and expose them in manager status output
**Source:** [thegent/src/thegent/shared_mcp_manager.py:187]
**Acceptance checklist:**

- [ ] Count dropped lockfile update events during contention windows.
- [ ] Surface dropped-update counters in manager status and diagnostics output.
- [ ] Add tests for normal lockfile updates, contention, and dropped-update reporting.
      **Notes:** Lost lockfile updates under contention are currently hard to detect and can mislead downstream clients.
