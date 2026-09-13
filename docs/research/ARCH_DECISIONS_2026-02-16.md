<DONE>
## Decision Change Log Template
- Record every accepted ADR update as one entry in this document immediately after merge.
- Include: decision ID (for example `ADR-015`), change date (`YYYY-MM-DD`), author, and approval owner.
- Summarize the delta in 1-2 lines: what changed, why now, and what prior ADR text was superseded.
- Link the authoritative ADR file under `thegent/docs/research/` and the implementation PR/commit.
- Note rollout impact explicitly: affected components, migration required (`yes/no`), and validation evidence location.

## Decision Acceptance Checklist

- ADR file is complete and uses final status language (`Accepted`), with alternatives and trade-offs documented.
- Impact is testable: success criteria, verification command(s), and observability signal are defined before approval.
- Backward-compatibility stance is explicit (breaking/non-breaking) and matches current no-fallback policy.
- Ownership is assigned for implementation and post-release verification, with a target review date set.
- Change log entry is added in this file in the same PR that accepts or amends the ADR.
