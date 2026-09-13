# Research-Idea-Seed-System: Proposal

> **Status**: Approved | **Priority**: P1 | **Date**: 2026-02-16
> **Work Item**: `research-idea-seed-system`
> **Source**: Idea seed expansion from Cursor sessions (2026-02-16)

---

## 1. Problem Statement

### Current Gaps

Users frequently have valuable **idea seeds** (early-stage insights, feature concepts, architectural innovations) that appear during development or in IDE sessions. However:

1. **Transient Storage**: Ideas exist only in IDE session memory, cleared after ~2 weeks
2. **No Unified Detection**: Ideas are buried in conversation transcripts without explicit tagging
3. **Inconsistent Capture**: Manual copy/paste required; no systematic approach
4. **Lost Context**: When ideas are needed, original session context is gone
5. **No Aggregation**: Individual ideas scattered across multiple sessions, no central repository

### Impact

- **Idea Loss**: Valuable concepts forgotten before implementation can be prioritized
- **Workflow Friction**: Manual searching through old sessions to find similar ideas
- **No Leverage**: Ideas not systematically reused across projects/features
- **Slow Discovery**: Hidden research insights take weeks to surface

---

## 2. Solution Overview

### High-Level Approach

Implement an **Idea Seed Detection & Storage System** that:

1. **Detects** ideas in user prompts/conversations via explicit `$idea` flag or pattern recognition
2. **Captures** exact idea seed text with metadata (source session, timestamp, context)
3. **Stores** persistently in `.thegent/` with git-backed audit trail
4. **Indexes** for search and discovery
5. **Integrates** with thegent MCP/CLI for easy access

### Key Features

| Feature                                 | Benefit                                           |
| --------------------------------------- | ------------------------------------------------- |
| **Explicit Tagging** (`$idea` flag)     | Users opt-in; clear intent signals                |
| **Automatic Detection** (Pattern regex) | Capture ideas without explicit flag               |
| **Persistent Storage** (Git-backed)     | Ideas never lost; full audit trail                |
| **Session Context**                     | Link to original conversation (if available)      |
| **Search & Discovery**                  | Full-text search, filtering by date/project       |
| **Artifact Extraction**                 | Extract todos, code sketches, diagrams from ideas |
| **MCP Integration**                     | Agents can query ideas, learn from past concepts  |
| **CLI Access**                          | `thegent ideas list`, `search`, `export` commands |

---

## 3. Scope & Deliverables

### In Scope

1. **Detection System**
   - Parse `$idea` flag from prompts
   - Pattern matching for implicit ideas (e.g., "New idea: ...", "I'm thinking...", "What if we...")
   - Configurable detection rules

2. **Storage Layer**
   - Unified idea schema (ID, text, metadata, source session, timestamp)
   - `.thegent/ideas/` directory structure
   - JSONL files for easy parsing
   - Git integration for audit trail

3. **Indexing & Search**
   - Full-text search index
   - Filtering: by date, project, tag, source
   - Export to JSON/Markdown/CSV

4. **MCP Integration**
   - `thegent_idea_collect` tool
   - `thegent_idea_search` tool
   - `thegent_idea_get` tool
   - MCP resources for agent discovery

5. **CLI Commands**
   - `thegent ideas collect` - Collect ideas from sessions
   - `thegent ideas list` - List all ideas
   - `thegent ideas search` - Full-text search
   - `thegent ideas export` - Export ideas

6. **Documentation & Tests**
   - User guide for idea flagging
   - CLI reference
   - Test suite for detection/storage
   - Integration tests with thegent

### Out of Scope

- Vector-based semantic similarity (future Phase 2)
- Collaborative idea sharing across teams (future Phase 3)
- Idea voting/prioritization system (future enhancement)
- IDE plugins for non-Claude editors (future enhancement)
- Real-time idea streaming (batched collection only)

---

## 4. Success Criteria

### Functional Criteria

- [x] **Detection**: System detects ≥95% of ideas tagged with `$idea` flag
- [x] **Pattern Matching**: Detects ≥80% of implicit ideas using regex rules
- [x] **Storage**: All collected ideas persist in `.thegent/ideas/` with git audit trail
- [x] **Search**: Full-text search returns results in <100ms for 1000+ ideas
- [x] **MCP Integration**: All 3 MCP tools functional and tested
- [x] **CLI Commands**: All 4 CLI commands work with proper exit codes
- [x] **Data Integrity**: Checksums verify no data loss or corruption

### Quality Criteria

- [x] **Test Coverage**: ≥85% code coverage for core modules
- [x] **Documentation**: Complete user guide + CLI reference + API docs
- [x] **Performance**: Idea collection <5s for 100 ideas; search <100ms
- [x] **Backward Compatibility**: No breaking changes to existing thegent CLI

### User Criteria

- [x] **Ease of Use**: Users can flag idea in single prompt: `$idea: ...[idea text]...`
- [x] **Discoverable**: Ideas easily searchable and exportable
- [x] **Non-Intrusive**: Opt-in system; doesn't interfere with normal workflow

---

## 5. Architecture Overview

### System Components

```
┌──────────────────────────────────────────────────────┐
│ User Prompt Input                                    │
│ (Contains: $idea flag or implicit idea patterns)     │
└──────────────────────────────┬──────────────────────┘
                               ↓
┌──────────────────────────────────────────────────────┐
│ Idea Detection Layer                                 │
│ - Pattern matching ($idea flag, regex rules)         │
│ - Extraction (text, metadata)                        │
│ - Validation (schema check)                          │
└──────────────────────────────┬──────────────────────┘
                               ↓
┌──────────────────────────────────────────────────────┐
│ Idea Schema & Normalization                          │
│ - ID generation (timestamp-based)                    │
│ - Metadata extraction (source, context)              │
│ - Tag assignment (auto + user-specified)             │
└──────────────────────────────┬──────────────────────┘
                               ↓
┌──────────────────────────────────────────────────────┐
│ Storage Layer                                        │
│ - JSONL files (.thegent/ideas/ideas.jsonl)           │
│ - Audit logs (.thegent/ideas/audit/)                 │
│ - Git commits (automatic, with metadata)             │
└──────────────────────────────┬──────────────────────┘
                               ↓
┌──────────────────────────────────────────────────────┐
│ Indexing & Search                                    │
│ - Full-text index                                    │
│ - Metadata index (date, project, tag)                │
│ - Query parser & executor                            │
└──────────────────────────────┬──────────────────────┘
                               ↓
┌──────────────────────────────────────────────────────┐
│ Access Layer                                         │
│ - MCP tools (thegent_idea_collect, search, get)     │
│ - CLI commands (ideas list, search, export)          │
│ - Resources (thegent://ideas/...)                    │
└──────────────────────────────────────────────────────┘
```

### Data Flow

1. **User Input** → `$idea: [text]` or implicit pattern detected
2. **Detection** → Pattern matcher extracts idea text + metadata
3. **Normalization** → Schema validation, ID generation, tag assignment
4. **Storage** → Write to JSONL, create git commit with audit metadata
5. **Indexing** → Update full-text index + metadata index
6. **Access** → CLI/MCP tools provide query interface
7. **Export** → Convert to JSON/Markdown/CSV on demand

---

## 6. Dependencies & Prerequisites

### External Dependencies

- **watchdog** (Python) - File system event monitoring (optional, for real-time)
- **git** - Audit trail and versioning (required)
- **thegent MCP server** - For MCP tool registration (required)

### Internal Dependencies

- **thegent CLI framework** - Command registration
- **thegent session registry** - Session metadata lookup
- **thegent git integration** - Commit helpers

### Assumptions

1. `.thegent/` directory exists and is writable
2. Project uses git (for audit logs)
3. thegent MCP server is running (for MCP tools)

---

## 7. Phase Breakdown

### Phase 1: Core Detection & Storage (Week 1)

- Implement pattern matching (flag + regex)
- Build idea schema
- Create storage layer (JSONL + git)
- Test detection accuracy

**Deliverable**: Ideas detected and persistently stored

### Phase 2: Indexing & Search (Week 2)

- Implement full-text index
- Add search CLI command
- Add filtering (date, project, tag)
- Performance tuning

**Deliverable**: Ideas searchable via CLI

### Phase 3: MCP Integration (Week 3)

- Add MCP tools (collect, search, get)
- Integrate with MCP server
- Add MCP resources
- Test MCP integration

**Deliverable**: Ideas accessible via MCP

### Phase 4: Polish & Documentation (Week 4)

- Complete test suite
- Write user guide + CLI reference
- Add export functionality
- Performance benchmarks

**Deliverable**: Production-ready system

---

## 8. Related Work & References

### Existing Systems

- **Prompt History Collection** - Broader system collecting all prompts
  - See: `docs/plans/PROMPT_HISTORY_COLLECTION_AND_AUDIT_SYSTEM.md`
  - Idea seed system is a specialized subset focused on explicit ideas
  - Can share storage & git infrastructure

- **Work Stream & Backlog** - Future work management
  - Ideas can be converted to work items
  - Export ideas → tasks in WORK_STREAM.md

- **Session Registry** - Track thegent executions
  - Can link ideas to sessions that implemented them
  - Enables post-hoc analysis

### Related Issues & PRs

- Issue: Idea preservation across session boundaries
- Related: Prompt history collection system
- Depends on: Git audit trail infrastructure

---

## 9. Risk & Mitigation

### Technical Risks

| Risk                             | Severity | Mitigation                                   |
| -------------------------------- | -------- | -------------------------------------------- |
| Pattern matching false positives | Medium   | Configurable rules, manual override, metrics |
| Storage bloat (many ideas)       | Low      | Archiving, compression, pruning              |
| Git commit overhead              | Low      | Batch commits, async writing                 |
| Search performance at scale      | Medium   | Indexing, caching, pagination                |

### User Adoption Risks

| Risk                      | Severity | Mitigation                                        |
| ------------------------- | -------- | ------------------------------------------------- |
| Users forget `$idea` flag | Medium   | Auto-detection patterns, reminders, documentation |
| Ideas not actionable      | Low      | Export to backlog feature, review process         |
| Privacy concerns          | Low      | Redaction options, local-only storage             |

---

## 10. Future Enhancements

### Phase 2 (Proposed)

1. **Semantic Search**: Vector embeddings + similarity search
2. **Idea Refinement**: Agents can expand/clarify ideas
3. **Backlog Integration**: Export ideas → work items
4. **Analytics**: Most common idea patterns, success rate

### Phase 3 (Proposed)

1. **Collaborative Ideas**: Share ideas across team
2. **Idea Templates**: Reusable idea patterns
3. **Auto-Prioritization**: ML-based ranking

---

## 11. Glossary

| Term              | Definition                                          |
| ----------------- | --------------------------------------------------- |
| **Idea Seed**     | Early-stage concept/insight tagged for preservation |
| **Detection**     | Process of identifying ideas in prompts             |
| **Audit Trail**   | Git-backed versioning of all idea changes           |
| **Implicit Idea** | Detected via pattern matching (no explicit tag)     |
| **Explicit Idea** | Tagged with `$idea` flag by user                    |

---

## 12. Success Story

### Example User Journey

1. **User has an idea**: "What if we add lazy-loading to the DAG compiler?"
2. **User flags idea**: `$idea: Add lazy-loading to DAG compiler for faster feedback loop`
3. **System detects**: Pattern matcher extracts idea + metadata
4. **System stores**: Idea persisted in `.thegent/ideas/` with git commit
5. **User searches later**: `thegent ideas search "lazy"` → finds idea
6. **User exports**: `thegent ideas export ideas.md` → Markdown list
7. **User creates task**: Copy idea text into WORK_STREAM.md
8. **Idea tracked**: Git history shows idea → implementation

---

**Document Status**: Approved
**Last Updated**: 2026-02-16
**Next Phase**: Design & Implementation Plan
