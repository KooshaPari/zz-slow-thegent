### [WL-10970]

Source: `tests/protocols/test_wl10970_wl10979_lane_b5.py` (`test_wl10970_resolve_turn_submit_parse_error_strips_non_dict_error`)

**Status**: Added regression test for `_resolve_turn_submit_parse_error` pass-through and non-dict rejection.

### [WL-10971]

Source: `tests/protocols/test_wl10970_wl10979_lane_b5.py` (`test_wl10971_build_turn_submit_commit_phase_carries_session_and_input`)

**Status**: Added regression for `_build_turn_submit_commit_phase` to preserve session reference.

### [WL-10972]

Source: `tests/protocols/test_wl10970_wl10979_lane_b5.py` (`test_wl10972_resolve_turn_submit_commit_target_returns_tuple_fields`)

**Status**: Added tuple-resolution regression for `_resolve_turn_submit_commit_target`.

### [WL-10973]

Source: `tests/protocols/test_wl10970_wl10979_lane_b5.py` (`test_wl10973_resolve_turn_submit_commit_target_rejects_invalid_shape`)

**Status**: Added strict-shape failure regression for `_resolve_turn_submit_commit_target`.

### [WL-10974]

Source: `tests/protocols/test_wl10970_wl10979_lane_b5.py` (`test_wl10974_commit_turn_submit_plan_mutates_session_and_turns`)

**Status**: Added mutation regression proving `_commit_turn_submit_plan` persists turn and session linkage.

### [WL-10975]

Source: `tests/protocols/test_wl10970_wl10979_lane_b5.py` (`test_wl10975_handle_turn_submit_parse_failure_bubbles_error_payload`)

**Status**: Added regression that parse failure helper returns raw parse payload unchanged.

### [WL-10976]

Source: `tests/protocols/test_wl10970_wl10979_lane_b5.py` (`test_wl10976_handle_turn_submit_request_rejects_non_string_input`)

**Status**: Added invalid-input regression for `turn/submit` request path and payload error contract.

### [WL-10977]

Source: `tests/protocols/test_wl10970_wl10979_lane_b5.py` (`test_wl10977_resolve_turn_submit_approval_fields_extracts_tuple`)

**Status**: Added contract regression for `_resolve_turn_submit_response_approval_fields` extraction.

### [WL-10978]

Source: `tests/protocols/test_wl10970_wl10979_lane_b5.py` (`test_wl10978_resolve_turn_submit_response_approval_fields_allows_missing_diff`)

**Status**: Added regression proving optional approval diff remains nullable in extracted tuple.

### [WL-10979]

Source: `tests/protocols/test_wl10970_wl10979_lane_b5.py` (`test_wl10979_build_turn_submit_side_effects_resolution_phase_preserves_inputs`)

**Status**: Added return-shape regression for `_build_turn_submit_side_effects_resolution_phase`.
