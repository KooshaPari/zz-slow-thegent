### [WL-10930]

**Title:** Preserve response shaping by separating response phase build and target resolution
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py]
**Acceptance checklist:**

- [x] Keep response-phase assembly deterministic.
- [x] Preserve existing response/no-response behavior.
- [x] Add regression tests around response-phase payload boundaries.
      **Notes:** Implemented via `_build_turn_submit_response_phase` contract tests in lane-B WL file.

### [WL-10931]

**Title:** Preserve no-id notification semantics in response target resolution
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py]
**Acceptance checklist:**

- [x] Resolve request/turn payload without requiring approval payload.
- [x] Preserve no-response behavior when request id is absent.
- [x] Add regression tests for no-id path.
      **Notes:** Validated with `test_wl10931_*` and `test_wl10939_*`.

### [WL-10932]

**Title:** Preserve approval payload contract with explicit validation helper
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py]
**Acceptance checklist:**

- [x] Introduce explicit validation for approval payload shape.
- [x] Fail loudly on malformed contracts.
- [x] Cover valid payload contract.
      **Notes:** Added `_validate_turn_submit_approval_payload`.

### [WL-10933]

**Title:** Preserve fail-fast behavior for missing approval id
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py]
**Acceptance checklist:**

- [x] Reject malformed approval payloads missing required id.
- [x] Keep error surface deterministic.
- [x] Add targeted regression test.
      **Notes:** Covered by `test_wl10933_*`.

### [WL-10934]

**Title:** Preserve fail-fast behavior for missing approval status
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py]
**Acceptance checklist:**

- [x] Reject malformed approval payloads missing required status.
- [x] Keep contract validation explicit.
- [x] Add targeted regression test.
      **Notes:** Covered by `test_wl10934_*`.

### [WL-10935]

**Title:** Preserve strict typing by rejecting non-string approval diff payloads
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py]
**Acceptance checklist:**

- [x] Reject non-string `diff` payloads.
- [x] Keep valid `diff` payload behavior unchanged.
- [x] Add targeted regression test.
      **Notes:** Covered by `test_wl10935_*`.

### [WL-10936]

**Title:** Preserve response-target integrity by rejecting non-object approval payloads
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py]
**Acceptance checklist:**

- [x] Guard response target against invalid approval payload types.
- [x] Fail loudly with deterministic error text.
- [x] Add targeted regression test.
      **Notes:** Covered by `test_wl10936_*`.

### [WL-10937]

**Title:** Preserve runtime completion path for non-approval turn submit
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py]
**Acceptance checklist:**

- [x] Keep non-approval submit path completed with notifications.
- [x] Ensure no approval payload leaks into response.
- [x] Add end-to-end regression test.
      **Notes:** Covered by `test_wl10937_*`.

### [WL-10938]

**Title:** Preserve runtime approval path with validated response payload
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py]
**Acceptance checklist:**

- [x] Keep approval-required submit path awaiting approval.
- [x] Validate returned approval payload contract.
- [x] Add end-to-end regression test.
      **Notes:** Covered by `test_wl10938_*`.

### [WL-10939]

**Title:** Preserve side effects for notification-only turn submit requests
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py]
**Acceptance checklist:**

- [x] Ensure notification-only requests emit side effects without response.
- [x] Preserve started/completed notification ordering.
- [x] Add end-to-end regression test.
      **Notes:** Covered by `test_wl10939_*`.
