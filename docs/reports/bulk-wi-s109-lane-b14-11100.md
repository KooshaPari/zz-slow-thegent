### [WL-11100]

**Title:** Preserve turn/submit phase-plan rejection for non-string input payloads.
**Source:** `tests/protocols/test_wl11100_wl11109_lane_b14.py`
**Acceptance checklist:**

- [x] Return invalid params parse error when `input` is not a string.

### [WL-11101]

**Title:** Preserve turn/submit phase-plan rejection for non-boolean approval flag.
**Source:** `tests/protocols/test_wl11100_wl11109_lane_b14.py`
**Acceptance checklist:**

- [x] Return invalid params parse error when `requires_approval` is not a boolean.

### [WL-11102]

**Title:** Preserve required-diff validation when approval mode is enabled.
**Source:** `tests/protocols/test_wl11100_wl11109_lane_b14.py`
**Acceptance checklist:**

- [x] Return invalid params parse error when `requires_approval=true` and diff is missing.

### [WL-11103]

**Title:** Preserve turn/submit parse-failure passthrough behavior.
**Source:** `tests/protocols/test_wl11100_wl11109_lane_b14.py`
**Acceptance checklist:**

- [x] Return parse failure response and emit no notifications when parse fails.

### [WL-11104]

**Title:** Preserve notification-path turn/submit commit and event emission.
**Source:** `tests/protocols/test_wl11100_wl11109_lane_b14.py`
**Acceptance checklist:**

- [x] For notification path, commit turn, keep completed terminal state, and emit started/execution/completed events.

### [WL-11105]

**Title:** Preserve response-path turn/submit approval payload projection.
**Source:** `tests/protocols/test_wl11100_wl11109_lane_b14.py`
**Acceptance checklist:**

- [x] For approval-required path, return result response including approval payload and awaiting-approval turn state.

### [WL-11106]

**Title:** Preserve non-approval side-effects completion flow.
**Source:** `tests/protocols/test_wl11100_wl11109_lane_b14.py`
**Acceptance checklist:**

- [x] Non-approval side-effects return `None`, mark turn completed, and assign tool-call id.

### [WL-11107]

**Title:** Preserve approval side-effects flow and payload creation.
**Source:** `tests/protocols/test_wl11100_wl11109_lane_b14.py`
**Acceptance checklist:**

- [x] Approval side-effects return approval payload and mark turn awaiting approval.

### [WL-11108]

**Title:** Preserve turn execution-plan initialization defaults.
**Source:** `tests/protocols/test_wl11100_wl11109_lane_b14.py`
**Acceptance checklist:**

- [x] Execution plan creates in-progress turn with null approval/tool-call IDs.

### [WL-11109]

**Title:** Preserve commit-phase persistence contract for turns.
**Source:** `tests/protocols/test_wl11100_wl11109_lane_b14.py`
**Acceptance checklist:**

- [x] Commit phase stores turn and appends turn id to session ordering.
