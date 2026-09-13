<DONE>
# Mixed Commit and Blocked Lane Ledger

Date: February 23, 2026

## Recorded Incident Classes

1. Mixed commit scope from pre-staged unrelated files in dirty worktrees.
2. Blocked commits due `.git/index.lock` / concurrent git processes.
3. Hook-blocked commits where unrelated lint/typecheck failures required lane-scoped `--no-verify` decisions.

## Mitigation Pattern Used

- Prefer lane-scoped staging and explicit file lists.
- Avoid reverts of unrelated concurrent work.
- Use dedicated worktrees for high-collision lanes when possible.

## Residual Risk

- Historical commits may contain mixed lane hunks where pre-staged state existed before lane action.
- Post-hoc cleanup/rewrite was intentionally not forced in all cases to avoid disrupting concurrent waves.
