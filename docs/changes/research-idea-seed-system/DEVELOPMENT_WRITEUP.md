# Research-Idea-Seed-System: Integrated Development Writeup

> **Status**: Ready for Implementation | **Date**: 2026-02-16
> **Work Item**: `research-idea-seed-system`
> **Duration**: 4 weeks (26.5 days estimated effort)
> **Priority**: P1

---

## 🎯 Executive Summary

### Problem Statement

Users have valuable **idea seeds** (concepts, insights, features) that emerge during development sessions, but **ideas are lost** because:

1. **Transient Storage** - Ideas exist only in IDE memory (cleared after ~2 weeks)
2. **No Systematic Capture** - Ideas buried in conversation transcripts without tagging
3. **Scattered Across Sessions** - Multiple sessions = no central repository
4. **Loss of Context** - When ideas are needed, original session context is gone
5. **No Aggregation** - Difficult to rediscover or cross-reference related ideas

**Impact**: Valuable concepts forgotten before implementation can be prioritized; manual searching through old sessions required.

### Solution Overview

Implement an **Idea Seed Detection & Storage System** that:

1. **Detects** ideas via explicit `$idea` flag or pattern recognition
2. **Stores** persistently in `.thegent/ideas/` with full git audit trail
3. **Indexes** for full-text search and metadata filtering
4. **Exposes** via CLI commands and MCP tools
5. **Never loses** ideas (git-backed, versioned, recoverable)

### Key Deliverables

| Component                                         | Status    | Impact                                  |
| ------------------------------------------------- | --------- | --------------------------------------- |
| Pattern-based detection (explicit + implicit)     | Phase 1   | Users flag or system auto-detects ideas |
| JSONL + git-backed storage                        | Phase 1   | Durable persistence with audit trail    |
| Full-text indexing & search                       | Phase 2   | Ideas discoverable in <100ms            |
| CLI commands (collect, list, search, get, export) | Phase 2-4 | Human-friendly access                   |
| MCP tools (collect, search, get, list)            | Phase 3   | Agent-friendly access                   |
| Export (JSON, Markdown, CSV)                      | Phase 4   | Share ideas with team/tools             |

---

## 📋 The Complete Picture

### Success Criteria

#### Functional

- ✅ Detect ≥95% of explicitly flagged ideas (`$idea:`)
- ✅ Detect ≥80% of implicit ideas (pattern matching)
- ✅ Persistent storage in `.thegent/ideas/` with git commits
- ✅ Full-text search <100ms for 1000+ ideas
- ✅ Filtering by date, tag, project
- ✅ Export to JSON/Markdown/CSV
- ✅ 4 MCP tools functional
- ✅ 5 CLI commands working

#### Quality

- ✅ ≥85% test coverage
- ✅ Zero external library dependencies (stdlib only)
- ✅ Type hints throughout
- ✅ Complete documentation
- ✅ All performance targets met
- ✅ Error handling and recovery capability

---

## 🏗️ System Architecture

### High-Level Components

```
┌─────────────────────────────────────┐
│ User Prompts (Claude/Cursor/Codex)  │
│ Containing: $idea flag or implicit  │
└────────────────┬────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│ Idea Detection Engine               │
│ • Pattern matching ($idea flag)     │
│ • Implicit patterns (regex rules)   │
│ • Confidence scoring                │
│ • Metadata extraction               │
└────────────────┬────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│ Storage Layer                       │
│ • JSONL append-only log             │
│ • Git commits (audit trail)         │
│ • Checksums (integrity)             │
│ • Daily snapshots                   │
└────────────────┬────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│ Indexing Layer                      │
│ • Full-text index (inverted)        │
│ • Metadata indices (date/tag/proj)  │
│ • Query execution                   │
└────────────────┬────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│ Access Layer                        │
│ • CLI: collect, list, search, get   │
│ • MCP tools: same operations        │
│ • Export: JSON, MD, CSV             │
└─────────────────────────────────────┘
```

### Data Schema (Canonical Idea Object)

```json
{
  "id": "idea_20260216_143022_abc123",
  "text": "Add lazy-loading to DAG compiler for faster feedback loop",
  "created_at": "2026-02-16T14:30:22Z",
  "source": {
    "type": "claude|cursor|codex",
    "session_id": "session_abc123",
    "workspace": "/path/to/project"
  },
  "detection": {
    "method": "explicit|implicit",
    "pattern": "$idea|what_if|new_idea",
    "confidence": 0.95
  },
  "tags": ["performance", "compiler", "dax"],
  "context": "Previous discussion about DAG compilation times...",
  "metadata": {
    "project": "thegent",
    "status": "seed|implemented",
    "linked_work_items": []
  },
  "git": {
    "commit_hash": "abc123def456",
    "branch": "main",
    "timestamp": "2026-02-16T14:30:25Z"
  },
  "checksum": "sha256:abc123..."
}
```

### Storage Structure

```
.thegent/ideas/
├── ideas.jsonl                  # Master append-only log
├── ideas.index.json             # Quick lookup index
├── audit/
│   ├── 2026/02/
│   │   ├── ideas_20260216.jsonl
│   │   └── ideas_20260217.jsonl
│   └── index.json               # Audit index + checksums
└── export/
    ├── ideas.json               # Latest export
    ├── ideas.md
    └── ideas.csv
```

---

## 🔍 Detection Algorithm

### Pattern Matching

#### Explicit Detection

```
Pattern: $idea:\s*(.+?)(?=$|$)
Example: "$idea: Add lazy-loading to DAG compiler"
Extracts: "Add lazy-loading to DAG compiler"
Confidence: 0.99 (user intent is explicit)
```

#### Implicit Detection

- `New idea:` / `Idea:` (confidence: 0.85)
- `What if we` / `Consider:` (confidence: 0.80)
- `I'm thinking about` / `Concept:` (confidence: 0.75)
- 7+ regex patterns covering common idea phrases

**Confidence Scoring**:

- Explicit flag: 0.99
- Implicit patterns: 0.70-0.90
- Manual override: 0.0 or 1.0

### Detection Workflow

```
1. Receive user prompt
2. Check for $idea flag (explicit)
3. Check regex patterns (implicit)
4. Extract metadata (source, timestamp, context)
5. Validate schema (length, fields, format)
6. Check for duplicates (text hash)
7. Store to JSONL + git commit
8. Update indices
9. Return idea ID + metadata
```

---

## 💾 Persistence Strategy

### JSONL Append-Only Log

**Why**:

- Simple, human-readable
- Efficient append (tail write only)
- Natural git compatibility
- Full audit trail (one line per idea)
- Easy recovery (git history)

**Write Process**:

1. Serialize idea to JSON
2. Append newline + JSON to `ideas.jsonl`
3. Fsync for durability
4. Create git commit: `idea: {id} {short_text}`
5. Update indices

### Git Integration

**Audit Trail**:

- One commit per idea (immediate)
- Commit msg: `idea: {id} {short_text}`
- Full history: `git log .thegent/ideas/`
- Recovery: `git show <commit>:.thegent/ideas/ideas.jsonl`

**Integrity**:

- SHA-256 checksums stored in idea object
- Verify on read: `sha256(idea_json) == idea.checksum`
- Daily snapshots for audit trail

---

## 🔎 Search & Indexing

### Full-Text Index

**Implementation**:

- Inverted index: word → [idea_ids]
- Tokenization: lowercase, stopword removal, stemming
- Updated incrementally as ideas arrive

**Performance**: <100ms search for 1000+ ideas

**Index File** (`.thegent/ideas/ideas.index.json`):

```json
{
  "inverted_index": {
    "lazy": ["idea_1", "idea_45"],
    "loading": ["idea_1", "idea_23"],
    "compiler": ["idea_1", "idea_56"]
  }
}
```

### Metadata Indices

- **Date Index**: `{YYYY-MM-DD → [idea_ids]}`
- **Tag Index**: `{tag → [idea_ids]}`
- **Project Index**: `{project → [idea_ids]}`
- **Status Index**: `{status → [idea_ids]}`

---

## 🖥️ CLI Interface

### Commands

#### `thegent ideas collect`

```bash
# Collect ideas from recent sessions
$ thegent ideas collect --since 6h
# Output: Collected 5 new ideas

# Collect with git commits
$ thegent ideas collect --git-commit
```

#### `thegent ideas list`

```bash
# List all ideas
$ thegent ideas list

# Filter by tag
$ thegent ideas list --tag performance --limit 10

# Verbose output with context
$ thegent ideas list --verbose
```

#### `thegent ideas search`

```bash
# Full-text search
$ thegent ideas search "lazy loading"

# Filter by tag + date
$ thegent ideas search "cache" --tag performance --since 1w

# Paginated results
$ thegent ideas search "feature" --limit 5 --offset 0
```

#### `thegent ideas get`

```bash
# Retrieve specific idea
$ thegent ideas get idea_20260216_143022_abc123

# JSON output
$ thegent ideas get idea_20260216_143022_abc123 --format json
```

#### `thegent ideas export`

```bash
# Export to JSON
$ thegent ideas export --format json --output ideas.json

# Export to Markdown
$ thegent ideas export --format markdown --output ideas.md

# Export with filters
$ thegent ideas export --format csv --tag architecture
```

---

## 🔗 MCP Integration

### MCP Tools

1. **`thegent_idea_collect`** - Collect ideas from sessions
2. **`thegent_idea_search`** - Full-text search ideas
3. **`thegent_idea_get`** - Retrieve specific idea by ID
4. **`thegent_idea_list`** - List ideas with filters

### MCP Resources

- `thegent://ideas` - List all ideas
- `thegent://ideas/{id}` - Get specific idea
- `thegent://ideas/recent` - 10 most recent
- `thegent://ideas/by-tag/{tag}` - Ideas by tag

### Agent Integration

```python
# Agents can query ideas to inform implementations
ideas = call_tool("thegent_idea_search", query="caching strategy")
for idea in ideas:
    use_in_planning(idea)
```

---

## 🎯 Implementation Phases

### Phase 1: Core Detection & Storage (Week 1, 7.5 days)

**Deliverable**: Ideas detected and persistently stored

| Task                 | Effort | Deliverable                   |
| -------------------- | ------ | ----------------------------- |
| 1.1 Project Setup    | 0.5d   | Directory structure           |
| 1.2 Idea Schema      | 1.5d   | Pydantic models + validation  |
| 1.3 Detection Engine | 2d     | Pattern matching + extraction |
| 1.4 Storage Layer    | 2d     | JSONL + git integration       |
| 1.5 CLI collect      | 1.5d   | Working collect command       |

**Success Criteria**:

- ✅ Schema validates all fields
- ✅ Detector ≥95% accurate on explicit ideas
- ✅ Ideas persist to JSONL with git commits
- ✅ `thegent ideas collect` works end-to-end
- ✅ Phase 1 tests pass (≥90% coverage)

---

### Phase 2: Indexing & Search (Week 2, 6 days)

**Deliverable**: Ideas searchable and filterable via CLI

| Task                 | Effort | Deliverable                   |
| -------------------- | ------ | ----------------------------- |
| 2.1 Full-Text Index  | 1.5d   | Inverted index, <100ms search |
| 2.2 Metadata Indices | 1d     | Date, tag, project filtering  |
| 2.3 Query Engine     | 2d     | Search, sort, paginate        |
| 2.4 Search/list/get  | 1.5d   | Three CLI commands            |

**Success Criteria**:

- ✅ Search <100ms for 1000+ ideas
- ✅ Filtering works (tag, date, project)
- ✅ Sorting by relevance/date works
- ✅ All search commands functional
- ✅ Phase 2 tests pass (≥90% coverage)

---

### Phase 3: MCP Integration (Week 3, 4 days)

**Deliverable**: Agents can discover and access ideas

| Task                   | Effort | Deliverable             |
| ---------------------- | ------ | ----------------------- |
| 3.1 MCP Tools          | 1.5d   | 4 tools implemented     |
| 3.2 Server Integration | 1.5d   | Registered with FastMCP |
| 3.3 MCP Resources      | 1d     | Resources exposed       |

**Success Criteria**:

- ✅ All 4 tools functional
- ✅ All 4 resources accessible
- ✅ Agent tests pass
- ✅ Phase 3 tests pass (≥90% coverage)

---

### Phase 4: Polish & Documentation (Week 4, 9.5 days)

**Deliverable**: Production-ready, tested, documented system

| Task                  | Effort | Deliverable                  |
| --------------------- | ------ | ---------------------------- |
| 4.1 Export            | 1.5d   | JSON, Markdown, CSV export   |
| 4.2 Test Suite        | 3d     | ≥85% coverage, all scenarios |
| 4.3 Documentation     | 1.5d   | User guide + API docs        |
| 4.4 Integration Tests | 1d     | E2E workflows                |
| 4.5 Hook Integration  | 1d     | UserPromptSubmit hook        |
| 4.6 Performance       | 1.5d   | Benchmarks + optimization    |

**Success Criteria**:

- ✅ All tests pass (≥85% coverage)
- ✅ Documentation complete
- ✅ Performance targets met
- ✅ Hook working automatically
- ✅ Production-ready

---

## 📊 Implementation Details

### Task Breakdown

**Phase 1 Tasks**:

1.1 **Project Setup** (0.5 days)

- Create `src/thegent/ideas/` directory
- Create `.thegent/ideas/` user data directory
- Add CLI entry point
- Setup `.gitignore`

  1.2 **Idea Schema** (1.5 days)

- Pydantic models for IdeaObject, IdeaSource, DetectionMeta
- Validation: length (50-5000 chars), format checks
- Checksum calculation (SHA-256)
- Serialization/deserialization
- ≥90% test coverage

  1.3 **Detection Engine** (2 days)

- Explicit pattern matching ($idea flag)
- 7+ implicit patterns (what if, new idea, etc.)
- Confidence scoring (0.70-0.99)
- Metadata extraction (source, timestamp, context)
- Duplicate detection (text hash + fuzzy)
- Validation + error handling
- ≥90% test coverage

  1.4 **Storage Layer** (2 days)

- JSONL write/read (append-only)
- Fsync for durability
- Git integration (commit with metadata)
- Checksum verification
- Error handling
- Recovery capability
- ≥90% test coverage

  1.5 **CLI collect** (1.5 days)

- Command group `thegent ideas`
- Subcommand `collect` with `--since` option
- Session discovery integration
- Progress reporting
- Error handling
- Integration tests

**Phase 2 Tasks**:

2.1 **Full-Text Index** (1.5 days)

- Tokenizer (lowercase, stopword removal)
- Inverted index structure
- Index building + persistence
- Search execution (<100ms)
- Performance benchmarks
- ≥90% test coverage

  2.2 **Metadata Indices** (1 day)

- Date index (YYYY-MM-DD → ids)
- Tag index (tag → ids)
- Project index (project → ids)
- Status index (status → ids)
- Index persistence + update logic
- ≥90% test coverage

  2.3 **Query Engine** (2 days)

- Query parser (tokenize, handle quotes)
- Full-text search + filtering
- Sorting (relevance, date, tag)
- Pagination (limit, offset)
- Result scoring (TF-IDF)
- Integration tests

  2.4 **Search/list/get** (1.5 days)

- `ideas search` command
- `ideas list` command
- `ideas get` command
- Output formatting (table, JSON, CSV)
- Pagination options
- Integration tests

**Phase 3 Tasks**:

3.1 **MCP Tools** (1.5 days)

- Implement 4 tools with input schemas
- Error handling
- Response formatting
- Tool tests

  3.2 **Server Integration** (1.5 days)

- Register tools with FastMCP
- Add to MCP manifest
- Implement resources
- Resource tests

  3.3 **MCP Resources** (1 day)

- `thegent://ideas`
- `thegent://ideas/{id}`
- `thegent://ideas/recent`
- `thegent://ideas/by-tag/{tag}`
- Resource tests

**Phase 4 Tasks**:

4.1 **Export** (1.5 days)

- JSON export
- Markdown export (formatted list)
- CSV export (tabular)
- Filtering + export command
- Export tests

  4.2 **Test Suite** (3 days)

- Unit tests: schema, detector, storage, index, query
- CLI tests: all commands
- MCP tool tests
- Export tests
- ≥85% coverage verification

  4.3 **Documentation** (1.5 days)

- User guide (how to flag ideas, examples)
- CLI reference (all commands)
- API docstrings (Google style)
- MCP documentation
- FAQ section

  4.4 **Integration Tests** (1 day)

- End-to-end workflows
- Real prompt examples
- Git recovery scenarios
- Performance testing

  4.5 **Hook Integration** (1 day)

- Create `hooks/idea-seed-detector.sh`
- Hook registry entry
- Automatic detection on UserPromptSubmit
- Configuration options

  4.6 **Performance** (1.5 days)

- Benchmark detection (<10ms)
- Benchmark storage (<50ms)
- Benchmark search (<100ms)
- Benchmark export (<500ms)
- Optimize indices
- Performance metrics/logging

---

## 📁 File Structure

### Source Code

```
src/thegent/ideas/
├── __init__.py              # Package, exports
├── schema.py                # Pydantic models, validation
├── detector.py              # Pattern matching, extraction
├── storage.py               # JSONL persistence
├── git.py                   # Git audit trail
├── index.py                 # Full-text + metadata indexing
├── query.py                 # Search, filter, sort
├── cli.py                   # CLI commands (collect, list, search, get, export)
├── export.py                # JSON/Markdown/CSV export
└── mcp_tools.py             # MCP tool implementations
```

### Tests

```
tests/ideas/
├── test_schema.py           # Schema validation tests
├── test_detector.py         # Pattern matching tests
├── test_storage.py          # Persistence tests
├── test_git.py              # Git integration tests
├── test_index.py            # Index building/search tests
├── test_query.py            # Query execution tests
├── test_cli.py              # CLI command tests
├── test_export.py           # Export format tests
└── conftest.py              # Pytest fixtures
```

### Documentation

```
docs/
├── guides/
│   └── idea-seeds.md        # User guide
├── reference/
│   └── IDEA_SEEDS_CLI_REFERENCE.md  # CLI reference
└── changes/research-idea-seed-system/
    ├── proposal.md          # Problem + scope
    ├── design.md            # Architecture + design
    ├── tasks.md             # Implementation tasks
    ├── README.md            # Quick start
    └── DEVELOPMENT_WRITEUP.md  # This file
```

---

## 🧪 Quality Standards

### Test Coverage

- **Target**: ≥85% coverage
- **Phase 1**: ≥90% per module
- **Phase 2**: ≥90% per module
- **Phase 3**: ≥90% per module
- **Phase 4**: ≥85% overall

### Code Quality

- **Type Hints**: Every function/class
- **Docstrings**: Google style
- **Line Length**: ≤100 chars
- **Function Length**: <50 lines (soft limit)
- **Class Length**: <200 lines (soft limit)
- **Dependencies**: Zero external (stdlib only)

### Performance Targets

| Operation         | Target | Approach                   |
| ----------------- | ------ | -------------------------- |
| Detect idea       | <10ms  | Pattern matching (no I/O)  |
| Store idea        | <50ms  | Sequential write + fsync   |
| Search 1000 ideas | <100ms | Inverted index (memory)    |
| Full export       | <500ms | Stream writing + buffering |
| Git commit        | <100ms | Batch if needed            |
| Index rebuild     | <1s    | Incremental indexing       |

---

## 🚀 Integration Points

### With Existing Systems

1. **Prompt History Collection System**
   - Broader system for all prompts
   - Idea Seed is focused subset
   - Share git infrastructure

2. **Work Stream & Backlog**
   - Ideas → work items
   - Export ideas → WORK_STREAM.md
   - Track implementation

3. **Session Registry**
   - Link ideas to source sessions
   - Analyze: "which ideas led to implementations?"
   - Enable post-hoc traceability

4. **Hook System**
   - UserPromptSubmit hook detects automatically
   - No user action required
   - Configurable patterns

5. **MCP Server**
   - Register tools with FastMCP
   - Agents discover ideas
   - Enable agent-driven ideation

---

## 📈 Success Metrics

### Functional Metrics

- ✅ Idea detection accuracy ≥95% (explicit)
- ✅ Idea detection accuracy ≥80% (implicit)
- ✅ Search performance <100ms
- ✅ Storage durability (git audit trail)
- ✅ Export completeness (all formats)

### Quality Metrics

- ✅ Test coverage ≥85%
- ✅ Zero bugs in Phase 1 (after testing)
- ✅ Zero performance regressions
- ✅ Zero external dependencies

### User Metrics

- ✅ CLI commands intuitive (≤3 args each)
- ✅ Documentation complete
- ✅ Examples work as documented
- ✅ Error messages helpful

---

## 🔄 Risk & Mitigation

| Risk                              | Likelihood | Impact | Mitigation                               |
| --------------------------------- | ---------- | ------ | ---------------------------------------- |
| Pattern matching false positives  | Medium     | Low    | Configurable patterns, manual override   |
| Storage bloat (many ideas)        | Low        | Low    | Archiving, compression, pruning          |
| Git commit overhead               | Low        | Low    | Batch commits, async writes              |
| Search performance degradation    | Low        | Medium | Caching, incremental indexing            |
| Users forget to flag ideas        | Medium     | Medium | Auto-detection patterns, reminders, docs |
| Ideas not actionable              | Low        | Low    | Export → backlog feature                 |
| Privacy concerns (sensitive data) | Low        | Medium | Redaction options, local-only storage    |

**Mitigation Strategy**: Phase-based delivery with testing at each phase. Risk re-evaluated after each phase.

---

## 📋 Effort Summary

| Phase       | Tasks | Effort        | Actual |
| ----------- | ----- | ------------- | ------ |
| **Phase 1** | 5     | 7.5 days      | —      |
| **Phase 2** | 4     | 6 days        | —      |
| **Phase 3** | 3     | 4 days        | —      |
| **Phase 4** | 6     | 9.5 days      | —      |
| **TOTAL**   | 18    | **26.5 days** | —      |

**Timeline**: 4 weeks at nominal pace (no blockers)

---

## ✅ Acceptance Checklist

### Phase 1 Completion

- [ ] Project structure created
- [ ] Schema implemented and validated
- [ ] Detector with ≥95% accuracy
- [ ] JSONL storage with git audit
- [ ] CLI collect command working
- [ ] Phase 1 tests pass (≥90% coverage)

### Phase 2 Completion

- [ ] Full-text index <100ms search
- [ ] Metadata indices all working
- [ ] Query engine with filtering/sorting
- [ ] Search, list, get commands working
- [ ] Phase 2 tests pass (≥90% coverage)

### Phase 3 Completion

- [ ] All 4 MCP tools functional
- [ ] MCP server integration complete
- [ ] All resources accessible
- [ ] Phase 3 tests pass (≥90% coverage)

### Phase 4 Completion

- [ ] Export to JSON/MD/CSV works
- [ ] Overall test coverage ≥85%
- [ ] Documentation complete
- [ ] E2E integration tests passing
- [ ] Hook integration working
- [ ] All performance targets met
- [ ] Production-ready

### Overall Goals

- [ ] Zero external library dependencies
- [ ] Backward compatible with existing CLI
- [ ] Works on macOS, Linux, Windows
- [ ] Git recovery capability verified
- [ ] Performance benchmarks documented

---

## 🎬 Getting Started

### For Reviewers

1. Read: Executive Summary (above)
2. Skim: Architecture section
3. Review: Risk & Mitigation
4. Decision: Approve/Request Changes

### For Architects

1. Read: Full document
2. Review: System Architecture section
3. Review: Integration Points section
4. Provide: Architectural approval

### For Implementers

1. Read: All sections
2. Start: Phase 1 Task 1.1 (Project Setup)
3. Follow: Task breakdown in each phase
4. Track: Actual vs. estimated effort

### For QA/Testers

1. Read: Quality Standards section
2. Review: Test coverage targets
3. Plan: Test cases for each phase
4. Verify: Acceptance criteria

---

## 📞 Questions & Support

| Question                      | Answer Source                 |
| ----------------------------- | ----------------------------- |
| **What is the problem?**      | Problem Statement section     |
| **How will we solve it?**     | Solution Overview section     |
| **What's the architecture?**  | System Architecture section   |
| **How do we detect ideas?**   | Detection Algorithm section   |
| **How are ideas stored?**     | Persistence Strategy section  |
| **How do we find ideas?**     | Search & Indexing section     |
| **What commands exist?**      | CLI Interface section         |
| **How do agents use ideas?**  | MCP Integration section       |
| **What's the timeline?**      | Implementation Phases section |
| **What's the effort?**        | Effort Summary section        |
| **What could go wrong?**      | Risk & Mitigation section     |
| **How do we verify success?** | Acceptance Checklist section  |

---

## 📚 Related Documents

- **proposal.md** - Detailed problem statement + scope
- **design.md** - Technical architecture + specifications
- **tasks.md** - Implementation tasks with dependencies
- **README.md** - Quick reference + examples
- **INDEX.md** - Navigation guide
- [Prompt History Collection System](../../plans/PROMPT_HISTORY_COLLECTION_AND_AUDIT_SYSTEM.md)
- [Work Stream](../../reference/WORK_STREAM.md)

---

## 🏁 Conclusion

The **Idea Seed Detection & Storage System** is a focused, high-value feature that solves a real problem: preserving valuable ideas that emerge during development.

**Key Success Factors**:

1. **Pattern-based detection** - Captures both explicit (`$idea`) and implicit ideas
2. **Simple storage** - JSONL + git = durable, auditable, recoverable
3. **Fast search** - Full-text indexing for <100ms queries
4. **Dual interface** - CLI for humans, MCP for agents
5. **Zero dependencies** - Standalone, easy to maintain

**4-week implementation** with phased delivery enables rapid iteration and testing. All components use Python stdlib only, ensuring easy deployment and minimal maintenance.

---

**Document Status**: Ready for Implementation
**Last Updated**: 2026-02-16
**Next Phase**: Phase 1 Implementation (Project Setup → Detection → Storage)
**Target Completion**: 2026-03-16 (4 weeks)
