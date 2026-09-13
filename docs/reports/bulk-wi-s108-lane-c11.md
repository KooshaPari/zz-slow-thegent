### [WL-11030]

**Title:** Preserve turn/submit result payload without approval field when absent.
**Source:** `tests/protocols/test_wl11030_wl11039_lane_c11.py`
**Acceptance checklist:**

- [x] Return `{"turn": ...}` when no approval payload is present.

### [WL-11031]

**Title:** Preserve turn/submit result payload with approval field when present.
**Source:** `tests/protocols/test_wl11030_wl11039_lane_c11.py`
**Acceptance checklist:**

- [x] Include `approval` key only when payload is provided.

### [WL-11032]

**Title:** Preserve response-resolution tuple extraction for valid payloads.
**Source:** `tests/protocols/test_wl11030_wl11039_lane_c11.py`
**Acceptance checklist:**

- [x] Return request-id/turn/approval payload tuple from built response phase.

### [WL-11033]

**Title:** Preserve optional approval fields as all-none when approval is absent.
**Source:** `tests/protocols/test_wl11030_wl11039_lane_c11.py`
**Acceptance checklist:**

- [x] Resolve approval tuple as `(None, None, None)` when no payload exists.

### [WL-11034]

**Title:** Preserve strict parse behavior for missing response turn.
**Source:** `tests/protocols/test_wl11030_wl11039_lane_c11.py`
**Acceptance checklist:**

- [x] Reject response resolution when `turn` is missing from response phase.

### [WL-11035]

**Title:** Preserve request-id type gate for required id in response resolution.
**Source:** `tests/protocols/test_wl11030_wl11039_lane_c11.py`
**Acceptance checklist:**

- [x] Reject dict request ids when a response id is required.

### [WL-11036]

**Title:** Preserve approval diff passthrough with explicit null.
**Source:** `tests/protocols/test_wl11030_wl11039_lane_c11.py`
**Acceptance checklist:**

- [x] Keep approval diff as `None` when passed explicitly.

### [WL-11037]

**Title:** Preserve type validation for non-string approval diff.
**Source:** `tests/protocols/test_wl11030_wl11039_lane_c11.py`
**Acceptance checklist:**

- [x] Reject approval payload diff values that are not strings or `None`.

### [WL-11038]

**Title:** Preserve numeric request-id handling in success response.
**Source:** `tests/protocols/test_wl11030_wl11039_lane_c11.py`
**Acceptance checklist:**

- [x] Return response id as provided integer request id.

### [WL-11039]

**Title:** Preserve bool-as-request-id rejection on required response id path.
**Source:** `tests/protocols/test_wl11030_wl11039_lane_c11.py`
**Acceptance checklist:**

- [x] Reject boolean request ids in response target resolution when response requires an id.
