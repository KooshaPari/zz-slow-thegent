### [WL-11010]

**Title:** Preserve session-id required validation when turn/submit params omit session id.
**Source:** `tests/protocols/test_wl11010_wl11019_lane_c10.py`
**Acceptance checklist:**

- [x] Reject missing `session_id`.
- [x] Return `session_id_required` structured parse reason.
      **Notes:** Covered by `test_wl11010_build_turn_submit_phase_plan_rejects_missing_session_id`.

### [WL-11011]

**Title:** Preserve session-id type validation for non-string identifiers in turn/submit.
**Source:** `tests/protocols/test_wl11010_wl11019_lane_c10.py`
**Acceptance checklist:**

- [x] Reject non-string `session_id`.
- [x] Return `session_id_required` structured parse reason.
      **Notes:** Covered by `test_wl11011_build_turn_submit_phase_plan_rejects_non_string_session_id`.

### [WL-11012]

**Title:** Preserve input type validation for non-string turn payload input.
**Source:** `tests/protocols/test_wl11010_wl11019_lane_c10.py`
**Acceptance checklist:**

- [x] Reject non-string `input` values before execution.
- [x] Return `input_must_be_string` when invalid.
      **Notes:** Covered by `test_wl11012_build_turn_submit_phase_plan_rejects_non_string_input`.

### [WL-11013]

**Title:** Preserve strict boolean contract for `requires_approval`.
**Source:** `tests/protocols/test_wl11010_wl11019_lane_c10.py`
**Acceptance checklist:**

- [x] Reject non-bool `requires_approval`.
- [x] Return `requires_approval_must_be_boolean`.
      **Notes:** Covered by `test_wl11013_build_turn_submit_phase_plan_rejects_non_bool_requires_approval_flag`.

### [WL-11014]

**Title:** Preserve approval-diff optional semantics when not required.
**Source:** `tests/protocols/test_wl11010_wl11019_lane_c10.py`
**Acceptance checklist:**

- [x] Keep tuple shape stable when `requires_approval=False` and `approval_diff=None`.
      **Notes:** Covered by `test_wl11014_build_turn_submit_side_effects_target_keeps_optional_missing_approval_diff`.

### [WL-11015]

**Title:** Preserve strict request-id parsing when response path requires IDs.
**Source:** `tests/protocols/test_wl11010_wl11019_lane_c10.py`
**Acceptance checklist:**

- [x] Reject boolean request IDs when `request_has_id=True`.
      **Notes:** Covered by `test_wl11015_extract_turn_submit_response_request_id_rejects_bool_request_id_when_expected`.

### [WL-11016]

**Title:** Preserve numeric request-id pass-through semantics.
**Source:** `tests/protocols/test_wl11010_wl11019_lane_c10.py`
**Acceptance checklist:**

- [x] Keep numeric request IDs unchanged when valid.
      **Notes:** Covered by `test_wl11016_extract_turn_submit_response_request_id_accepts_numeric_request_id`.

### [WL-11017]

**Title:** Preserve float request-id preservation in turn submit success responses.
**Source:** `tests/protocols/test_wl11010_wl11019_lane_c10.py`
**Acceptance checklist:**

- [x] Return success payload with exact float request ID.
- [x] Avoid accidental approval payload insertion.
      **Notes:** Covered by `test_wl11017_build_turn_submit_success_response_preserves_float_request_id`.

### [WL-11018]

**Title:** Preserve parse-failure passthrough for turn/submit.
**Source:** `tests/protocols/test_wl11010_wl11019_lane_c10.py`
**Acceptance checklist:**

- [x] Return exact parse error payload without shaping.
      **Notes:** Covered by `test_wl11018_handle_turn_submit_parse_failure_returns_exact_error_payload`.

### [WL-11019]

**Title:** Preserve response target strictness for malformed approval payload shape.
**Source:** `tests/protocols/test_wl11010_wl11019_lane_c10.py`
**Acceptance checklist:**

- [x] Raise on non-dict approval payload during target resolution.
      **Notes:** Covered by `test_wl11019_resolve_turn_submit_response_target_rejects_non_dict_approval_payload_shape`.
