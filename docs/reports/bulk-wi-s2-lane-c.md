### [WL-5210] Leak Detection Test Infrastructure Spec (psleak+tracemalloc+fdleaky)

**Status:** OPEN
**Priority:** P1
**Area:** runtime,qa
**Effort:** S
**Blocked by:** WL-5208
**Source:** [thegent/docs/reference/WORK_STREAM.md:23010]
Define leak-class coverage ownership across `psleak`, `tracemalloc`, and `fdleaky`; codify pytest fixture contracts, `CHECK_LEAKS=1` gating, and CI thresholds.

### [WL-5211] psutil Adoption Plan: Scope Boundary and Cross-Platform Parity

**Status:** OPEN
**Priority:** P1
**Area:** runtime
**Effort:** S
**Blocked by:** none
**Source:** [thegent/docs/reference/WORK_STREAM.md:23020]
Publish an ADR that sets `psutil` scope versus custom monitoring, resolves Windows parity behavior, and defines dependency classification.

### [WL-5212] Non-Canonical File Consolidation Execution Plan

**Status:** OPEN
**Priority:** P2
**Area:** infra
**Effort:** S
**Blocked by:** none
**Source:** [thegent/docs/reference/WORK_STREAM.md:23030]
Produce a sequenced consolidation runbook with dependency ordering, parity checks before deletion, and final broken-reference scanning criteria.

### [WL-5213] Cross-Platform Secret Storage Design Document

**Status:** OPEN
**Priority:** P2
**Area:** infra
**Effort:** S
**Blocked by:** WL-5207
**Source:** [thegent/docs/reference/WORK_STREAM.md:23040]
Design the secure storage strategy per platform, define fail-loud behavior when keystores are unavailable, and plan migration from `~/.thegent`.

### [WL-5214] LOC Trend History Dashboard and Week-over-Week Delta Reporting

**Status:** OPEN
**Priority:** P2
**Area:** metrics,reporting
**Effort:** S
**Blocked by:** none
**Source:** [thegent/docs/reference/WORK_STREAM.md:23050]
Add a rolling 4-week LOC delta dashboard per language and top file, and attach it to each weekly WL-137 report output.

### [WL-5215] WL-137 Alert Auto-Dispatch to WORK_STREAM on Threshold Breach

**Status:** OPEN
**Priority:** P2
**Area:** quality,reporting
**Effort:** S
**Blocked by:** none
**Source:** [thegent/docs/reference/WORK_STREAM.md:23060]
Implement automation that appends a templated OPEN item to `WORK_STREAM.md` whenever WL-137 weekly checks breach configured thresholds.

### [WL-5216] Weekly LOC Diagnosis Scheduling and Cadence Enforcement

**Status:** OPEN
**Priority:** P2
**Area:** quality,dx
**Effort:** S
**Blocked by:** none
**Source:** [thegent/docs/reference/WORK_STREAM.md:23070]
Register and enforce a weekly scheduler so `task diag:wl137` runs on cadence with visible execution evidence.

### [WL-5217] Stale Completion Report Archive Plan and Execution Checklist

**Status:** OPEN
**Priority:** P3
**Area:** docs
**Effort:** S
**Blocked by:** none
**Source:** [thegent/docs/reference/WORK_STREAM.md:23080]
Create an archive checklist for stale completion reports, define destination structure, and verify no active work items reference archived files.

### [WL-5218] WBS Phase Completion Dashboard: Phases 2, 4, 5, 6 Progress Tracker

**Status:** OPEN
**Priority:** P1
**Area:** reporting,metrics
**Effort:** M
**Blocked by:** none
**Source:** [thegent/docs/reference/WORK_STREAM.md:23090]
Add a phase-progress dashboard in `PLAN_STATUS.md` with per-phase item counts, completion percentages, and weekly refresh criteria.

### [WL-5219] Serena Memory Files Governance Policy and Promotion Checklist

**Status:** OPEN
**Priority:** P2
**Area:** governance,docs
**Effort:** S
**Blocked by:** none
**Source:** [thegent/docs/reference/WORK_STREAM.md:23100]
Document memory lifecycle governance, including creation standards, promotion to `docs/plans/`, reference rules, and retirement criteria.
