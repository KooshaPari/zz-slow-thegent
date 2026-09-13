### [WL-10960]

**Title:** Preserve default input behavior for missing turn-submit input parameter
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py]
**Acceptance checklist:**

- [x] Keep missing `input` defaulting to empty string.
- [x] Preserve parse-phase shape for empty-string fallback.
- [x] Add focused regression coverage.
      **Notes:** Covered by `test_wl10960_*`.

### [WL-10961]

**Title:** Prefer `unified_diff` over `diff` when both are provided
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py]
**Acceptance checklist:**

- [x] Use `unified_diff` as primary approval-diff source.
- [x] Preserve backward-compatible fallback to `diff`.
- [x] Add focused regression coverage.
      **Notes:** Covered by `test_wl10961_*`.

### [WL-10962]

**Title:** Preserve `diff` fallback behavior for approval diff extraction
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py]
**Acceptance checklist:**

- [x] Fall back to `diff` when `unified_diff` is absent.
- [x] Preserve raw diff passthrough.
- [x] Add focused regression coverage.
      **Notes:** Covered by `test_wl10962_*`.

### [WL-10963]

**Title:** Reject approval-required submit when no diff is provided
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py]
**Acceptance checklist:**

- [x] Return parse failure when approval is required and diff is missing.
- [x] Preserve `diff_required_when_requires_approval` reason code.
- [x] Add focused regression coverage.
      **Notes:** Covered by `test_wl10963_*`.

### [WL-10964]

**Title:** Reject empty/blank diff when approval is required
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py]
**Acceptance checklist:**

- [x] Reject whitespace-only approval diff.
- [x] Preserve `diff_must_be_non_empty_string` parse contract.
- [x] Add focused regression coverage.
      **Notes:** Covered by `test_wl10964_*`.

### [WL-10965]

**Title:** Reject non-string approval diff in approval-required submit
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py]
**Acceptance checklist:**

- [x] Reject non-string `unified_diff` values.
- [x] Preserve `diff_must_be_string` error code.
- [x] Add focused regression coverage.
      **Notes:** Covered by `test_wl10965_*`.

### [WL-10966]

**Title:** Preserve turn-submit side-effects resolution tuple shape
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py]
**Acceptance checklist:**

- [x] Return normalized tuple for side-effect execution.
- [x] Preserve all tuple fields and ordering.
- [x] Add focused regression coverage.
      **Notes:** Covered by `test_wl10966_*`.

### [WL-10967]

**Title:** Preserve response-phase tuple resolution for turn-submit approvals
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py]
**Acceptance checklist:**

- [x] Preserve request-id and turn resolution with approval payload.
- [x] Preserve response tuple invariants.
- [x] Add focused regression coverage.
      **Notes:** Covered by `test_wl10967_*`.

### [WL-10968]

**Title:** Preserve turn-submit start-to-approval notification ordering
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py]
**Acceptance checklist:**

- [x] Emit `turn/started` before side-effect updates.
- [x] Emit `item/agentMessage/delta` before `approval/requested`.
- [x] Add focused regression coverage.
      **Notes:** Covered by `test_wl10968_*`.

### [WL-10969]

**Title:** Return parse-failure contract for missing session in turn-submit
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py]
**Acceptance checklist:**

- [x] Fail with session-not-found error for missing `session_id`.
- [x] Preserve response-only error envelope for invalid session.
- [x] Confirm no side-effect notifications are emitted.
      **Notes:** Covered by `test_wl10969_*`.
