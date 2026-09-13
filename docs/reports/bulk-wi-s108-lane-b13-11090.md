### [WL-11090]

**Title:** Preserve parse-error normalization for non-dict turn/submit parse errors.
**Source:** `tests/protocols/test_wl11090_wl11099_lane_b13.py`
**Acceptance checklist:**

- [x] Return `None` when parse-error payload is not a dict.

### [WL-11091]

**Title:** Preserve turn/submit parse-phase field projection from the phase plan.
**Source:** `tests/protocols/test_wl11090_wl11099_lane_b13.py`
**Acceptance checklist:**

- [x] Carry `session_id`, `session`, `user_input`, `requires_approval`, and `approval_diff` through parse-phase construction.

### [WL-11092]

**Title:** Preserve successful execution-target tuple resolution for valid turn/submit parse phase.
**Source:** `tests/protocols/test_wl11090_wl11099_lane_b13.py`
**Acceptance checklist:**

- [x] Resolve `(session_id, session, user_input, requires_approval, approval_diff)` for valid payloads.

### [WL-11093]

**Title:** Preserve strict type validation for turn/submit execution-target `requires_approval`.
**Source:** `tests/protocols/test_wl11090_wl11099_lane_b13.py`
**Acceptance checklist:**

- [x] Reject non-boolean `requires_approval` during execution-target resolution.

### [WL-11094]

**Title:** Preserve successful commit-target tuple resolution for valid turn/submit commit phase.
**Source:** `tests/protocols/test_wl11090_wl11099_lane_b13.py`
**Acceptance checklist:**

- [x] Resolve `(turn_id, turn, session)` when commit payload shape is valid.

### [WL-11095]

**Title:** Preserve strict commit-target validation for malformed session payloads.
**Source:** `tests/protocols/test_wl11090_wl11099_lane_b13.py`
**Acceptance checklist:**

- [x] Reject non-dict `session` values during commit-target resolution.

### [WL-11096]

**Title:** Preserve successful side-effects target tuple resolution for valid turn/submit side-effects phase.
**Source:** `tests/protocols/test_wl11090_wl11099_lane_b13.py`
**Acceptance checklist:**

- [x] Resolve all side-effects tuple fields for valid phase payloads.

### [WL-11097]

**Title:** Preserve strict side-effects target validation for malformed approval diff payloads.
**Source:** `tests/protocols/test_wl11090_wl11099_lane_b13.py`
**Acceptance checklist:**

- [x] Reject non-string/non-null `approval_diff` values during side-effects target resolution.

### [WL-11098]

**Title:** Preserve strict turn/submit approval payload resolution when approval diff is unresolved.
**Source:** `tests/protocols/test_wl11090_wl11099_lane_b13.py`
**Acceptance checklist:**

- [x] Raise a hard error when approval payload resolution receives a non-string diff.

### [WL-11099]

**Title:** Preserve turn/submit result payload shape by omitting approval when absent.
**Source:** `tests/protocols/test_wl11090_wl11099_lane_b13.py`
**Acceptance checklist:**

- [x] Build result payload with serialized turn and no `approval` field when approval payload is absent.
