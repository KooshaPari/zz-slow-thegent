<DONE>
# "See Also" Section Template

> **Purpose**: Standard template for consistent "See Also" sections across all documentation

---

## Standard Template

```markdown
---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) - Master index
- [Related Document](./RELATED_DOC.md) - Related topic
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory (if research doc)
```

---

## Variations by Document Type

### Research Documents

```markdown
## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
- [Related Research](./RELATED_RESEARCH.md) - Related research
- [02-UNIFIED-WBS.md](../plans/02-UNIFIED-WBS.md) - Work breakdown structure
```

### Expanded/Consolidated Documents

```markdown
## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream (X BACKLOG items)
- [Original Document](./ORIGINAL_DOC.md) - Original fragment (if applicable)
- [Consolidated Version](./CONSOLIDATED_DOC.md) - Consolidated guide (if applicable)
- [02-UNIFIED-WBS.md](../plans/02-UNIFIED-WBS.md) - Work breakdown structure
```

### Plan Documents

```markdown
## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) - Master index
- [02-UNIFIED-WBS.md](../plans/02-UNIFIED-WBS.md) - Work breakdown structure
- [Related Plan](./RELATED_PLAN.md) - Related plan
```

### Index/Summary Documents

```markdown
## See Also

- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) - Master index
```

---

## Guidelines

1. **Always include**: WORK_STREAM.md link
2. **Research docs**: Include RESEARCH_SEED_FRAGMENT_INVENTORY
3. **Plan docs**: Include 00-MASTER-INDEX.md and 02-UNIFIED-WBS.md
4. **Expanded docs**: Link to original/consolidated versions
5. **Keep it relevant**: Only link to directly related documents
6. **Consistent format**: Use bullet list with descriptive text

---

**Status**: Template ready for use

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
