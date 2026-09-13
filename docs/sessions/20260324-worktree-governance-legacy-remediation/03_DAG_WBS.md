# 03_DAG_WBS

## Phase 1: Discovery

- P1.1 Generate remediation report
- P1.2 Identify clean legacy lanes for migration

## Phase 2: Migration

- P2.1 Migrate clean legacy worktrees into canonical root
- P2.2 Refresh governance inventory and remediation counts

## Phase 3: Validation

- P3.1 Run strict governance checks
- P3.2 Verify migration does not alter behavior

## Dependencies

- P1.2 depends on P1.1
- P2.1 depends on P1.2
- P2.2 depends on P2.1
- P3.1 depends on P2.2
- P3.2 depends on P2.1
