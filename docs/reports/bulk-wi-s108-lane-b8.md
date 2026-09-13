### [WL-11010]

**Title:** Preserve session-id validation on turn/submit parse phase
**Source:** `tests/protocols/test_wl11010_wl11019_lane_b8.py`
**Acceptance checklist:**

- [x] Reject missing `session_id`.
- [x] Reject non-string `session_id`.
      **Notes:** Covered by `test_wl11010_build_turn_submit_phase_plan_rejects_missing_session_id` and `test_wl11011_build_turn_submit_phase_plan_rejects_non_string_session_id`.

### [WL-11011]

**Title:** Preserve input type guard for turn/submit requests
**Source:** `tests/protocols/test_wl11010_wl11019_lane_b8.py`
**Acceptance checklist:**

- [x] Reject non-string `input` values before plan building.
      **Notes:** Covered by `test_wl11012_build_turn_submit_phase_plan_rejects_non_string_input`.

### [WL-11012]

**Title:** Preserve strict boolean contract for `requires_approval`
**Source:** `tests/protocols/test_wl11010_wl11019_lane_b8.py`
**Acceptance checklist:**

- [x] Reject non-bool `requires_approval`.
      **Notes:** Covered by `test_wl11013_build_turn_submit_phase_plan_rejects_non_bool_requires_approval_flag`.

### [WL-11013]

**Title:** Preserve optional approval-diff nullability for non-approval path
**Source:** `tests/protocols/test_wl11010_wl11019_lane_b8.py`
**Acceptance checklist:**

- [x] Keep side-effects target tuple shape when `requires_approval` is false and `approval_diff` is `None`.
      **Notes:** Covered by `test_wl11014_build_turn_submit_side_effects_target_keeps_optional_missing_approval_diff`.

### [WL-11014]

**Title:** Preserve request-id type strictness in turn/submit response extraction
**Source:** `tests/protocols/test_wl11010_wl11019_lane_b8.py`
**Acceptance checklist:**

- [x] Reject boolean request IDs when response contract is active.
      **Notes:** Covered by `test_wl11015_extract_turn_submit_response_request_id_rejects_bool_request_id_when_expected`.

### [WL-11015]

**Title:** Preserve numeric request-id pass-through semantics
**Source:** `tests/protocols/test_wl11010_wl11019_lane_b8.py`
**Acceptance checklist:**

- [x] Keep non-bool numeric request IDs unchanged when valid.
      **Notes:** Covered by `test_wl11016_extract_turn_submit_response_request_id_accepts_numeric_request_id`.

### [WL-11016]

**Title:** Preserve float request ID in success response envelope
**Source:** `tests/protocols/test_wl11010_wl11019_lane_b8.py`
**Acceptance checklist:**

- [x] Return request response with the same float `id` and no accidental approval payload insertion.
      **Notes:** Covered by `test_wl11017_build_turn_submit_success_response_preserves_float_request_id`.

### [WL-11017]

**Title:** Preserve parse-failure passthrough for turn/submit
**Source:** `tests/protocols/test_wl11010_wl11019_lane_b8.py`
**Acceptance checklist:**

- [x] Return exact parse error payload unmodified from parse-failure handler.
      **Notes:** Covered by `test_wl11018_handle_turn_submit_parse_failure_returns_exact_error_payload`.

### [WL-11018]

**Title:** Preserve response target strictness for malformed approval payload
**Source:** `tests/protocols/test_wl11010_wl11019_lane_b8.py`
**Acceptance checklist:**

- [x] Raise on non-dict approval payload during response target resolution.
      **Notes:** Covered by `test_wl11019_resolve_turn_submit_response_target_rejects_non_dict_approval_payload_shape`.

### [WL-11019]

**Title:** Turn/submit response helpers remain consistent
**Source:** `tests/protocols/test_wl11010_wl11019_lane_b8.py`
**Acceptance checklist:**

- [x] Keep response-helper contract aligned across request-id parsing and response builders.
      **Notes:** Covered by items `WL-11015` through `WL-11017` in this slice.
