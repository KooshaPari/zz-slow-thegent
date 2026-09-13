### [WL-8020]

**Title:** Make explicit Ollama provider/model validation return typed failure metadata
**Source:** [thegent/src/thegent/cli/services/run_model_helpers.py:41]
**Acceptance checklist:**

- [ ] Return a structured validation payload containing requested provider, model, and remediation hint when `--provider ollama` is misconfigured.
- [ ] Preserve current behavior when Ollama provider inputs are valid.
- [ ] Add tests for missing model list, unsupported model, and successful resolution paths.
      **Notes:** This improves UI-level error clarity and reduces ambiguous routing fallbacks for local model setup.

### [WL-8021]

**Title:** Make session cwd resolution cache explicitly invalidated on path churn
**Source:** [thegent/src/thegent/cli/services/run_session_helpers.py:33]
**Acceptance checklist:**

- [ ] Invalidate `_CWD_CACHE` entries when process working directory changes.
- [ ] Keep resolved cwd behavior unchanged for explicit `--cd` and project-root inference.
- [ ] Add regression coverage for stale cache reuse after `cd` context changes and repeated calls.
      **Notes:** The TTL cache currently optimizes repeated calls but can serve stale entries across cwd transitions.

### [WL-8022]

**Title:** Add schema-versioned parsing guardrails for normalization policy settings
**Source:** [thegent/src/thegent/config.py:219]
**Acceptance checklist:**

- [ ] Add validation for `retention_by_domain` shape and enforce versioned migration handling for malformed values.
- [ ] Preserve valid legacy payloads and existing environment-variable overrides.
- [ ] Add unit tests for happy path, malformed map payload, and migration fallback behavior.
      **Notes:** Settings parsing currently accepts a broad set of input forms and needs explicit boundary checks around policy migration.

### [WL-8023]

**Title:** Expose router status snapshots with per-agent rationale freshness
**Source:** [thegent/src/thegent/routing/route_executor.py:172]
**Acceptance checklist:**

- [ ] Attach age and freshness indicators to each agent rationale in status output.
- [ ] Keep existing routing decision counting and policy calculation unchanged.
- [ ] Add tests for fresh snapshot inclusion and stale-state transitions.
      **Notes:** Debugging routing drift is slower today without recency context on last per-agent rationale.

### [WL-8024]

**Title:** Add deterministic strategy execution order for cache pre-warm runs
**Source:** [thegent/src/thegent/cache/pre_warmer.py:128]
**Acceptance checklist:**

- [ ] Preserve registration order when warm cycles run across multiple strategies.
- [ ] Ensure failed strategy runs record error state without aborting the remaining queue.
- [ ] Add tests for deterministic ordering, error isolation, and completion when one strategy fails.
      **Notes:** Deterministic warm ordering is required for reproducible startup performance diagnostics.

### [WL-8025]

**Title:** Add namespace-aware semantic cache hit telemetry on lookup misses
**Source:** [thegent/src/thegent/routing/semantic_cache.py:222]
**Acceptance checklist:**

- [ ] Emit hit/miss counters with namespace and reason (provider-unavailable, expired-only, threshold-miss).
- [ ] Preserve exact match behavior and provider fallback semantics.
- [ ] Add tests covering namespace filters, miss reasons, and hit threshold gating.
      **Notes:** Current miss details are only implicit; explicit telemetry will improve cache tuning.

### [WL-8026]

**Title:** Tighten validator contracts for email and URL pattern edge cases
**Source:** [thegent/src/thegent/validation/validators.py:23]
**Acceptance checklist:**

- [ ] Reject clearly invalid unicode and whitespace-heavy inputs before regex evaluation.
- [ ] Preserve backward-compatible acceptance for currently valid legacy addresses.
- [ ] Add tests for internationalized addresses, trailing spaces, and scheme edge cases.
      **Notes:** Validator regexes are lightweight and need explicit boundary enforcement for production traffic.

### [WL-8027]

**Title:** Extend Prometheus rendering with deterministic metric label ordering for gauges
**Source:** [thegent/src/thegent/observability/prometheus.py:96]
**Acceptance checklist:**

- [ ] Sort histogram bucket output deterministically across runs and repeated render calls.
- [ ] Preserve existing metric names, HELP/TYPE lines, and counter/gauge semantics.
- [ ] Add render-order snapshots for counters, gauges, and histograms in unit tests.
      **Notes:** Stable output ordering is required for reliable snapshot-based assertions and dashboards.

### [WL-8028]

**Title:** Improve rate-limiter `reset_after` calculation precision
**Source:** [thegent/src/thegent/routing/rate_limiter.py:76]
**Acceptance checklist:**

- [ ] Return zero-safe `reset_after` for empty windows and consistent behavior across boundary timestamps.
- [ ] Preserve existing allow/check API and consumption semantics for both throttling and pass-through paths.
- [ ] Add tests for zero-count windows, boundary expiries, and multi-key isolation.
      **Notes:** Timestamp arithmetic should be explicit to avoid negative or misleading TTL resets under low-volume traffic.

### [WL-8029]

**Title:** Preserve conflict ordering guarantees when resolving and re-queuing manual conflict items
**Source:** [thegent/src/thegent/integrations/conflict_queue.py:116]
**Acceptance checklist:**

- [ ] Ensure `dequeue()` maintains FIFO order for unresolved entries after resolve/reinsert cycles.
- [ ] Preserve existing queue semantics for `resolve()` and `_resolved_map` transitions.
- [ ] Add tests for duplicate resolves, queue starvation prevention, and first-unresolved retrieval.
      **Notes:** Manual conflict handling is a governance-critical path and needs deterministic ordering guarantees.
