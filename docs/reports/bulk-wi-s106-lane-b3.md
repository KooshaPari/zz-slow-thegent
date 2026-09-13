### [WL-10950]

**Title:** Preserve response target request-id passthrough for numeric request identifiers
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py]
**Acceptance checklist:**

- [x] Resolve response target with numeric request IDs intact.
- [x] Preserve typed request-id passthrough behavior.
- [x] Add focused regression coverage.
      **Notes:** Covered by `test_wl10950_*`.

### [WL-10951]

**Title:** Preserve response target request-id passthrough for string request identifiers
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py]
**Acceptance checklist:**

- [x] Resolve response target with string request IDs intact.
- [x] Preserve request/reply envelope identity behavior.
- [x] Add focused regression coverage.
      **Notes:** Covered by `test_wl10951_*`.

### [WL-10952]

**Title:** Preserve notification-mode response target behavior with absent request id
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py]
**Acceptance checklist:**

- [x] Preserve `request_has_id=False` notification semantics.
- [x] Preserve `None` request id behavior in response target resolution.
- [x] Add focused regression coverage.
      **Notes:** Covered by `test_wl10952_*`.

### [WL-10953]

**Title:** Preserve no-response contract for turn-submit notification flow
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py]
**Acceptance checklist:**

- [x] Keep `_build_turn_submit_success_response` suppressed for notification requests.
- [x] Preserve deterministic no-envelope behavior.
- [x] Add focused regression coverage.
      **Notes:** Covered by `test_wl10953_*`.

### [WL-10954]

**Title:** Preserve response envelope contract for id-bearing turn-submit requests
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py]
**Acceptance checklist:**

- [x] Keep JSON-RPC result envelope structure stable when request id exists.
- [x] Preserve response id passthrough.
- [x] Add focused regression coverage.
      **Notes:** Covered by `test_wl10954_*`.

### [WL-10955]

**Title:** Preserve result payload shape without approval object on non-approval submit
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py]
**Acceptance checklist:**

- [x] Keep `approval` field absent when approval payload is not present.
- [x] Preserve backward-compatible result payload for non-approval paths.
- [x] Add focused regression coverage.
      **Notes:** Covered by `test_wl10955_*`.

### [WL-10956]

**Title:** Preserve result payload inclusion of approval object on approval-required submit
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py]
**Acceptance checklist:**

- [x] Keep `approval` field present when approval payload exists.
- [x] Preserve full approval payload passthrough.
- [x] Add focused regression coverage.
      **Notes:** Covered by `test_wl10956_*`.

### [WL-10957]

**Title:** Preserve optional approval diff semantics for response payload validation
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py]
**Acceptance checklist:**

- [x] Keep approval diff optional in extractor contract.
- [x] Preserve `None` behavior when diff key is absent.
- [x] Add focused regression coverage.
      **Notes:** Covered by `test_wl10957_*`.

### [WL-10958]

**Title:** Preserve fail-fast behavior for empty approval id payloads
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py]
**Acceptance checklist:**

- [x] Reject empty approval id strings.
- [x] Preserve deterministic unresolved error semantics.
- [x] Add focused regression coverage.
      **Notes:** Covered by `test_wl10958_*`.

### [WL-10959]

**Title:** Preserve fail-fast behavior for empty approval status payloads
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py]
**Acceptance checklist:**

- [x] Reject empty approval status strings.
- [x] Preserve deterministic unresolved error semantics.
- [x] Add focused regression coverage.
      **Notes:** Covered by `test_wl10959_*`.
