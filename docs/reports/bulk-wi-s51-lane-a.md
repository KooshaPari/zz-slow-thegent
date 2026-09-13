### [WL-8070]

**Title:** Make route-execution rationale snapshots include immutable decision hash
**Source:** [thegent/src/thegent/routing/route_executor.py:249]
**Acceptance checklist:**

- [ ] Add deterministic hash/correlation metadata to `ExecutionOutcome` artifacts without changing existing success path output.
- [ ] Ensure hash generation is stable across equivalent outcomes and explicit on every routed completion.
- [ ] Add unit coverage for hash reproducibility and mismatch cases when reranking changes rationale inputs.
      **Notes:** Strengthens auditability of routing arbitration outputs for dispute analysis.

### [WL-8071]

**Title:** Add deterministic retention policy for claimable prompt-queue snapshots
**Source:** [thegent/src/thegent/queue/storage.py:95]
**Acceptance checklist:**

- [ ] Preserve pending-count semantics while making snapshot reads deterministic under concurrent claims.
- [ ] Keep queue filtering behavior unchanged for pending/retry status filters.
- [ ] Add regression tests for ordering under concurrent `list_pending`/`claim` usage.
      **Notes:** Queue visibility should remain stable for operators relying on first-claimed FIFO order.

### [WL-8072]

**Title:** Separate circuit-breaker OPEN rejection from post-failure tripping diagnostics
**Source:** [thegent/src/thegent/routing/circuit_breaker.py:99]
**Acceptance checklist:**

- [ ] Keep `CircuitOpenError` raised only for pre-call open-state rejections while preserving existing open transitions.
- [ ] Add explicit telemetry fields for was-open vs just-tripped state in logs.
- [ ] Add tests for open pre-check, trip-on-call, and already-open rejection paths.
      **Notes:** This avoids conflating initial rejection with immediate post-failure breaker transitions.

### [WL-8073]

**Title:** Emit richer budget exhaustion reason codes in cost tracking
**Source:** [thegent/src/thegent/routing/cost_tracker.py:153]
**Acceptance checklist:**

- [ ] Add machine-readable reason field when daily budget thresholds are crossed.
- [ ] Preserve existing warning log and tracking counters during budget overruns.
- [ ] Add tests for crossing warning and exact-threshold boundaries.
      **Notes:** Operators need explicit reason payloads to distinguish hard stop vs soft warning in downstream telemetry.

### [WL-8074]

**Title:** Stabilize Prometheus label ordering for autosync connector metrics
**Source:** [thegent/src/thegent/observability/prometheus.py:249]
**Acceptance checklist:**

- [ ] Sort label keys for autosync debug metrics and retain previous metric names and HELP/TYPE lines.
- [ ] Keep rendering deterministic across repeated invocations with identical payloads.
- [ ] Add snapshot tests for autosync connector metric line ordering.
      **Notes:** Deterministic ordering will reduce alert noise in metric-diff tooling.

### [WL-8075]

**Title:** Make config resolution failures return structured error classes in control plane
**Source:** [thegent/src/thegent/control_plane/server.py:183]
**Acceptance checklist:**

- [ ] Preserve successful /v1/config/resolve payload shape while adding explicit error payload for invalid keys.
- [ ] Return standardized status details for tenant/session/validation failure branches.
- [ ] Add tests for malformed keys, tenant-file decode failures, and successful schema-valid responses.
      **Notes:** Better error structuring improves client retry and remediation behavior.

### [WL-8076]

**Title:** Split prompt rewrite passes into configurable precedence phases
**Source:** [thegent/src/thegent/routing/prompt_rewriter.py:183]
**Acceptance checklist:**

- [ ] Isolate truncation as final phase and record phase order in rewrite result metadata.
- [ ] Keep current rewrite output for default config when no rule matches.
- [ ] Add tests for equal-priority rule ordering and truncation-after-rules behavior.
      **Notes:** Makes provider/model rewriting behavior deterministic and explainable.

### [WL-8077]

**Title:** Normalize validator edge-case responses for URL/email checks
**Source:** [thegent/src/thegent/validation/validators.py:23]
**Acceptance checklist:**

- [ ] Return explicit false for whitespace-trimmed or malformed UTF-8 URLs/emails.
- [ ] Preserve current acceptance for standard valid inputs.
- [ ] Add table-driven tests for whitespace, missing scheme, and unicode edge cases.
      **Notes:** Validation should fail fast before regex side effects in downstream routing.

### [WL-8078]

**Title:** Expose retention policy parse errors as typed exceptions in config settings
**Source:** [thegent/src/thegent/config.py:219]
**Acceptance checklist:**

- [ ] Preserve successful settings loading when `retention_by_domain` payload is valid.
- [ ] Add dedicated error path for malformed retention maps with key/value diagnostics.
- [ ] Add tests for missing keys, non-int values, and mixed-validity inputs.
      **Notes:** Prevents ambiguous startup behavior when policy JSON is malformed.

### [WL-8079]

**Title:** Guard session fork/rollback error classes for better boundary behavior
**Source:** [thegent/src/thegent/session/manager.py:84]
**Acceptance checklist:**

- [ ] Keep existing fork/rollback semantics while adding clearer invalid range and missing-session errors.
- [ ] Ensure rollback returns final depth consistently when no-op branches are no longer hit.
- [ ] Add tests for boundary conditions around empty sessions, negative rollback, and max turn rollback.
      **Notes:** Tightens session control behavior and lowers ambiguity in recovery workflows.
