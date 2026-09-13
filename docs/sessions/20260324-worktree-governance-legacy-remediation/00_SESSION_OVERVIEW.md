# 00_SESSION_OVERVIEW

## Goal

Harden worktree governance with a documented legacy remediation workflow, preserve canonical commands, and keep migration decisions explicit and auditable.

## Scope

- Worktree governance commands and reports
- Legacy worktree remediation guidance
- Session-level documentation of decisions and current counts

## Key Decisions

- Legacy worktrees are reported via `task quality:governance:legacy-remediation-report` and must be migrated with `thegent worktree migrate-legacy` before strict governance can pass.
- Migration only applies to clean, non-detached legacy lanes; dirty or detached lanes are blocked until cleaned.

## Current Counts (from remediation report)

- total legacy worktrees: `25`
- dirty legacy worktrees: `25`
- prunable legacy worktrees: `0`

## Latest Blocker

- The detached legacy lane `lane-split-modules-bootstrap-v2` previously had a real
  `DU src/thegent/native/git_native.py` delete/modify conflict, and that specific conflict is now
  resolved.
- The lane is still not migratable because it remains detached, dirty, and outside the canonical
  `/.worktrees` root.

## Canonical Commands

- Report: `task quality:governance:legacy-remediation-report`
- Script: `scripts/worktree_governance.sh migrate-legacy <legacy-path> <domain> <scale> <change-anchor> [state]`
- Migrate: `thegent worktree migrate-legacy <legacy-path> <domain> <scale> <change-anchor> [state]`
- Refresh: `thegent worktree refresh <change-anchor> --ref origin/canary --strategy rebase`

## References

- `docs/governance/UNIFIED_WORKTREE_WORKFLOW_GOVERNANCE.md`
- `docs/governance/WORKTREE_AND_DELEGATION_INDEX.md`
- `docs/governance/GOVERNANCE_SUMMARY.md`
