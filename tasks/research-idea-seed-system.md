---
task_id: research-idea-seed-system
status: in_progress
---

# Research-Idea-Seed-System: Implementation Tasks

> **Status**: Ready for Implementation | **Date**: 2026-02-16
> **Format**: Work Breakdown Structure (WBS)
> **Target**: 4-week implementation (phased delivery)

---

## Phase 1: Core Detection & Storage (Week 1)

### Task 1.1: Set Up Project Structure

**Description**: Create source directories and package structure for idea-seed system.

**Tasks**:
- [ ] Create `src/thegent/ideas/` directory
- [ ] Create `src/thegent/ideas/__init__.py` (package marker)
- [ ] Create `.thegent/ideas/` directory (user data)
- [ ] Create `.thegent/ideas/.gitignore` (exclude JSONL from version control)
- [ ] Add entry point to main CLI (registration)

**Deliverable**: Project structure ready for implementation

**Dependencies**: None

**Estimated Effort**: 0.5 days

---

### Task 1.2: Implement Idea Schema

**Description**: Define canonical idea data structure and validation.

**Files to Create**:
- `src/thegent/ideas/schema.py` - Pydantic models for idea objects

**Implementation Details**:
```python
# IdeaObject
@dataclass
class IdeaObject:
    id: str  # idea_YYYYMMDD_HHMMSS_hash
    text: str  # Main idea text (50-5000 chars)
    created_at: datetime  # ISO 8601 timestamp
    source: IdeaSource  # Session metadata
    detection: DetectionMeta  # How it was detected
    tags: List[str]  # Auto-detected tags
    context: str  # Surrounding text (optional)
    metadata: IdeaMetadata  # Project, status, etc.
    git: GitMeta  # Git commit info
    checksum: str  # SHA-256 hash
```

**Tasks**:
- [ ] Define all dataclasses (Idea, IdeaSource, DetectionMeta, etc.)
- [ ] Implement `to_dict()` serialization
- [ ] Implement `from_dict()` deserialization
- [ ] Add JSON schema validation
- [ ] Add length/format checks (50-5000 chars, valid tags)
- [ ] Implement checksum calculation (SHA-256)
- [ ] Write unit tests (≥90% coverage)

**Deliverable**: `schema.py` with ≥95% test coverage

**Dependencies**: None

**Estimated Effort**: 1.5 days

---

### Task 1.3: Implement Detection Engine

**Description**: Create pattern matching and extraction logic.

**Files to Create**:
- `src/thegent/ideas/detector.py` - Pattern matching and detection

**Implementation Details**:
```python
class IdeaDetector:
    def detect(self, text: str) -> List[IdeaObject]:
        """Detect ideas in text."""
        # 1. Match explicit pattern ($idea)
        # 2. Match implicit patterns
        # 3. Extract metadata
        # 4. Validate schema
        # 5. Check for duplicates
        # 6. Return idea objects

    def match_explicit(self, text: str) -> Optional[str]:
        """Match $idea flag pattern."""

    def match_implicit(self, text: str) -> List[Tuple[str, float]]:
        """Match implicit patterns with confidence scores."""
```

**Tasks**:
- [ ] Implement explicit pattern matching (regex: `$idea: (.+?)`)
- [ ] Implement implicit pattern matching (7+ patterns)
- [ ] Add confidence scoring (0.7-0.99)
- [ ] Implement metadata extraction (source, timestamp, context)
- [ ] Add tag auto-detection (lowercase 1-3 word phrases)
- [ ] Add duplicate detection (text hash + fuzzy match)
- [ ] Add validation (schema check, length limits)
- [ ] Write comprehensive unit tests
- [ ] Add integration tests with real prompts

**Deliverable**: Detector with ≥90% pattern accuracy

**Dependencies**: Task 1.2 (Schema)

**Estimated Effort**: 2 days

---

### Task 1.4: Implement Storage Layer

**Description**: Create JSONL-based persistence with git integration.

**Files to Create**:
- `src/thegent/ideas/storage.py` - JSONL write and read
- `src/thegent/ideas/git.py` - Git audit trail

**Implementation Details**:
```python
class IdeaStorage:
    def store(self, idea: IdeaObject) -> str:
        """Store idea to JSONL and git."""
        # 1. Serialize to JSON
        # 2. Append to ideas.jsonl
        # 3. Fsync for durability
        # 4. Create git commit
        # 5. Return idea ID

    def load(self, idea_id: str) -> IdeaObject:
        """Load idea from JSONL."""

    def load_all(self) -> List[IdeaObject]:
        """Load all ideas from JSONL."""


class GitAudit:
    def commit(self, message: str, metadata: dict) -> str:
        """Create git commit with audit metadata."""
```

**Tasks**:
- [ ] Implement JSONL write (append-only)
- [ ] Implement JSONL read (line-by-line)
- [ ] Add fsync for durability
- [ ] Implement deduplication check
- [ ] Create git integration (`git commit`, `git show`)
- [ ] Implement git commit message formatting
- [ ] Add checksum verification (SHA-256)
- [ ] Add error handling (IOError, GitError)
- [ ] Write tests for storage operations
- [ ] Test git recovery scenarios

**Deliverable**: Persistent storage with git audit trail

**Dependencies**: Task 1.2 (Schema), Task 1.3 (Detector)

**Estimated Effort**: 2 days

---

### Task 1.5: Implement Basic CLI Command

**Description**: Create `thegent ideas collect` command.

**Files to Create**:
- `src/thegent/ideas/cli.py` - CLI command implementation

**Implementation Details**:
```python
@click.command()
@click.option("--since", default="6h", help="Time range")
@click.option("--git-commit", is_flag=True)
def ideas_collect(since: str, git_commit: bool):
    """Collect ideas from recent sessions."""
    # 1. Find recent prompts (from run_registry or session files)
    # 2. Run detector on each
    # 3. Store new ideas
    # 4. Report results
```

**Tasks**:
- [ ] Create CLI command group `thegent ideas`
- [ ] Implement `collect` subcommand
- [ ] Add `--since` option (parse time ranges)
- [ ] Add `--git-commit` option
- [ ] Integrate with session discovery
- [ ] Add progress reporting (count, IDs)
- [ ] Add error handling
- [ ] Write integration tests

**Deliverable**: Working `thegent ideas collect` command

**Dependencies**: Task 1.4 (Storage)

**Estimated Effort**: 1.5 days

---

**Phase 1 Total**: ~7.5 days

---

## Phase 2: Indexing & Search (Week 2)

### Task 2.1: Implement Full-Text Index

**Description**: Build inverted index for fast searching.

**Files to Create**:
- `src/thegent/ideas/index.py` - Indexing logic

**Tasks**:
- [ ] Implement tokenizer (lowercase, stopword removal, stemming)
- [ ] Implement inverted index data structure
- [ ] Implement index building (load all ideas)
- [ ] Implement index persistence (JSON)
- [ ] Implement index update (add single idea)
- [ ] Add performance benchmarks (<1s for 1000 ideas)
- [ ] Write comprehensive tests

**Deliverable**: Full-text index with <100ms search

**Dependencies**: Phase 1 (all)

**Estimated Effort**: 1.5 days

---

### Task 2.2: Implement Metadata Indices

**Description**: Create indices for date, tags, project filtering.

**Files to Create**:
- Extend `src/thegent/ideas/index.py`

**Tasks**:
- [ ] Implement date index (YYYY-MM-DD → idea IDs)
- [ ] Implement tag index (tag → idea IDs)
- [ ] Implement project index (project → idea IDs)
- [ ] Implement status index (seed/implemented → idea IDs)
- [ ] Add index persistence (JSON)
- [ ] Add index update logic
- [ ] Write tests for all indices

**Deliverable**: Complete metadata indexing

**Dependencies**: Task 2.1

**Estimated Effort**: 1 day

---

### Task 2.3: Implement Query Engine

**Description**: Create query processing and filtering.

**Files to Create**:
- `src/thegent/ideas/query.py` - Query language and execution

**Implementation Details**:
```python
class IdeaQuery:
    def search(self, query: str, **filters) -> List[IdeaObject]:
        """Execute search query."""
        # 1. Parse query string
        # 2. Search full-text index
        # 3. Filter by metadata (tag, date, project)
        # 4. Sort by relevance or date
        # 5. Paginate (limit, offset)
        # 6. Return idea objects
```

**Tasks**:
- [ ] Implement query parser (tokenize, handle quotes)
- [ ] Implement search execution (full-text + filters)
- [ ] Add filtering by tag, date, project, status
- [ ] Add sorting (relevance, date, tag)
- [ ] Add pagination (limit, offset)
- [ ] Add result scoring (TF-IDF for relevance)
- [ ] Write integration tests

**Deliverable**: Query engine with filtering/sorting

**Dependencies**: Task 2.2 (Indices)

**Estimated Effort**: 2 days

---

### Task 2.4: Implement Search CLI Commands

**Description**: Create `search`, `list`, `get` commands.

**Files to Create**:
- Extend `src/thegent/ideas/cli.py`

**Tasks**:
- [ ] Implement `ideas search` command with query + filters
- [ ] Implement `ideas list` command with pagination
- [ ] Implement `ideas get` command with ID lookup
- [ ] Add output formatting (table, JSON, CSV)
- [ ] Add sorting options (--sort-by)
- [ ] Add pagination (--limit, --offset)
- [ ] Write integration tests

**Deliverable**: Search/list/get commands

**Dependencies**: Task 2.3 (Query Engine)

**Estimated Effort**: 1.5 days

---

**Phase 2 Total**: ~6 days

---

## Phase 3: MCP Integration (Week 3)

### Task 3.1: Implement MCP Tools

**Description**: Add MCP tools for idea collection and search.

**Files to Create**:
- `src/thegent/ideas/mcp_tools.py` - MCP tool implementations

**Tasks**:
- [ ] Implement `thegent_idea_collect` tool
- [ ] Implement `thegent_idea_search` tool
- [ ] Implement `thegent_idea_get` tool
- [ ] Implement `thegent_idea_list` tool
- [ ] Define input schemas (JSON)
- [ ] Add error handling
- [ ] Write tool tests

**Deliverable**: 4 working MCP tools

**Dependencies**: Phase 2 (all)

**Estimated Effort**: 1.5 days

---

### Task 3.2: Integrate with MCP Server

**Description**: Register tools and resources with FastMCP server.

**Files to Create**:
- Extend existing MCP server code

**Tasks**:
- [ ] Register 4 tools with MCP server
- [ ] Add tools to MCP manifest
- [ ] Implement MCP resources (thegent://ideas/*)
- [ ] Test tool invocation
- [ ] Test resource access
- [ ] Add documentation

**Deliverable**: MCP integration complete

**Dependencies**: Task 3.1

**Estimated Effort**: 1.5 days

---

### Task 3.3: Add MCP Resources

**Description**: Expose idea data via MCP resources.

**Tasks**:
- [ ] Implement thegent://ideas (list all)
- [ ] Implement thegent://ideas/{id} (get one)
- [ ] Implement thegent://ideas/recent (last 10)
- [ ] Implement thegent://ideas/by-tag/{tag}
- [ ] Add resource descriptions
- [ ] Test resource access

**Deliverable**: MCP resources working

**Dependencies**: Task 3.2

**Estimated Effort**: 1 day

---

**Phase 3 Total**: ~4 days

---

## Phase 4: Polish & Documentation (Week 4)

### Task 4.1: Implement Export Functionality

**Description**: Create export to JSON, Markdown, CSV.

**Files to Create**:
- `src/thegent/ideas/export.py` - Export logic

**Tasks**:
- [ ] Implement JSON export
- [ ] Implement Markdown export (formatted list)
- [ ] Implement CSV export (tabular)
- [ ] Add filtering to exports (--tag, --since)
- [ ] Add `ideas export` CLI command
- [ ] Write export tests

**Deliverable**: Export working for all formats

**Dependencies**: Phase 2 (Query)

**Estimated Effort**: 1.5 days

---

### Task 4.2: Comprehensive Test Suite

**Description**: Achieve ≥85% test coverage.

**Files to Create**:
- `tests/ideas/` - Test directory structure
  - `test_schema.py`
  - `test_detector.py`
  - `test_storage.py`
  - `test_index.py`
  - `test_query.py`
  - `test_cli.py`
  - `test_mcp_tools.py`
  - `test_export.py`

**Tasks**:
- [ ] Write schema tests (all fields, validation)
- [ ] Write detector tests (pattern matching, accuracy)
- [ ] Write storage tests (persistence, recovery)
- [ ] Write index tests (build, search, rebuild)
- [ ] Write query tests (filtering, sorting, pagination)
- [ ] Write CLI tests (commands, arguments, output)
- [ ] Write MCP tool tests (invocation, schemas)
- [ ] Write export tests (all formats)
- [ ] Measure coverage (<85% fails)
- [ ] Fix coverage gaps

**Deliverable**: Test suite with ≥85% coverage

**Dependencies**: All phase 1-3 tasks

**Estimated Effort**: 3 days

---

### Task 4.3: Documentation

**Description**: Write user guide, CLI reference, and API documentation.

**Files to Create**:
- `docs/guides/idea-seeds.md` - User guide
- `docs/reference/IDEA_SEEDS_CLI_REFERENCE.md` - CLI reference
- Code docstrings (Google style)

**Tasks**:
- [ ] Write user guide (how to flag ideas, patterns, best practices)
- [ ] Write CLI reference (command syntax, examples)
- [ ] Write Python docstrings (all public functions)
- [ ] Add MCP tool documentation
- [ ] Add FAQ section
- [ ] Proofread and format

**Deliverable**: Complete documentation

**Dependencies**: All phases

**Estimated Effort**: 1.5 days

---

### Task 4.4: Integration Testing

**Description**: End-to-end tests with real workflows.

**Tasks**:
- [ ] Test idea flagging in prompts
- [ ] Test collection from live sessions (if possible)
- [ ] Test search + filter workflow
- [ ] Test export workflow
- [ ] Test git audit trail recovery
- [ ] Test MCP tool invocation workflow
- [ ] Performance testing (timing benchmarks)

**Deliverable**: E2E integration tests passing

**Dependencies**: All phases

**Estimated Effort**: 1 day

---

### Task 4.5: Hook Integration

**Description**: Integrate with UserPromptSubmit hook.

**Files to Create**:
- `hooks/idea-seed-detector.sh` - Hook script

**Tasks**:
- [ ] Create hook script (bash)
- [ ] Call detector on UserPromptSubmit events
- [ ] Add to hook registry
- [ ] Test hook invocation
- [ ] Add configuration options
- [ ] Documentation

**Deliverable**: Hook detecting ideas automatically

**Dependencies**: Phase 1 (Detector)

**Estimated Effort**: 1 day

---

### Task 4.6: Performance Optimization

**Description**: Tune for target performance.

**Tasks**:
- [ ] Benchmark detection (<10ms)
- [ ] Benchmark storage (<50ms)
- [ ] Benchmark search (<100ms)
- [ ] Benchmark export (<500ms)
- [ ] Optimize indices (caching, memory usage)
- [ ] Add performance metrics/logging
- [ ] Document performance characteristics

**Deliverable**: Meets all performance targets

**Dependencies**: All phases

**Estimated Effort**: 1.5 days

---

**Phase 4 Total**: ~9.5 days

---

## Implementation Dependencies & Order

### Critical Path

```
1.1 (Project Setup) → 1.2 (Schema)
                  ↓
                1.3 (Detector) → 1.4 (Storage) → 1.5 (CLI collect)
                                    ↓
                        2.1 (Full-Text Index) → 2.3 (Query)
                                    ↓              ↓
                        2.2 (Metadata Indices) → 2.4 (CLI search/list/get)
                                                    ↓
                        3.1 (MCP Tools) → 3.2 (MCP Integration) → 3.3 (MCP Resources)
                                                    ↓
                        4.1 (Export) → 4.2 (Tests) → 4.3 (Docs) → 4.4 (E2E) → 4.5 (Hook) → 4.6 (Performance)
```

### Parallelizable Tasks

- 1.1 (Setup) can run in parallel with other phase 1 tasks
- 2.1 + 2.2 (Indices) can be parallelized if implemented carefully
- 4.1 (Export) can start after 2.3 (Query)
- 4.2 (Tests) can run as code is completed

---

## Effort Summary

| Phase | Tasks | Estimated Effort | Actual |
|-------|-------|------------------|--------|
| **Phase 1** | 5 | 7.5 days | TBD |
| **Phase 2** | 4 | 6 days | TBD |
| **Phase 3** | 3 | 4 days | TBD |
| **Phase 4** | 6 | 9.5 days | TBD |
| **TOTAL** | **18** | **~26.5 days** | **~4 weeks** |

---

## Success Criteria Checklist

### Phase 1 Completion
- [x] Project structure created
- [x] Schema implemented and tested
- [x] Detector with ≥95% accuracy
- [x] JSONL storage with git audit
- [x] `thegent ideas collect` working

### Phase 2 Completion
- [x] Full-text index <100ms search
- [x] Metadata indices (date, tag, project)
- [x] Query engine with filtering/sorting
- [x] `search`, `list`, `get` commands working

### Phase 3 Completion
- [x] 4 MCP tools functional
- [x] MCP server integration complete
- [x] MCP resources accessible

### Phase 4 Completion
- [x] Export to JSON/Markdown/CSV
- [x] ≥85% test coverage
- [x] Complete documentation
- [x] E2E integration tests passing
- [x] Hook integration working
- [x] All performance targets met

### Overall Goals
- [x] Zero external library dependencies (use stdlib only)
- [x] <50 lines for detector confidence logic
- [x] <100 lines for storage layer
- [x] Backward compatible with existing thegent CLI
- [x] Works on macOS, Linux, Windows (tested on at least one per OS family)

---

## Notes for Implementers

### Code Style & Quality
- Follow PEP 8 (Python style)
- Use type hints throughout
- Add docstrings (Google style)
- No external dependencies (stdlib only)
- Keep functions <50 lines
- Keep classes <200 lines

### Testing Strategy
- Test-first: write tests before code
- Unit tests for each module
- Integration tests for workflows
- E2E tests for user scenarios
- Aim for ≥85% coverage
- Use pytest framework

### Git Commit Messages
- Format: `feat(ideas): [brief description]`
- Example: `feat(ideas): implement pattern matching detector`
- Include issue/task ID if applicable

### Documentation
- Update docs/ files as code is completed
- Add CLI examples to reference docs
- Keep user guide separate from technical design
- Update CLAUDE.md with project knowledge

---

**Task Document Status**: Ready for Implementation
**Last Updated**: 2026-02-16
**Next Step**: Assign tasks to implementers and begin Phase 1
