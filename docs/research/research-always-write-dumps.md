<DONE>
# Always Write Conversation Dumps - Implementation Status

> **WORK_STREAM ID:** research-always-write-dumps
> **Priority:** P2
> **Status:** ✅ Complete

## Summary

This work item ensures that conversation dumps are always written to `docs/research/CONVERSATION_DUMP_YYYY-MM-DD.md` when completing significant work.

## Implementation Status

### ✅ Policy Documented in CLAUDE.md

The conversation dump policy is documented in two locations in `CLAUDE.md`:

1. **Section: Conversation Dumps (Always Write)** (lines 57-65):
   - Mandates writing dumps for significant work
   - Specifies format: `docs/research/CONVERSATION_DUMP_YYYY-MM-DD.md`
   - Includes key decisions, findings, rationale, and handoff notes

2. **Section: Conversation Dump Policy (Always Write Down)** (lines 359-375):
   - Detailed format specification
   - Sections: Issues Addressed, Fixes Applied, Research Findings, Plans, Open Questions
   - References template: `docs/research/CONVERSATION_DUMP_2026-02-16.md`

### ✅ Template Available

Template document exists at:

- `docs/research/CONVERSATION_DUMP_2026-02-16.md`

### ✅ Expanded Guide Available

Comprehensive guide exists at:

- `docs/research/CONVERSATION_DUMP_2026-02-16_EXPANDED.md`

## Usage

Agents should write conversation dumps when:

- Completing research work
- Making design decisions
- Implementing multi-file changes
- Making decisions that affect the project

**Format**: `docs/research/CONVERSATION_DUMP_YYYY-MM-DD.md`

**Sections**:

- Issues Addressed
- Fixes Applied
- Research Findings
- Plans
- Open Questions
- Cursor-Agent Recovery Note (if applicable)

## Acceptance Criteria

- [x] Policy documented in CLAUDE.md
- [x] Template document available
- [x] Expanded guide available
- [x] Format specification clear
- [x] Usage guidelines provided

## References

- [CLAUDE.md](../../CLAUDE.md) - Main policy document
- [CONVERSATION_DUMP_2026-02-16.md](./CONVERSATION_DUMP_2026-02-16.md) - Template
- [CONVERSATION_DUMP_2026-02-16_EXPANDED.md](./CONVERSATION_DUMP_2026-02-16_EXPANDED.md) - Expanded guide
- [WORK_STREAM.md](../reference/WORK_STREAM.md)
