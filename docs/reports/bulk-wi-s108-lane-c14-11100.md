### [WL-11100]

**Title:** Preserve notification response-path acceptance for null `request_id`.
**Source:** `tests/protocols/test_wl11100_wl11109_lane_c14.py`
**Acceptance checklist:**

- [x] Return `None` when `request_has_id=False` and response phase carries `request_id=None`.

### [WL-11101]

**Title:** Preserve strict rejection for request response-path null `request_id`.
**Source:** `tests/protocols/test_wl11100_wl11109_lane_c14.py`
**Acceptance checklist:**

- [x] Raise response-target unresolved error when `request_has_id=True` and `request_id` is `None`.

### [WL-11102]

**Title:** Preserve strict request-id validation for non-scalar request response-path IDs.
**Source:** `tests/protocols/test_wl11100_wl11109_lane_c14.py`
**Acceptance checklist:**

- [x] Raise response-target unresolved error when `request_has_id=True` and `request_id` is invalid JSON-RPC id type.

### [WL-11103]

**Title:** Preserve null response approval-id projection when approval payload is absent.
**Source:** `tests/protocols/test_wl11100_wl11109_lane_c14.py`
**Acceptance checklist:**

- [x] Return `None` from response approval-id extractor when payload is `None`.

### [WL-11104]

**Title:** Preserve null response approval-status projection when approval payload is absent.
**Source:** `tests/protocols/test_wl11100_wl11109_lane_c14.py`
**Acceptance checklist:**

- [x] Return `None` from response approval-status extractor when payload is `None`.

### [WL-11105]

**Title:** Preserve null response approval-diff projection when approval payload is absent.
**Source:** `tests/protocols/test_wl11100_wl11109_lane_c14.py`
**Acceptance checklist:**

- [x] Return `None` from response approval-diff extractor when payload is `None`.

### [WL-11106]

**Title:** Preserve full approval-fields tuple projection for valid response approval payload.
**Source:** `tests/protocols/test_wl11100_wl11109_lane_c14.py`
**Acceptance checklist:**

- [x] Return `(id, status, diff)` tuple unchanged when approval payload values are valid.

### [WL-11107]

**Title:** Preserve response target tuple resolution when approval payload is omitted.
**Source:** `tests/protocols/test_wl11100_wl11109_lane_c14.py`
**Acceptance checklist:**

- [x] Return stable tuple with `approval_payload=None` for valid response-phase values.

### [WL-11108]

**Title:** Preserve strict rejection for invalid approval payload identity during response target resolution.
**Source:** `tests/protocols/test_wl11100_wl11109_lane_c14.py`
**Acceptance checklist:**

- [x] Raise response-target unresolved error when response approval payload `id` is empty.

### [WL-11109]

**Title:** Preserve strict request-id enforcement in response resolution phase.
**Source:** `tests/protocols/test_wl11100_wl11109_lane_c14.py`
**Acceptance checklist:**

- [x] Raise response-target unresolved error when resolution phase has `request_has_id=True` with invalid `request_id`.
