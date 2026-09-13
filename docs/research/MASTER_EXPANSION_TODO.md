<DONE>
# Master Expansion TODO — Complete Documentation Sprawl

> **Status**: Active | **Version**: 2.0 | **Date**: 2026-02-17
> **Purpose**: Comprehensive todo list for expanding all fragmented/seed/research docs into complete, optimized, production-ready documentation

---

## Expansion Criteria

Each doc must be expanded to meet:

- ✅ **Optimize**: Remove redundancy; performance targets; link to libs/crates
- ✅ **Robustify**: Failure modes, error handling, retry/fallback, validation
- ✅ **Practical + Intuitive**: Actionable tasks, clear acceptance criteria, discoverable structure
- ✅ **Holistic + Harmonious**: Cross-links, consistent with WORK_STREAM/WBS, no orphan decisions
- ✅ **Maximal/Optimal Engineering**: End-to-end flow, observable, recoverable, cost-conscious

---

## Priority 0: Critical Fragments (In Progress)

### ✅ SESSION_RESEARCH_FRAGMENTS.md

**Status**: ✅ Expanded
**Output**: [SESSION_RESEARCH_FRAGMENTS_EXPANDED.md](./SESSION_RESEARCH_FRAGMENTS_EXPANDED.md)
**Work Items**: 5 BACKLOG items added

### ✅ CONVERSATION_DUMP_2026-02-16.md

**Status**: ✅ Expanded
**Output**: [CONVERSATION_DUMP_2026-02-16_EXPANDED.md](./CONVERSATION_DUMP_2026-02-16_EXPANDED.md)
**Work Items**: 4 BACKLOG items extracted

### ✅ idea-seeds/\*.md (4 files)

**Status**: ✅ Expanded
**Output**: [IDEA_SEED_EXPANSION_COMPLETE.md](./idea-seeds/IDEA_SEED_EXPANSION_COMPLETE.md)
**Work Items**: 1 BACKLOG item (3 duplicates merged)

---

## Priority 1: High-Value Expansions

### 1. CROSS_PLATFORM Research Consolidation

**Files**:

- `CROSS_PLATFORM_GAPS_AND_EXTENSIONS_RESEARCH.md` (333 lines)
- `CROSS_PLATFORM_EXTENSIONS_WIDER_DEEPER_OPTIMIZATION.md`
- `CROSS_PLATFORM_RESEARCH_SUMMARY.md`
- `CROSS_PLATFORM_RESEARCH_INDEX.md` (353 lines)
- `CROSS_PLATFORM_RESEARCH_COMPLETION_SUMMARY.md` (458 lines)

**TODO**:

- [ ] Consolidate into single comprehensive guide
- [ ] Expand each platform (macOS, Linux, Windows, WSL) with deep dives
- [ ] Add implementation patterns, code examples
- [ ] Add testing strategies per platform
- [ ] Add performance benchmarks per platform
- [ ] Add troubleshooting guides per platform
- [ ] Cross-reference with implementation plans
- [ ] Create platform-specific quick start guides

**Target**: `docs/research/CROSS_PLATFORM_RESEARCH_COMPLETE.md` + platform guides

### 2. HOOK_RUST_MIGRATION_RESEARCH_SYNTHESIS.md

**Status**: Synthesis, needs expansion
**TODO**:

- [ ] Expand migration strategy with detailed steps
- [ ] Add performance comparison (shell vs Rust)
- [ ] Add migration timeline with milestones
- [ ] Add rollback strategies
- [ ] Add testing requirements
- [ ] Add code examples for each hook
- [ ] Cross-reference with implementation plan
- [ ] Add risk mitigation strategies

**Target**: `docs/research/HOOK_RUST_MIGRATION_COMPLETE.md`

### 3. LIBRARY_REPLACEMENT Research Consolidation

**Files**:

- `LIBRARY_FIRST_AUDIT_AND_PLAN.md`
- `LIBRARY_REPLACEMENT_AUDIT_DEEP.md` (825 lines)
- `LIBRARY_REPLACEMENT_PHASE_DWBS.md`

**TODO**:

- [ ] Consolidate into unified replacement plan
- [ ] Add migration strategy for each library
- [ ] Add performance benchmarks
- [ ] Add compatibility matrices
- [ ] Add rollback procedures
- [ ] Cross-reference with WBS

**Target**: `docs/research/LIBRARY_REPLACEMENT_COMPLETE.md`

### 4. Phase Documents (phase13-_, phase14-_, phase15-\*)

**TODO**:

- [ ] Add "Purpose" section to each
- [ ] Add "Depends" section
- [ ] Add acceptance criteria
- [ ] Add WORK_STREAM IDs
- [ ] Link to 02-UNIFIED-WBS

**Target**: Updated phase docs with complete structure

### 5. GOVERNANCE_WP_GAPS.md

**TODO**:

- [ ] Convert gaps into BACKLOG items
- [ ] Expand each gap with options
- [ ] Add owner assignments
- [ ] Add priority rankings
- [ ] Link to WORK_STREAM

**Target**: BACKLOG items + expanded gap analysis

### 6. COST_ROUTING_DEFERRED.md

**TODO**:

- [ ] Either implement cost routing
- [ ] Or formalize as deferred with unblock criteria
- [ ] Add decision record (ADR)
- [ ] Add timeline for implementation

**Target**: Implementation plan OR deferral documentation

---

## Priority 2: Index & Summary Docs

### 7. SWARM_RESEARCH_INDEX.md

**TODO**:

- [ ] Add "sprawl-status" column per linked doc
- [ ] Link to RESEARCH_SEED_FRAGMENT_INVENTORY
- [ ] Mark which docs are complete vs fragments

**Target**: Updated index with sprawl status

### 8. CROSS_PLATFORM_RESEARCH_INDEX.md

**TODO**:

- [ ] Add sprawl-status column
- [ ] Link to RESEARCH_SEED_FRAGMENT_INVENTORY
- [ ] Ensure each target doc has sprawl todo if fragment

**Target**: Updated index with sprawl status

### 9. 00-MASTER-INDEX.md

**TODO**:

- [ ] Add "Research sprawl" row
- [ ] Link to RESEARCH_SEED_FRAGMENT_INVENTORY
- [ ] Add sprawl status tracking

**Target**: Updated master index

---

## Priority 3: Full Research Docs (Audit & Polish)

### 10. CROSS_PLATFORM_MULTI_TENANT_DESKTOP_AUTOMATION_RESEARCH.md (3956 lines)

**TODO**:

- [ ] Add summary table at top
- [ ] Cross-link to WORK_STREAM/WBS
- [ ] Add "Next actions" with IDs
- [ ] Robustify (failure modes, validation)
- [ ] Add performance targets

**Target**: Polished comprehensive research doc

### 11. FASTMCP_IMPLEMENTATION_GUIDE.md (1332 lines)

**TODO**:

- [ ] Add summary table
- [ ] Cross-link to implementation plans
- [ ] Add "Next actions" with IDs
- [ ] Add troubleshooting section
- [ ] Add performance benchmarks

**Target**: Complete implementation guide

### 12. PYTHON_FRONTMATTER_NATIVE_BACKMATTER_AUDIT_PLAN.md (959 lines)

**TODO**:

- [ ] Add summary table
- [ ] Cross-link to migration plans
- [ ] Add "Next actions" with IDs
- [ ] Add migration timeline
- [ ] Add rollback procedures

**Target**: Complete audit and migration plan

### 13. CACHING_INDEXING_PREWARMING_DEEP_RESEARCH.md (839 lines)

**TODO**:

- [ ] Add summary table
- [ ] Cross-link to implementation
- [ ] Add "Next actions" with IDs
- [ ] Add performance targets
- [ ] Add cost analysis

**Target**: Complete research with implementation guidance

### 14. LIBRARY_REPLACEMENT_AUDIT_DEEP.md (825 lines)

**TODO**:

- [ ] Add summary table
- [ ] Cross-link to replacement plans
- [ ] Add "Next actions" with IDs
- [ ] Add migration strategies
- [ ] Add compatibility matrices

**Target**: Complete audit with migration plan

---

## Priority 4: Normalization (All MD Docs)

### 15. Frontmatter Standardization

**TODO**:

- [ ] Ensure all docs have frontmatter or H1 title
- [ ] Add purpose/status/date to each
- [ ] Standardize format

**Target**: All docs normalized

### 16. Cross-Linking

**TODO**:

- [ ] Add "See also" sections
- [ ] Link to WORK_STREAM where relevant
- [ ] Link to 00-MASTER-INDEX where relevant
- [ ] Link to related research/plans

**Target**: Comprehensive cross-linking

### 17. Structure Consistency

**TODO**:

- [ ] Consistent heading levels
- [ ] Consistent section ordering
- [ ] Consistent table formats
- [ ] Consistent code block formats

**Target**: Uniform structure across all docs

---

## Progress Tracking

### Completed ✅

- [x] SESSION_RESEARCH_FRAGMENTS.md → Expanded
- [x] CONVERSATION_DUMP_2026-02-16.md → Expanded
- [x] idea-seeds/\*.md (4 files) → Expanded

### In Progress 🔄

- [ ] CROSS_PLATFORM research consolidation
- [ ] HOOK_RUST_MIGRATION expansion
- [ ] LIBRARY_REPLACEMENT consolidation

### Pending 📅

- [ ] Phase documents expansion
- [ ] GOVERNANCE_WP_GAPS conversion
- [ ] COST_ROUTING_DEFERRED formalization
- [ ] Index docs updates
- [ ] Full research docs polish
- [ ] All MD normalization

---

## Next Steps

1. **Continue P0 expansions** (if any remaining)
2. **Begin P1 expansions** (high-value consolidations)
3. **Update indexes** (P2) as docs are expanded
4. **Polish full research docs** (P3) with summaries and cross-links
5. **Normalize all MD docs** (P4) for consistency

---

## References

- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Main inventory
- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [02-UNIFIED-WBS.md](../plans/02-UNIFIED-WBS.md) - Work breakdown structure
- [DOCUMENTATION_EXPANSION_TODO.md](../plans/DOCUMENTATION_EXPANSION_TODO.md) - Original expansion TODO

---

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream (all extracted BACKLOG items)
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) - Plan index
- [02-UNIFIED-WBS.md](../plans/02-UNIFIED-WBS.md) - Work breakdown structure

---

**Status**: Active expansion in progress
**Last Updated**: 2026-02-17

---

## 8. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added planning patterns
2. Added implementation roadmap
3. Enhanced cross-references

### Cross-References Added

- WORK_STREAM.md
- Implementation guides

### Practical Additions

- Planning templates
- Roadmap configurations
