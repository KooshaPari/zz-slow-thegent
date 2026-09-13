### [WL-11020]

**Title:** Preserve parse-error pass-through identity
**Source:** `tests/protocols/test_wl11020_wl11029_lane_c10b.py`
**Acceptance checklist:**

- [x] Return raw dict parse-error payload unchanged when parse_error is a dict.
      **Notes:** Covered by `test_wl11020_resolve_turn_submit_parse_error_returns_error_payload`.

### [WL-11021]

**Title:** Preserve parse-error absence semantics
**Source:** `tests/protocols/test_wl11020_wl11029_lane_c10b.py`
**Acceptance checklist:**

- [x] Return `None` when parse error is missing or explicitly `None`.
      **Notes:** Covered by `test_wl11021_resolve_turn_submit_parse_error_returns_none_for_missing_payload`.

### [WL-11022]

**Title:** Preserve parse-phase pass-through for non-approval turns
**Source:** `tests/protocols/test_wl11020_wl11029_lane_c10b.py`
**Acceptance checklist:**

- [x] Keep `requires_approval=False` and `approval_diff=None` when approval is not requested.
      **Notes:** Covered by `test_wl11022_build_turn_submit_parse_phase_rejects_missing_approval_diff_only_when_needed`.

### [WL-11023]

**Title:** Preserve execution-target decomposition for valid parse output
**Source:** `tests/protocols/test_wl11020_wl11029_lane_c10b.py`
**Acceptance checklist:**

- [x] Resolve and return execution tuple fields for valid parse phase.
      **Notes:** Covered by `test_wl11023_build_turn_submit_execution_phase_returns_execution_target`.

### [WL-11024]

**Title:** Preserve execution-target strict typing in plan resolver
**Source:** `tests/protocols/test_wl11020_wl11029_lane_c10b.py`
**Acceptance checklist:**

- [x] Raise for invalid session type during execution target resolution.
      **Notes:** Covered by `test_wl11024_build_turn_submit_execution_target_rejects_invalid_plan_shape`.

### [WL-11025]

**Title:** Preserve turn/submit commit phase structure
**Source:** `tests/protocols/test_wl11020_wl11029_lane_c10b.py`
**Acceptance checklist:**

- [x] Build commit phase with turn ID, turn payload, and session object.
      **Notes:** Covered by `test_wl11025_build_turn_submit_commit_phase_keeps_turn_shape`.

### [WL-11026]

**Title:** Preserve commit-target strictness on malformed tuple input
**Source:** `tests/protocols/test_wl11020_wl11029_lane_c10b.py`
**Acceptance checklist:**

- [x] Raise for non-string turn ID in commit target resolution.
      **Notes:** Covered by `test_wl11026_resolve_turn_submit_commit_target_rejects_invalid_fields`.

### [WL-11027]

**Title:** Preserve side-effects payload defaults for no-approval path
**Source:** `tests/protocols/test_wl11020_wl11029_lane_c10b.py`
**Acceptance checklist:**

- [x] Keep `requires_approval=False` and `approval_diff=None` in side-effects phase.
      **Notes:** Covered by `test_wl11027_build_turn_submit_side_effects_phase_keeps_optional_fields`.

### [WL-11028]

**Title:** Preserve side-effects target typing guardrails
**Source:** `tests/protocols/test_wl11020_wl11029_lane_c10b.py`
**Acceptance checklist:**

- [x] Raise when `turn_id` is not a string in side-effects target resolution.
      **Notes:** Covered by `test_wl11028_build_turn_submit_side_effects_target_rejects_bad_turn_id`.

### [WL-11029]

**Title:** Preserve response approval fields for missing optional diff
**Source:** `tests/protocols/test_wl11020_wl11029_lane_c10b.py`
**Acceptance checklist:**

- [x] Resolve approval tuple with `diff=None` when absent.
      **Notes:** Covered by `test_wl11029_resolve_turn_submit_response_approval_fields_allows_empty_diff`.
