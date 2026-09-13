### [WL-7750]

**Title:** Preserve control-plane provider selection failures with typed fallback reason in metadata
**Source:** [thegent/src/thegent/config_provider.py:114]
**Acceptance checklist:**

- [ ] Distinguish import, construction, and runtime probe failures when creating `ControlPlaneConfigProvider`.
- [ ] Add `fallback_reason` and `fallback_stage` fields to provider metadata while keeping existing keys backward compatible.
- [ ] Add tests that validate metadata for success path, import failure path, and provider init exception path.
      **Notes:** Current degraded fallback metadata collapses multiple failure modes, which slows incident triage and rollback decisions.

### [WL-7751]

**Title:** Make prompt queue rewrites crash-safe with temp-file + fsync + atomic replace
**Source:** [thegent/src/thegent/core/prompt_queue.py:176]
**Acceptance checklist:**

- [ ] Rewrite `_write_all` to write into a sibling temp file, flush+fsync, then atomically replace the queue file.
- [ ] Ensure parent directory fsync is performed where supported so rename durability is preserved across crashes.
- [ ] Add tests for normal rewrite, interrupted write simulation, and preserving last valid queue on write failure.
      **Notes:** Direct in-place rewrite can leave truncated JSONL after process interruption, causing silent task loss.

### [WL-7752]

**Title:** Add thread-safe mutation guards for in-memory session registry operations
**Source:** [thegent/src/thegent/session/manager.py:41]
**Acceptance checklist:**

- [ ] Introduce a lock strategy that protects `_sessions` mutations in create, append, fork, and rollback paths.
- [ ] Keep public method signatures unchanged and preserve current exception semantics.
- [ ] Add concurrency tests that run parallel append/fork operations and assert no lost turns or duplicate session IDs.
      **Notes:** Session state is mutable shared data without synchronization, which risks races under concurrent tool execution.

### [WL-7753]

**Title:** Return explicit initialization diagnostics when shared LSP startup partially fails
**Source:** [thegent/src/thegent/shared_server_integration.py:41]
**Acceptance checklist:**

- [ ] Track per-language LSP startup failures and return them in a structured `errors` block alongside successful servers.
- [ ] Add an option to enforce strict mode (fail session init if any requested language server fails).
- [ ] Add tests for all-success, partial-failure, and strict-mode rejection flows.
      **Notes:** Current behavior silently drops failed language servers, producing incomplete session capabilities without visibility.

### [WL-7754]

**Title:** Enforce timeout escalation policy for async subprocesses with deterministic teardown
**Source:** [thegent/src/thegent/infra/fast_subprocess.py:175]
**Acceptance checklist:**

- [ ] On timeout, implement terminate-then-kill escalation with bounded grace period and platform-safe process-group handling.
- [ ] Capture timeout diagnostics (signal path, elapsed wait, pid/pgid) in the returned failure context.
- [ ] Add tests for cooperative exit, forced kill path, and orphan-child prevention behavior.
      **Notes:** Timeout handling without explicit escalation policy can leak subprocess trees and degrade host stability over long runs.

### [WL-7755]

**Title:** Add bounded backpressure metrics and drop policy for overloaded trace write queue
**Source:** [thegent/src/thegent/trace/recorder.py:122]
**Acceptance checklist:**

- [ ] Track queue depth high-watermark, enqueue drops, and sync-fallback count as recorder stats.
- [ ] Introduce a configurable drop strategy for sustained queue saturation instead of unbounded sync fallback churn.
- [ ] Add tests for queue full behavior verifying deterministic stats and data-loss signaling.
      **Notes:** Queue saturation currently falls back to synchronous writes without durable observability, masking throughput regressions.

### [WL-7756]

**Title:** Wrap schema migration in transaction with rollback-safe version stamping
**Source:** [thegent/src/thegent/planning/workstream_db.py:53]
**Acceptance checklist:**

- [ ] Execute migration steps and schema_version update inside a single explicit transaction.
- [ ] Prevent schema_version bump when any migration statement fails and ensure connection cleanup on exception.
- [ ] Add tests for successful v1->v2 migration and injected migration failure with unchanged version row.
      **Notes:** Non-atomic migration/version updates can leave DBs in ambiguous states that are hard to recover automatically.

### [WL-7757]

**Title:** Capture per-check latency and timeout classification in health check results
**Source:** [thegent/src/thegent/monitoring/health_check.py:25]
**Acceptance checklist:**

- [ ] Extend check execution to record `duration_ms` and classify failures as exception vs timeout.
- [ ] Add optional per-check timeout enforcement without breaking existing synchronous check registration.
- [ ] Add tests for fast success, exception failure, and timeout-triggered failure payloads.
      **Notes:** Health output currently exposes only pass/fail state, limiting root-cause analysis for intermittent degradations.

### [WL-7758]

**Title:** Normalize and scan decoded input before HTML escaping in sanitizer pipeline
**Source:** [thegent/src/thegent/security/input_sanitizer.py:40]
**Acceptance checklist:**

- [ ] Apply Unicode normalization and percent/HTML entity decoding before SQL/XSS/command pattern checks.
- [ ] Keep output escaping behavior intact while preserving deterministic max-length truncation order.
- [ ] Add tests for encoded attack payloads, mixed-encoding benign text, and normalization edge cases.
      **Notes:** Pattern checks currently run on raw input and can miss encoded payload variants that bypass first-pass detection.

### [WL-7759]

**Title:** Reject batch JSON-RPC payloads explicitly and enforce response ID type consistency
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py:134]
**Acceptance checklist:**

- [ ] Detect array payloads and return a standards-compliant invalid-request error instead of undefined dispatch behavior.
- [ ] Ensure error responses preserve valid scalar request IDs and null invalid IDs consistently.
- [ ] Add tests for single valid request, batch payload rejection, and malformed ID type handling.
      **Notes:** Dispatcher assumptions around object payloads and ID echoing can produce non-compliant responses for malformed clients.
