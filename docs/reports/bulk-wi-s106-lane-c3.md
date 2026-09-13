### [WL-10950]

**Title:** Preserve response-target request-id extraction via explicit helper
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py]
**Acceptance checklist:**

- [x] Extract request-id lookup into a dedicated response-target helper.
- [x] Preserve deterministic response/no-response routing inputs.
- [x] Add focused regression coverage.
      **Notes:** Implemented via `_extract_turn_submit_response_request_id`.

### [WL-10951]

**Title:** Preserve fail-fast request-id validation when response envelope is required
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py]
**Acceptance checklist:**

- [x] Reject missing/invalid request id when `request_has_id=True`.
- [x] Keep failure surface deterministic.
- [x] Add targeted regression coverage.
      **Notes:** Covered by `test_wl10951_*`.

### [WL-10952]

**Title:** Preserve optional approval-id extraction behavior with explicit helper
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py]
**Acceptance checklist:**

- [x] Extract approval-id lookup into a dedicated helper.
- [x] Preserve `None` behavior when approval payload is absent.
- [x] Add focused regression coverage.
      **Notes:** Implemented via `_extract_turn_submit_response_approval_id`.

### [WL-10953]

**Title:** Preserve fail-fast approval-id contract validation in response target resolution
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py]
**Acceptance checklist:**

- [x] Reject malformed approval-id payloads explicitly.
- [x] Keep unresolved error semantics unchanged.
- [x] Add targeted regression coverage.
      **Notes:** Covered by `test_wl10953_*`.

### [WL-10954]

**Title:** Preserve optional approval-status extraction behavior with explicit helper
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py]
**Acceptance checklist:**

- [x] Extract approval-status lookup into a dedicated helper.
- [x] Preserve `None` behavior when approval payload is absent.
- [x] Add focused regression coverage.
      **Notes:** Implemented via `_extract_turn_submit_response_approval_status`.

### [WL-10955]

**Title:** Preserve fail-fast approval-status contract validation in response target resolution
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py]
**Acceptance checklist:**

- [x] Reject malformed approval-status payloads explicitly.
- [x] Keep unresolved error semantics unchanged.
- [x] Add targeted regression coverage.
      **Notes:** Covered by `test_wl10955_*`.

### [WL-10956]

**Title:** Preserve approval-diff extraction through explicit response helper
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py]
**Acceptance checklist:**

- [x] Extract approval-diff lookup into a dedicated helper.
- [x] Preserve valid string diff behavior.
- [x] Add focused regression coverage.
      **Notes:** Implemented via `_extract_turn_submit_response_approval_diff`.

### [WL-10957]

**Title:** Preserve fail-fast approval-diff typing on malformed response payloads
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py]
**Acceptance checklist:**

- [x] Reject non-string approval diff payloads.
- [x] Keep unresolved error semantics unchanged.
- [x] Add targeted regression coverage.
      **Notes:** Covered by `test_wl10957_*`.

### [WL-10958]

**Title:** Preserve grouped approval-field response resolution via explicit phase helper
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py]
**Acceptance checklist:**

- [x] Add dedicated helper to resolve approval id/status/diff tuple.
- [x] Keep response target parsing deterministic.
- [x] Add focused regression coverage.
      **Notes:** Implemented via `_resolve_turn_submit_response_approval_fields`.

### [WL-10959]

**Title:** Preserve approval-required turn-submit response envelope parity after helper extraction
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py]
**Acceptance checklist:**

- [x] Preserve response envelope id/result payload on approval-required requests.
- [x] Preserve `approval/requested` notification side effect.
- [x] Add end-to-end regression coverage.
      **Notes:** Covered by `test_wl10959_*`.
