### [WL-5790] governance_fs line 127 backlog marker

**Status:** COMPLETED
**Priority:** P2
**Area:** backlog,bulk
**Effort:** S
**Blocked by:** none
**Source:** [thegent/docs/reports/bulk-wi-b1-lane-f.md:496]
Implemented explicit directory traversal errors in TODO scanning (`count_todos`) with fail-fast IO handling.
**Evidence:** `cd hooks/hook-dispatcher && cargo test -q count_todos` (4 passed).

### [WL-5791] governance_fs line 137 backlog marker

**Status:** COMPLETED
**Priority:** P2
**Area:** backlog,bulk
**Effort:** S
**Blocked by:** none
**Source:** [thegent/docs/reports/bulk-wi-b1-lane-f.md:505]
Implemented explicit propagation for recursive TODO scan descent and IO failures (`count_todos`) instead of silent skipping.
**Evidence:** `cd hooks/hook-dispatcher && cargo test -q count_todos` (4 passed).

### [WL-5792] governance_fs line 142 backlog marker

**Status:** COMPLETED
**Priority:** P2
**Area:** backlog,bulk
**Effort:** S
**Blocked by:** none
**Source:** [thegent/docs/reports/bulk-wi-b1-lane-f.md:514]
Implemented explicit TODO/FIXME file-read path with `?` semantics and concrete failure propagation.
**Evidence:** `cd hooks/hook-dispatcher && cargo test -q count_todos::tests::count_todos_is_empty_for_unsupported_extensions` (1 passed).

### [WL-5793] governance_fs line 143 backlog marker

**Status:** COMPLETED
**Priority:** P2
**Area:** backlog,bulk
**Effort:** S
**Blocked by:** none
**Source:** [thegent/docs/reports/bulk-wi-b1-lane-f.md:523]
Implemented regex-based token counting (`\\b(TODO|FIXME)\\b`) to avoid placeholder-style substring false positives.
**Evidence:** `cd hooks/hook-dispatcher && cargo test -q count_todos::tests::count_todos_ignores_markers_without_boundaries` (1 passed).

### [WL-5794] main line 23 backlog marker

**Status:** COMPLETED
**Priority:** P2
**Area:** backlog,bulk
**Effort:** S
**Blocked by:** none
**Source:** [thegent/docs/reports/bulk-wi-b1-lane-f.md:532]
`run_governance_scan` now handles TODO scan failures explicitly and exits governance non-zero when TODO scanning fails.
**Evidence:** `cd hooks/hook-dispatcher && cargo test -q` (4 passed, including module integration that exercises error paths).

### [WL-5795] main line 650 backlog marker

**Status:** OPEN
**Priority:** P2
**Area:** backlog,bulk
**Effort:** S
**Blocked by:** none
**Source:** [thegent/docs/reports/bulk-wi-b1-lane-f.md:541]
Implement concrete logic here and remove the stub/placeholder signal with focused coverage.

### [WL-5796] batch line 14 backlog marker

**Status:** OPEN
**Priority:** P2
**Area:** backlog,bulk
**Effort:** S
**Blocked by:** none
**Source:** [thegent/docs/reports/bulk-wi-b1-lane-f.md:55]
Implement concrete logic here and remove the stub/placeholder signal with focused coverage.

### [WL-5797] main line 653 backlog marker

**Status:** OPEN
**Priority:** P2
**Area:** backlog,bulk
**Effort:** S
**Blocked by:** none
**Source:** [thegent/docs/reports/bulk-wi-b1-lane-f.md:550]
Implement concrete logic here and remove the stub/placeholder signal with focused coverage.

### [WL-5798] main line 700 backlog marker

**Status:** OPEN
**Priority:** P2
**Area:** backlog,bulk
**Effort:** S
**Blocked by:** none
**Source:** [thegent/docs/reports/bulk-wi-b1-lane-f.md:559]
Implement concrete logic here and remove the stub/placeholder signal with focused coverage.

### [WL-5799] main line 701 backlog marker

**Status:** OPEN
**Priority:** P2
**Area:** backlog,bulk
**Effort:** S
**Blocked by:** none
**Source:** [thegent/docs/reports/bulk-wi-b1-lane-f.md:568]
Implement concrete logic here and remove the stub/placeholder signal with focused coverage.
