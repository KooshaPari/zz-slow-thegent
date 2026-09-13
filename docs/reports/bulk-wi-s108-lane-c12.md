### [WL-11070]

**Title:** Preserve null-safe approval id extraction for missing response approval payload.
**Source:** `tests/protocols/test_wl11070_wl11079_lane_c12.py`
**Acceptance checklist:**

- [x] Return `None` for approval id when response approval payload is absent.

### [WL-11071]

**Title:** Preserve null-safe approval status extraction for missing response approval payload.
**Source:** `tests/protocols/test_wl11070_wl11079_lane_c12.py`
**Acceptance checklist:**

- [x] Return `None` for approval status when response approval payload is absent.

### [WL-11072]

**Title:** Preserve null-safe approval diff extraction for missing response approval payload.
**Source:** `tests/protocols/test_wl11070_wl11079_lane_c12.py`
**Acceptance checklist:**

- [x] Return `None` for approval diff when response approval payload is absent.

### [WL-11073]

**Title:** Preserve all-none approval tuple resolution when response approval payload is absent.
**Source:** `tests/protocols/test_wl11070_wl11079_lane_c12.py`
**Acceptance checklist:**

- [x] Resolve approval tuple as `(None, None, None)` without raising.

### [WL-11074]

**Title:** Preserve string request-id extraction on required response-id path.
**Source:** `tests/protocols/test_wl11070_wl11079_lane_c12.py`
**Acceptance checklist:**

- [x] Return string request id unchanged when response id is required.

### [WL-11075]

**Title:** Preserve integer request-id extraction on required response-id path.
**Source:** `tests/protocols/test_wl11070_wl11079_lane_c12.py`
**Acceptance checklist:**

- [x] Return integer request id unchanged when response id is required.

### [WL-11076]

**Title:** Preserve response emission gate behavior for notification-style turn/submit requests.
**Source:** `tests/protocols/test_wl11070_wl11079_lane_c12.py`
**Acceptance checklist:**

- [x] Return `None` success response when `request_has_id=False`.

### [WL-11077]

**Title:** Preserve strict rejection when response phase omits request-has-id marker.
**Source:** `tests/protocols/test_wl11070_wl11079_lane_c12.py`
**Acceptance checklist:**

- [x] Raise response target unresolved when `request_has_id` is missing.

### [WL-11078]

**Title:** Preserve strict rejection when response resolution phase omits turn payload.
**Source:** `tests/protocols/test_wl11070_wl11079_lane_c12.py`
**Acceptance checklist:**

- [x] Raise response target unresolved when `turn` is missing from response phase.

### [WL-11079]

**Title:** Preserve response-phase field completeness for downstream resolution helpers.
**Source:** `tests/protocols/test_wl11070_wl11079_lane_c12.py`
**Acceptance checklist:**

- [x] Build response phase with stable keys: request marker, request id, turn, and approval payload.
