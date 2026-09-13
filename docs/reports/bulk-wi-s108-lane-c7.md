### [WL-10990]

**Title:** Preserve raw parse-phase projection behavior for turn/submit plan assembly
**Source:** `tests/protocols/test_wl10990_wl10999_lane_c7.py`
**Acceptance checklist:**

- [x] Keep parse phase outputs identical to input plan payload fields.
- [x] Add focused regression for preserved mapping.
      **Notes:** Covered by `test_wl10990_build_turn_submit_parse_phase_keeps_raw_plan_fields`.

### [WL-10991]

**Title:** Reject non-string approval diff during turn submit execution target resolution
**Source:** `tests/protocols/test_wl10990_wl10999_lane_c7.py`
**Acceptance checklist:**

- [x] Fail fast when `approval_diff` is non-string while required.
- [x] Preserve fail-fast error semantics.
      **Notes:** Covered by `test_wl10991_resolve_turn_submit_execution_target_rejects_non_string_diff`.

### [WL-10992]

**Title:** Preserve nullable approval payload expansion to all-`None` response field tuple
**Source:** `tests/protocols/test_wl10990_wl10999_lane_c7.py`
**Acceptance checklist:**

- [x] Return `(None, None, None)` for missing approval payload.
- [x] Add focused regression coverage.
      **Notes:** Covered by `test_wl10992_resolve_turn_submit_response_approval_fields_returns_none_tuple`.

### [WL-10993]

**Title:** Preserve approval payload in turn submit success response envelope
**Source:** `tests/protocols/test_wl10990_wl10999_lane_c7.py`
**Acceptance checklist:**

- [x] Preserve approval payload when request response is expected.
- [x] Ensure response includes turn and approval fields together.
      **Notes:** Covered by `test_wl10993_build_turn_submit_success_response_includes_approval_payload`.

### [WL-10994]

**Title:** Preserve notification-only turn/submit flow for approval request without response id
**Source:** `tests/protocols/test_wl10990_wl10999_lane_c7.py`
**Acceptance checklist:**

- [x] Handle approval submit when request id is omitted.
- [x] Produce expected notification sequence without JSON-RPC response.
      **Notes:** Covered by `test_wl10994_handle_turn_submit_request_without_id_notifies_approval_request`.

### [WL-10995]

**Title:** Preserve completion resolution contract for non-approval submission path
**Source:** `tests/protocols/test_wl10990_wl10999_lane_c7.py`
**Acceptance checklist:**

- [x] Mark turn as completed and set tool call id during completion.
- [x] Preserve terminal turn completion notification.
      **Notes:** Covered by `test_wl10995_resolve_turn_submit_completion_marks_turn_completed_and_adds_tool_call_id`.

### [WL-10996]

**Title:** Preserve turn submit side-effects phase field projection
**Source:** `tests/protocols/test_wl10990_wl10999_lane_c7.py`
**Acceptance checklist:**

- [x] Keep approval fields and user input in side-effects payload.
- [x] Maintain scalar and identity-like content.
      **Notes:** Covered by `test_wl10996_build_turn_submit_side_effects_phase_preserves_required_fields`.

### [WL-10997]

**Title:** Preserve numeric request id in turn/submit success response
**Source:** `tests/protocols/test_wl10990_wl10999_lane_c7.py`
**Acceptance checklist:**

- [x] Preserve numeric request IDs from protocol envelope.
- [x] Return response using same request identifier.
      **Notes:** Covered by `test_wl10997_handle_turn_submit_request_preserves_numeric_request_id`.

### [WL-10998]

**Title:** Reject malformed side-effects target missing turn record
**Source:** `tests/protocols/test_wl10990_wl10999_lane_c7.py`
**Acceptance checklist:**

- [x] Raise unresolved error when `turn` is missing for side-effects target.
- [x] Preserve strict error signal for invalid phase shapes.
      **Notes:** Covered by `test_wl10998_resolve_turn_submit_side_effects_target_rejects_missing_turn_payload`.

### [WL-10999]

**Title:** Reject empty approval payload IDs during extraction
**Source:** `tests/protocols/test_wl10990_wl10999_lane_c7.py`
**Acceptance checklist:**

- [x] Treat empty approval id as invalid contract.
- [x] Keep fail-fast behavior in approval payload extraction.
      **Notes:** Covered by `test_wl10999_extract_turn_submit_approval_payload_id_rejects_empty_string`.
