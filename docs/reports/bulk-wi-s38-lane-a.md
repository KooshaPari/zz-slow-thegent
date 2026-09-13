### [WL-7420]

**Title:** Replace no-op low-confidence handoff branch with explicit confidence-degradation handling
**Source:** [thegent/src/thegent/execution.py:589]
**Acceptance checklist:**

- [ ] Replace the `pass` branch for `confidence < 0.8` with explicit state updates and audit metadata.
- [ ] Preserve handoff confirmation semantics for high-confidence transitions.
- [ ] Add tests for high-confidence, low-confidence, and boundary-threshold handoff confirmations.
      **Notes:** The current low-confidence path is intentionally detected but performs no action, leaving continuity risk invisible.

### [WL-7421]

**Title:** Surface chat-line validation failures without silently dropping malformed records
**Source:** [thegent/src/thegent/execution.py:1389]
**Acceptance checklist:**

- [ ] Replace broad chat-line parse suppression with explicit validation-error handling and structured diagnostics.
- [ ] Preserve skip-on-invalid behavior for malformed lines while keeping successful lines unaffected.
- [ ] Add tests for valid chat entries, blank lines, and malformed JSON payloads.
      **Notes:** Returning `None` for all exceptions hides whether failures are schema-related or transport-related corruption.

### [WL-7422]

**Title:** Distinguish pending-message parse faults from non-pending message filtering outcomes
**Source:** [thegent/src/thegent/execution.py:1401]
**Acceptance checklist:**

- [ ] Replace broad message parse suppression with explicit parse and schema error branches.
- [ ] Preserve current behavior that returns only `pending` messages.
- [ ] Add tests for pending entries, non-pending entries, and malformed message lines.
      **Notes:** The generic `except` path conflates invalid records with valid-but-non-pending records.

### [WL-7423]

**Title:** Classify run-registry tail hash read failures instead of silently returning missing-hash state
**Source:** [thegent/src/thegent/execution.py:1464]
**Acceptance checklist:**

- [ ] Replace broad `_get_last_hash` exception suppression with explicit file-read, JSON-decode, and hash-field extraction branches.
- [ ] Preserve return contract of `None` when no hash exists.
- [ ] Add tests for empty registry, malformed tail record, and valid hash retrieval.
      **Notes:** Silent fallback masks corruption in the hash chain bootstrap path.

### [WL-7424]

**Title:** Preserve trust-boundary state corruption diagnostics while maintaining nullable environment lookup
**Source:** [thegent/src/thegent/execution.py:2157]
**Acceptance checklist:**

- [ ] Replace broad environment-state parse suppression with explicit read/decode failure categories.
- [ ] Preserve current API behavior of returning `None` when no prior environment is available.
- [ ] Add tests for valid state payloads, malformed JSON, and unreadable state file paths.
      **Notes:** Returning `None` for every failure mode hides transition-governance state corruption.

### [WL-7425]

**Title:** Split MAIF artifact generation dependency failures from signer/runtime serialization faults
**Source:** [thegent/src/thegent/execution.py:2232]
**Acceptance checklist:**

- [ ] Replace broad MAIF generation fallback handling with explicit dependency, artifact-write, and serialization failure branches.
- [ ] Preserve deterministic artifact generation path and documented fallback behavior where applicable.
- [ ] Add tests for successful Rust MAIF generation, manager failure, and fallback artifact integrity.
      **Notes:** One catch-all path currently obscures root cause when MAIF emission degrades.

### [WL-7426]

**Title:** Differentiate registry integrity-check JSON decode failures from hash/signature mismatch findings
**Source:** [thegent/src/thegent/execution.py:2322]
**Acceptance checklist:**

- [ ] Replace broad integrity loop exception handling with explicit JSON parse and field-shape validation branches.
- [ ] Preserve corruption counting and issue aggregation semantics.
- [ ] Add tests for valid lines, malformed JSON lines, and incomplete record payloads.
      **Notes:** Current error aggregation labels all failures as decode errors even when structure is valid but incomplete.

### [WL-7427]

**Title:** Make escalation queue listing robust by tracking dropped malformed items with explicit counters
**Source:** [thegent/src/thegent/execution.py:2515]
**Acceptance checklist:**

- [ ] Replace silent malformed-line skips in `list_pending` with explicit dropped-item accounting and diagnostics.
- [ ] Preserve successful item ordering and `past_sla_only` filter behavior.
- [ ] Add tests for valid queue entries, malformed lines, and mixed valid/invalid queues.
      **Notes:** Silent `continue` loses observability into escalation queue data quality.

### [WL-7428]

**Title:** Prevent unresolved escalation rewrite corruption when queue resolution encounters malformed records
**Source:** [thegent/src/thegent/execution.py:2537]
**Acceptance checklist:**

- [ ] Replace broad parse suppression in escalation `resolve` with explicit malformed-record retention and diagnostics.
- [ ] Preserve successful resolution semantics for matching pending items.
- [ ] Add tests for mixed queue content, malformed records, and successful resolution persistence.
      **Notes:** Suppressed parse failures can conceal persistent queue corruption while rewriting files.

### [WL-7429]

**Title:** Separate REST transport failures from response-shape contract violations in MCP REST bridge
**Source:** [thegent/src/thegent/mcp/rest_to_mcp.py:116]
**Acceptance checklist:**

- [ ] Replace broad request exception capture with explicit timeout, network, and HTTP protocol failure branches.
- [ ] Preserve non-throwing tool contract that returns structured `RestToolResult` errors.
- [ ] Add tests for successful responses, timeout/network exceptions, and invalid method/endpoint failures.
      **Notes:** A single generic error channel currently masks the operational cause of REST tool failures.
