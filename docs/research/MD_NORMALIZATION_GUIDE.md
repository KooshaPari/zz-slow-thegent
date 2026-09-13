<DONE>
# MD Documentation Normalization Guide

> **Status**: Complete | **Date**: 2026-02-17
> **Purpose**: Guide for normalizing all MD docs with frontmatter, cross-links, and "See also" sections

---

## Normalization Checklist

### 1. Frontmatter

**Required Format**:

```markdown
---
title: Document Title
status: Complete | Draft | In Progress
date: YYYY-MM-DD
purpose: Brief purpose statement
---

# Document Title
```

**Or Alternative** (if no frontmatter):

```markdown
# Document Title

> **Status**: Complete | **Date**: YYYY-MM-DD
> **Purpose**: Brief purpose statement
```

### 2. Cross-Links

**Required Sections**:

- Link to [WORK_STREAM.md](../reference/WORK_STREAM.md) if work items exist
- Link to [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) if fragment/seed
- Link to [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) if plan-related
- Link to related research/plan documents

### 3. "See Also" Section

**Required Format**:

```markdown
## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
- [Related Document](./RELATED_DOC.md) - Related topic
```

---

## Expanded/Consolidated Docs Status

| Document                                           | Frontmatter | See Also | Cross-Links | Status   |
| -------------------------------------------------- | ----------- | -------- | ----------- | -------- |
| SESSION_RESEARCH_FRAGMENTS_EXPANDED.md             | ✅          | ✅       | ✅          | Complete |
| CONVERSATION_DUMP_2026-02-16_EXPANDED.md           | ✅          | ✅       | ✅          | Complete |
| CROSS_PLATFORM_RESEARCH_CONSOLIDATED.md            | ✅          | ✅       | ✅          | Complete |
| HOOK_RUST_MIGRATION_RESEARCH_SYNTHESIS_EXPANDED.md | ✅          | ✅       | ✅          | Complete |
| LIBRARY_REPLACEMENT_CONSOLIDATED.md                | ✅          | ✅       | ✅          | Complete |
| PHASE_DOCUMENTS_EXPANDED.md                        | ✅          | ✅       | ✅          | Complete |
| GOVERNANCE_WP_GAPS_EXPANDED.md                     | ✅          | ✅       | ✅          | Complete |
| COST_ROUTING_DEFERRED_EXPANDED.md                  | ✅          | ✅       | ✅          | Complete |

**Status**: ✅ All expanded/consolidated docs normalized

---

## Standardization Rules

### Heading Levels

- **H1**: Document title only
- **H2**: Major sections
- **H3**: Subsections
- **H4**: Sub-subsections

### Table Format

- Use markdown tables for structured data
- Include headers
- Align columns consistently

### Code Blocks

- Use language tags: ` ```python`, ` ```rust`, ` ```bash`
- Include context comments
- Show imports/exports

### Links

- Use relative paths: `[Text](./file.md)`
- Use absolute paths for cross-directory: `[Text](../other/file.md)`
- Link to WORK_STREAM for work items

---

## Automation

**Script**: `scripts/normalize-md-docs.sh`

**Usage**:

```bash
./scripts/normalize-md-docs.sh
```

**Checks**:

- Frontmatter presence
- "See also" sections
- Cross-links to WORK_STREAM
- Heading level consistency

---

## References

- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) - Master index

---

**Status**: Normalization guide complete. All expanded docs follow standards.

---

## 7. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added practical implementation patterns
2. Added configuration examples
3. Enhanced cross-references to related docs

### Cross-References Added

- Related research and implementation guides
- WORK_STREAM.md for tracking

### Practical Additions

- Implementation templates
- Configuration examples
- Best practices

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [SEE_ALSO_TEMPLATE.md](./SEE_ALSO_TEMPLATE.md) - Template guide
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
