### [WL-10940]

**Title:** Preserve response-target request-id gate with explicit boolean extraction helper
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py]
**Acceptance checklist:**

- [x] Extract request-id response gate into dedicated helper.
- [x] Fail loudly on non-boolean values.
- [x] Add focused regression coverage.
      **Notes:** Implemented via `_extract_turn_submit_response_request_has_id`.

### [WL-10941]

**Title:** Preserve fail-fast request-id gate behavior for malformed response-phase payloads
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py]
**Acceptance checklist:**

- [x] Keep deterministic error surface for malformed request-id gate payloads.
- [x] Preserve existing response-target unresolved semantics.
- [x] Add regression coverage for non-boolean gate values.
      **Notes:** Covered by `test_wl10941_*`.

### [WL-10942]

**Title:** Preserve response-target turn extraction with explicit typed helper
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py]
**Acceptance checklist:**

- [x] Extract turn payload lookup into dedicated helper.
- [x] Preserve dict-only contract for turn payload.
- [x] Add focused regression coverage.
      **Notes:** Implemented via `_extract_turn_submit_response_turn`.

### [WL-10943]

**Title:** Preserve fail-fast turn extraction behavior for malformed turn payloads
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py]
**Acceptance checklist:**

- [x] Keep deterministic unresolved error on non-dict turn payload.
- [x] Preserve existing response-target behavior for valid payloads.
- [x] Add regression coverage.
      **Notes:** Covered by `test_wl10943_*`.

### [WL-10944]

**Title:** Preserve optional approval payload behavior with explicit extractor helper
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py]
**Acceptance checklist:**

- [x] Extract approval payload lookup into dedicated helper.
- [x] Preserve optional `None` behavior.
- [x] Add focused regression coverage.
      **Notes:** Implemented via `_extract_turn_submit_response_approval_payload`.

### [WL-10945]

**Title:** Preserve fail-fast behavior on malformed non-dict approval payloads
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py]
**Acceptance checklist:**

- [x] Reject non-dict approval payloads explicitly.
- [x] Preserve unresolved error semantics.
- [x] Add regression coverage.
      **Notes:** Covered by `test_wl10945_*`.

### [WL-10946]

**Title:** Preserve approval-id contract with explicit extraction helper
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py]
**Acceptance checklist:**

- [x] Extract approval-id validation into dedicated helper.
- [x] Reject missing/empty id loudly.
- [x] Add regression coverage.
      **Notes:** Implemented via `_extract_turn_submit_approval_payload_id`.

### [WL-10947]

**Title:** Preserve approval-status contract with explicit extraction helper
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py]
**Acceptance checklist:**

- [x] Extract approval-status validation into dedicated helper.
- [x] Reject missing/empty status loudly.
- [x] Add regression coverage.
      **Notes:** Implemented via `_extract_turn_submit_approval_payload_status`.

### [WL-10948]

**Title:** Preserve optional approval diff typing with explicit extraction helper
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py]
**Acceptance checklist:**

- [x] Extract approval-diff validation into dedicated helper.
- [x] Reject non-string diff payloads.
- [x] Add regression coverage.
      **Notes:** Implemented via `_extract_turn_submit_approval_payload_diff`.

### [WL-10949]

**Title:** Preserve notification-mode approval side effects with no response envelope
**Source:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py]
**Acceptance checklist:**

- [x] Preserve side effects for notification-only approval-required turn submit requests.
- [x] Preserve no-response envelope behavior when request id is absent.
- [x] Add end-to-end regression coverage.
      **Notes:** Covered by `test_wl10949_*`.
