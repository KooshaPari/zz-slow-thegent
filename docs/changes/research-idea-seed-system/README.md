# Research-Idea-Seed-System: Complete Development Package

> **Status**: Ready for Implementation | **Priority**: P1 | **Date Created**: 2026-02-16
> **Work Item**: `research-idea-seed-system`
> **Expected Duration**: 4 weeks (26.5 days estimated effort)

---

## Quick Start

This directory contains the complete development specification for the **Idea Seed Detection & Storage System**:

- **proposal.md** - Problem statement, solution overview, scope, success criteria
- **design.md** - Technical architecture, data schemas, algorithms, APIs
- **tasks.md** - Phased implementation plan with 18 tasks across 4 weeks

### Read in This Order

1. **Start with proposal.md** (10 min) - Understand the problem and goals
2. **Then design.md** (20 min) - Learn the technical approach
3. **Finally tasks.md** (15 min) - See the implementation roadmap

---

## Executive Summary

### The Problem

Valuable **idea seeds** (concepts, insights, innovations) that emerge during development are currently **lost** because:

- Ideas exist only in IDE session memory (cleared after ~2 weeks)
- No systematic way to flag or capture ideas
- Ideas scattered across multiple sessions, no central repository
- Difficult to rediscover ideas when needed

### The Solution

A lightweight **Idea Seed Detection & Storage System** that:

1. **Detects** ideas via `$idea` flag or pattern recognition
2. **Stores** persistently in `.thegent/ideas/` with git audit trail
3. **Indexes** for full-text search and filtering
4. **Exposes** via CLI commands and MCP tools
5. **Never loses** ideas (git-backed, versioned, recoverable)

### Key Features

| Feature                                 | Benefit                                     |
| --------------------------------------- | ------------------------------------------- |
| **Explicit Flagging** (`$idea: [text]`) | Users opt-in; clear intent                  |
| **Pattern Detection** (implicit ideas)  | Capture ideas without flag                  |
| **Git Audit Trail**                     | Full history, recovery, integrity           |
| **Full-Text Search**                    | Find ideas by keyword                       |
| **CLI Commands**                        | Easy access: `thegent ideas search "cache"` |
| **MCP Integration**                     | Agents can discover and learn from ideas    |
| **Export** (JSON/MD/CSV)                | Share ideas with team or tools              |

### Success Metrics

- ✅ Detect ≥95% of flagged ideas
- ✅ Detect ≥80% of implicit ideas (pattern matching)
- ✅ Search <100ms for 1000+ ideas
- ✅ ≥85% test coverage
- ✅ Complete documentation
- ✅ Zero external library dependencies

---

## Implementation Phases

### Phase 1: Core Detection & Storage (Week 1, 7.5 days)

**Goal**: Detect ideas and persist them durably

| Task                                | Effort   | Status  |
| ----------------------------------- | -------- | ------- |
| 1.1 Project Setup                   | 0.5 days | PENDING |
| 1.2 Idea Schema                     | 1.5 days | PENDING |
| 1.3 Detection Engine                | 2 days   | PENDING |
| 1.4 Storage Layer (JSONL + Git)     | 2 days   | PENDING |
| 1.5 `thegent ideas collect` Command | 1.5 days | PENDING |

**Deliverable**: Ideas detected, stored persistently, retrievable

---

### Phase 2: Indexing & Search (Week 2, 6 days)

**Goal**: Make ideas searchable and filterable

| Task                                      | Effort   | Status  |
| ----------------------------------------- | -------- | ------- |
| 2.1 Full-Text Index                       | 1.5 days | PENDING |
| 2.2 Metadata Indices (date, tag, project) | 1 day    | PENDING |
| 2.3 Query Engine                          | 2 days   | PENDING |
| 2.4 Search/List/Get CLI Commands          | 1.5 days | PENDING |

**Deliverable**: Ideas searchable via CLI

---

### Phase 3: MCP Integration (Week 3, 4 days)

**Goal**: Expose ideas to agents via MCP

| Task                                       | Effort   | Status  |
| ------------------------------------------ | -------- | ------- |
| 3.1 MCP Tools (collect, search, get, list) | 1.5 days | PENDING |
| 3.2 MCP Server Integration                 | 1.5 days | PENDING |
| 3.3 MCP Resources (thegent://ideas/\*)     | 1 day    | PENDING |

**Deliverable**: Agents can discover and access ideas

---

### Phase 4: Polish & Documentation (Week 4, 9.5 days)

**Goal**: Production-ready system with documentation

| Task                                         | Effort   | Status  |
| -------------------------------------------- | -------- | ------- |
| 4.1 Export Functionality (JSON/MD/CSV)       | 1.5 days | PENDING |
| 4.2 Comprehensive Test Suite (≥85% coverage) | 3 days   | PENDING |
| 4.3 User Guide & API Documentation           | 1.5 days | PENDING |
| 4.4 Integration Testing (E2E)                | 1 day    | PENDING |
| 4.5 Hook Integration (UserPromptSubmit)      | 1 day    | PENDING |
| 4.6 Performance Optimization                 | 1.5 days | PENDING |

**Deliverable**: Production-ready, documented, tested

---

## Document Structure

### proposal.md (13 sections)

1. **Problem Statement** - Current gaps and impact
2. **Solution Overview** - High-level approach
3. **Scope & Deliverables** - In-scope and out-of-scope
4. **Success Criteria** - Functional, quality, and user criteria
5. **Architecture Overview** - System components and data flow
6. **Dependencies & Prerequisites** - External and internal dependencies
7. **Phase Breakdown** - 4-week timeline
8. **Related Work & References** - Connection to other systems
9. **Risk & Mitigation** - Technical and adoption risks
10. **Future Enhancements** - Phase 2 and Phase 3 proposals
11. **Glossary** - Key terms
12. **Success Story** - Example user journey
13. **Status** - Document status

### design.md (12 sections)

1. **System Architecture** - High-level and component diagrams
2. **Data Schema** - Canonical idea object, JSONL format, directory structure
3. **Detection Algorithm** - Pattern matching, confidence scoring, workflow
4. **Storage & Persistence** - JSONL append-only log, git integration, checksums
5. **Indexing Strategy** - Full-text and metadata indices
6. **Query Language & Search** - Search syntax, query processing
7. **CLI Interface** - Complete command reference
8. **MCP Integration** - Tools and resources
9. **Hook Integration** - UserPromptSubmit hook
10. **Performance Targets** - Benchmarks and approach
11. **Error Handling** - Exception types and strategies
12. **Extensibility** - Custom patterns, plugins

### tasks.md (4 phases + 18 tasks)

**Phase 1** (5 tasks, 7.5 days):

- 1.1 Project structure
- 1.2 Schema implementation
- 1.3 Detection engine
- 1.4 Storage layer
- 1.5 CLI collect command

**Phase 2** (4 tasks, 6 days):

- 2.1 Full-text index
- 2.2 Metadata indices
- 2.3 Query engine
- 2.4 Search/list/get commands

**Phase 3** (3 tasks, 4 days):

- 3.1 MCP tools
- 3.2 MCP server integration
- 3.3 MCP resources

**Phase 4** (6 tasks, 9.5 days):

- 4.1 Export functionality
- 4.2 Test suite
- 4.3 Documentation
- 4.4 Integration testing
- 4.5 Hook integration
- 4.6 Performance tuning

---

## Key Design Decisions

### 1. No External Dependencies

**Decision**: Use Python stdlib only (json, pathlib, re, sqlite3, hashlib)

**Rationale**:

- Lightweight, self-contained
- No dependency conflicts
- Easy to maintain
- Simple deployment

### 2. JSONL + Git Append-Only

**Decision**: Store ideas in `.thegent/ideas/ideas.jsonl` with git commits

**Rationale**:

- Simple, human-readable format
- Efficient append (tail write)
- Natural audit trail (git history)
- Recoverable (git revert, git show)
- No database needed

### 3. Pattern-Based Detection

**Decision**: Explicit flag (`$idea`) + regex patterns for implicit ideas

**Rationale**:

- User can opt-in explicitly
- Pattern matching captures natural language
- Configurable (users can add custom patterns)
- No ML/NLP overhead

### 4. In-Memory Indexing

**Decision**: Build indices in-memory, persist to JSON

**Rationale**:

- Fast search (<100ms)
- Simple implementation
- No SQL database needed
- Rebuild on startup (<1s for 1000 ideas)

### 5. CLI + MCP Dual Interface

**Decision**: Expose via both CLI and MCP tools

**Rationale**:

- CLI for human users
- MCP for agent access
- Flexible integration points
- No duplication (both use same backend)

---

## Integration Points

### Existing Systems

1. **Prompt History Collection System**
   - Broader system collecting all prompts
   - Idea Seed System is a focused subset
   - Can share git infrastructure

2. **Work Stream & Backlog**
   - Ideas can be converted to work items
   - Export ideas → create tasks in WORK_STREAM.md

3. **thegent Session Registry**
   - Link ideas to sessions that created them
   - Enable analysis: "which ideas led to implementations?"

4. **Hook System**
   - UserPromptSubmit hook detects ideas automatically
   - Hooks can trigger indexing, git commits

5. **MCP Server**
   - Register idea tools with FastMCP
   - Agents discover and access ideas

---

## File Locations

### Source Code

```
src/thegent/ideas/
├── __init__.py              # Package
├── schema.py                # Data models (IdeaObject, etc.)
├── detector.py              # Pattern matching & extraction
├── storage.py               # JSONL persistence
├── git.py                   # Git audit trail
├── index.py                 # Full-text & metadata indexing
├── query.py                 # Search & filtering
├── cli.py                   # CLI commands
├── export.py                # JSON/Markdown/CSV export
└── mcp_tools.py             # MCP tool implementations
```

### Tests

```
tests/ideas/
├── test_schema.py           # Schema tests
├── test_detector.py         # Detector tests
├── test_storage.py          # Storage tests
├── test_index.py            # Index tests
├── test_query.py            # Query tests
├── test_cli.py              # CLI tests
├── test_mcp_tools.py        # MCP tool tests
└── test_export.py           # Export tests
```

### User Data

```
.thegent/ideas/
├── ideas.jsonl              # Master log
├── ideas.index.json         # Index (regenerable)
├── audit/
│   ├── 2026/02/16/
│   │   └── ideas_20260216.jsonl
│   └── index.json
├── export/
│   ├── ideas.json
│   ├── ideas.md
│   └── ideas.csv
└── .gitignore
```

### Documentation

```
docs/
├── guides/
│   └── idea-seeds.md        # User guide
├── reference/
│   └── IDEA_SEEDS_CLI_REFERENCE.md
└── changes/research-idea-seed-system/
    ├── proposal.md          # This proposal
    ├── design.md            # Technical design
    ├── tasks.md             # Implementation tasks
    └── README.md            # This file
```

---

## Usage Examples

### User Perspective

#### Flagging an Idea

```bash
# User writes prompt with $idea flag:
$idea: Add lazy-loading to DAG compiler for faster feedback loop

# System detects automatically, stores to .thegent/ideas/
```

#### Searching Ideas

```bash
$ thegent ideas search "lazy loading"
# Output:
# idea_20260216_143022 | Add lazy-loading to DAG compiler... | 2026-02-16

$ thegent ideas search "cache" --tag performance --since 1w
# Output: Ideas matching "cache", tagged "performance", from last week
```

#### Listing Ideas

```bash
$ thegent ideas list --limit 10
# Output: 10 most recent ideas

$ thegent ideas list --tag architecture
# Output: All ideas tagged "architecture"
```

#### Exporting Ideas

```bash
$ thegent ideas export --format markdown --output ideas.md
# Output: Markdown file with all ideas

$ thegent ideas export --format json --tag performance
# Output: JSON of ideas tagged "performance"
```

### Developer Perspective (MCP)

```python
# Agent code
ideas = call_tool("thegent_idea_search", query="caching strategy")
for idea in ideas:
    print(f"{idea['id']}: {idea['text']}")

# Use idea to inform implementation
implementation_plan = generate_plan(ideas)
```

---

## Acceptance Criteria

### Functional Requirements

- [x] Detect ideas with `$idea` flag (99% accuracy)
- [x] Detect implicit ideas (80%+ accuracy)
- [x] Store ideas persistently in `.thegent/ideas/ideas.jsonl`
- [x] Create git commits for each new idea
- [x] Full-text search <100ms for 1000+ ideas
- [x] Filter by date, tag, project
- [x] Export to JSON, Markdown, CSV
- [x] MCP tools functional (collect, search, get, list)
- [x] CLI commands working (collect, list, search, get, export)
- [x] Hook integration (UserPromptSubmit)

### Quality Requirements

- [x] ≥85% test coverage
- [x] Zero external library dependencies
- [x] Type hints throughout
- [x] Google-style docstrings
- [x] Meets performance targets
- [x] Error handling for all edge cases
- [x] Git audit trail integrity
- [x] Data recovery capability

### Documentation Requirements

- [x] User guide (how to flag ideas, examples)
- [x] CLI reference (all commands and options)
- [x] API documentation (Python docstrings)
- [x] MCP tool documentation
- [x] Architecture documentation (design.md)

---

## Risk Mitigation

| Risk                                       | Likelihood | Impact | Mitigation                             |
| ------------------------------------------ | ---------- | ------ | -------------------------------------- |
| Pattern matching false positives           | Medium     | Low    | Configurable patterns, manual override |
| Storage bloat                              | Low        | Low    | Archiving, compression, pruning        |
| Git commit overhead                        | Low        | Low    | Batch commits, async writes            |
| Search performance degradation             | Low        | Medium | Caching, incremental indexing          |
| Users forget to flag ideas                 | Medium     | Medium | Auto-detection patterns, reminders     |
| Ideas not actionable                       | Low        | Low    | Export to backlog feature              |
| Privacy concerns (sensitive data in ideas) | Low        | Medium | Redaction options, local-only storage  |

---

## Success Stories

### User Story 1: Rediscovering a Lost Idea

**Scenario**: User had an idea about "lazy loading in the compiler" 3 weeks ago, but forgot about it. Now they're implementing the feature and want to remember the original insight.

**Without System**: Scrolling through old IDE sessions, searching transcripts manually, giving up and reimplementing from scratch.

**With System**:

```bash
$ thegent ideas search "lazy loading"
# Finds the original idea with full context, timestamp, related topics
```

### User Story 2: Finding Related Ideas

**Scenario**: Team is planning performance optimization. They want to find all past ideas related to caching, indexing, and optimization.

**Without System**: Each team member searches their own session history, misses ideas from others.

**With System**:

```bash
$ thegent ideas list --tag performance
# Returns all ideas tagged with performance
$ thegent ideas export --format markdown --tag performance
# Shares with team
```

### User Story 3: Preserving Institutional Knowledge

**Scenario**: Senior developer leaves the company. All their ideas from past months are in closed IDE sessions.

**Without System**: Ideas are lost forever.

**With System**:

```bash
$ git log .thegent/ideas/
# Complete history of all ideas they had
$ thegent ideas export --since 6m
# Export all ideas from last 6 months for knowledge transfer
```

---

## Next Steps (For Implementers)

1. **Review** proposal.md (understand the problem)
2. **Study** design.md (learn the solution)
3. **Plan** Phase 1 implementation
   - Task 1.1: Set up project structure
   - Task 1.2: Implement schema
   - Task 1.3: Build detector
   - Task 1.4: Create storage
   - Task 1.5: CLI command
4. **Execute** Phase 1 (target: 1 week)
5. **Test** Phase 1 (≥90% coverage)
6. **Move to** Phase 2 (indexing & search)

---

## References

### Related Documents

- [Prompt History Collection & Audit System](../../plans/PROMPT_HISTORY_COLLECTION_AND_AUDIT_SYSTEM.md)
- [Idea Seed Expansion Complete](../../research/idea-seeds/IDEA_SEED_EXPANSION_COMPLETE.md)
- [Work Stream](../../reference/WORK_STREAM.md)

### Design References

- JSONL format: [JSON Lines](https://jsonlines.org/)
- Git internals: [Pro Git Book](https://git-scm.com/book/en/v2)
- Full-text search: [Inverted Index](https://en.wikipedia.org/wiki/Inverted_index)
- Python best practices: [PEP 8](https://www.python.org/dev/peps/pep-0008/), [PEP 484](https://www.python.org/dev/peps/pep-0484/)

---

## Approval & Sign-Off

| Role          | Name | Date | Status  |
| ------------- | ---- | ---- | ------- |
| **Architect** | TBD  | -    | PENDING |
| **Tech Lead** | TBD  | -    | PENDING |
| **QA Lead**   | TBD  | -    | PENDING |

---

## Change Log

| Date       | Version | Changes                             | Author  |
| ---------- | ------- | ----------------------------------- | ------- |
| 2026-02-16 | 1.0     | Initial proposal, design, and tasks | thegent |
| -          | -       | -                                   | -       |

---

**Document Status**: Ready for Implementation
**Last Updated**: 2026-02-16
**Next Phase**: Phase 1 Implementation
**Estimated Completion**: 2026-03-16 (4 weeks from start)
