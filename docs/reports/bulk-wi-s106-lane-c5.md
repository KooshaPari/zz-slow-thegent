### [WL-10970]

**Title:** Preserve parse-error extraction path for non-dict turn submit parse payloads
**Source:** `tests/protocols/test_wl10970_wl10979_lane_c5.py`
**Acceptance checklist:**

- [x] Reject parse errors with non-dict `parse_error` by returning `None`.
- [x] Preserve parse-error reason pass-through for dict payloads.
- [x] Add focused regression coverage.
      **Notes:** Covered by `test_wl10970_*`.

### [WL-10971]

**Title:** Preserve commit-phase structure as direct session/input tuple projection
**Source:** `tests/protocols/test_wl10970_wl10979_lane_c5.py`
**Acceptance checklist:**

- [x] Extract turn submit commit-phase with session and input in one pass.
- [x] Preserve object identity for session payload.
- [x] Add focused regression coverage.
      **Notes:** Covered by `test_wl10971_*`.

### [WL-10972]

**Title:** Preserve typed commit target extraction for turn/submit execution
**Source:** `tests/protocols/test_wl10970_wl10979_lane_c5.py`
**Acceptance checklist:**

- [x] Resolve tuple fields from commit plan.
- [x] Preserve exact tuple contract (`turn_id`, `turn`, `session`).
- [x] Add focused regression coverage.
      **Notes:** Covered by `test_wl10972_*`.

### [WL-10973]

**Title:** Preserve fail-fast behavior for malformed commit target payloads
**Source:** `tests/protocols/test_wl10970_wl10979_lane_c5.py`
**Acceptance checklist:**

- [x] Raise ValueError for malformed commit payload shape.
- [x] Keep unresolved error semantics on invalid values.
- [x] Add focused regression coverage.
      **Notes:** Covered by `test_wl10973_*`.

### [WL-10974]

**Title:** Preserve commit-plan side effects against in-memory session store
**Source:** `tests/protocols/test_wl10970_wl10979_lane_c5.py`
**Acceptance checklist:**

- [x] Mutate session turn list during commit.
- [x] Store turn record in state registry.
- [x] Add focused regression coverage.
      **Notes:** Covered by `test_wl10974_*`.

### [WL-10975]

**Title:** Preserve parse-failure passthrough from turn/submit parser
**Source:** `tests/protocols/test_wl10970_wl10979_lane_c5.py`
**Acceptance checklist:**

- [x] Bubble parse failures using original error payload.
- [x] Preserve parse payload shape.
- [x] Add focused regression coverage.
      **Notes:** Covered by `test_wl10975_*`.

### [WL-10976]

**Title:** Preserve non-string input validation for turn/submit
**Source:** `tests/protocols/test_wl10970_wl10979_lane_c5.py`
**Acceptance checklist:**

- [x] Reject non-string turn input with -32602.
- [x] Preserve reason code/message in error payload.
- [x] Add focused regression coverage.
      **Notes:** Covered by `test_wl10976_*`.

### [WL-10977]

**Title:** Preserve approval tuple extraction for response projection
**Source:** `tests/protocols/test_wl10970_wl10979_lane_c5.py`
**Acceptance checklist:**

- [x] Resolve approval payload into `(id, status, diff)`.
- [x] Keep string diff when provided.
- [x] Add focused regression coverage.
      **Notes:** Covered by `test_wl10977_*`.

### [WL-10978]

**Title:** Preserve optional diff behavior in approval tuple extraction
**Source:** `tests/protocols/test_wl10970_wl10979_lane_c5.py`
**Acceptance checklist:**

- [x] Resolve approval tuple with missing diff as `None`.
- [x] Preserve id/status extraction.
- [x] Add focused regression coverage.
      **Notes:** Covered by `test_wl10978_*`.

### [WL-10979]

**Title:** Preserve side-effect-phase tuple projection for response wiring
**Source:** `tests/protocols/test_wl10970_wl10979_lane_c5.py`
**Acceptance checklist:**

- [x] Build side-effects phase with exact scalar payload projection.
- [x] Resolve phase into complete positional tuple.
- [x] Add focused regression coverage.
      **Notes:** Covered by `test_wl10979_*`.
