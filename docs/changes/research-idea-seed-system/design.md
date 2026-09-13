# Research-Idea-Seed-System: Design

> **Status**: Complete | **Date**: 2026-02-16
> **Document Purpose**: Technical architecture and implementation design
> **Audience**: Implementers, architects

---

## 1. System Architecture

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Claude Code / Codex / Cursor Sessions                       │
│ (User prompts containing $idea flag or implicit patterns)   │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ thegent Hook System (UserPromptSubmit)                      │
│ - Intercepts prompts during processing                      │
│ - Passes to idea detection system                           │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ Idea Detection Engine                                        │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ 1. Pattern Matcher                                   │   │
│ │    - Regex: /\$idea:\s*(.+?)(?=\$|$)/i             │   │
│ │    - Implicit patterns:                             │   │
│ │      - \"New idea:\", \"Idea:\", \"I'm thinking...\"│   │
│ │      - \"What if we\", \"Consider:\", \"Concept:\"  │   │
│ │    - Returns: (matched, text, confidence)           │   │
│ └──────────────────────────────────────────────────────┘   │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ 2. Metadata Extractor                                │   │
│ │    - Source: session_id, timestamp, workspace        │   │
│ │    - Context: preceding text (128 chars)             │   │
│ │    - Tags: auto-detected or user-provided            │   │
│ └──────────────────────────────────────────────────────┘   │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ 3. Validator                                         │   │
│ │    - Schema check (required fields)                  │   │
│ │    - Deduplication (exact text match)                │   │
│ │    - Length check (50-5000 chars)                    │   │
│ └──────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ Storage Layer                                                │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ Primary: JSONL (.thegent/ideas/ideas.jsonl)         │   │
│ │ - Append-only log of all ideas                       │   │
│ │ - One JSON object per line                           │   │
│ │ - Full history preserved                             │   │
│ └──────────────────────────────────────────────────────┘   │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ Audit: Daily snapshots (.thegent/ideas/audit/)      │   │
│ │ - ideas_YYYYMMDD.jsonl (daily snapshots)             │   │
│ │ - audit_index.json (file index + checksums)          │   │
│ └──────────────────────────────────────────────────────┘   │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ Git Integration                                      │   │
│ │ - Auto-commit after each new idea                    │   │
│ │ - Commit msg: \"idea: [idea_id] [short text]\"       │   │
│ │ - Full versioning + recovery                         │   │
│ └──────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         ↓\n┌─────────────────────────────────────────────────────────────┐\n│ Indexing Layer (In-Memory or On-Disk)                      │\n│ ┌──────────────────────────────────────────────────────┐   │\n│ │ Full-Text Index                                      │   │\n│ │ - Inverted index (word → idea IDs)                   │   │\n│ │ - Tokenization: lowercase, remove stopwords          │   │\n│ │ - Updated on each new idea                           │   │\n│ └──────────────────────────────────────────────────────┘   │\n│ ┌──────────────────────────────────────────────────────┐   │\n│ │ Metadata Index                                       │   │\n│ │ - date_index: idea_id → timestamp                    │   │\n│ │ - tag_index: tag → [idea_ids]                        │   │\n│ │ - project_index: project → [idea_ids]                │   │\n│ └──────────────────────────────────────────────────────┘   │\n└────────────────────────┬────────────────────────────────────┘\n                         ↓\n┌─────────────────────────────────────────────────────────────┐\n│ Query & Access Layer                                         │\n│ ┌──────────────────────────────────────────────────────┐   │\n│ │ CLI Commands                                         │   │\n│ │ - ideas collect [--since TIME]                       │   │\n│ │ - ideas list [--limit N] [--tag TAG]                 │   │\n│ │ - ideas search QUERY [--tag TAG] [--since TIME]      │   │\n│ │ - ideas export [--format json|md|csv]                │   │\n│ │ - ideas get ID                                       │   │\n│ └──────────────────────────────────────────────────────┘   │\n│ ┌──────────────────────────────────────────────────────┐   │\n│ │ MCP Tools                                            │   │\n│ │ - thegent_idea_collect()                             │   │\n│ │ - thegent_idea_search(query)                         │   │\n│ │ - thegent_idea_get(id)                               │   │\n│ │ - thegent_idea_list([limit, tag, since])             │   │\n│ └──────────────────────────────────────────────────────┘   │\n│ ┌──────────────────────────────────────────────────────┐   │\n│ │ MCP Resources                                        │   │\n│ │ - thegent://ideas                                    │   │\n│ │ - thegent://ideas/{id}                               │   │\n│ │ - thegent://ideas/recent                             │   │
│ └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Data Schema

### 2.1 Idea Object (Canonical)

```json
{
  "id": "idea_20260216_143022_abc123",
  "text": "Add lazy-loading to DAG compiler for faster feedback loop",
  "created_at": "2026-02-16T14:30:22Z",
  "source": {
    "type": "claude|cursor|codex",
    "session_id": "session_abc123",
    "prompt_index": 42,
    "workspace": "/path/to/project"
  },
  "detection": {
    "method": "explicit|implicit",
    "pattern": "$idea|new_idea|what_if",
    "confidence": 0.95
  },
  "tags": ["performance", "compiler", "dax"],
  "context": "Previous discussion about DAG compilation times...",
  "metadata": {
    "project": "thegent",
    "status": "seed",
    "linked_work_items": [],
    "implementation_count": 0
  },
  "git": {
    "commit_hash": "abc123def456",
    "branch": "main",
    "timestamp": "2026-02-16T14:30:25Z"
  },
  "checksum": "sha256:abc123..."
}
```

### 2.2 JSONL Storage Format

```jsonl
{"id":"idea_20260216_143022_abc123","text":"Add lazy-loading...","created_at":"2026-02-16T14:30:22Z",...}
{"id":"idea_20260216_144500_xyz789","text":"Implement cache invalidation...","created_at":"2026-02-16T14:45:00Z",...}
...
```

### 2.3 Directory Structure

```
.thegent/
├── ideas/
│   ├── ideas.jsonl                  # Master log (append-only)
│   ├── ideas.index.json             # Quick lookup index
│   ├── audit/
│   │   ├── 2026/
│   │   │   └── 02/
│   │   │       ├── ideas_20260216.jsonl  # Daily snapshot
│   │   │       └── ideas_20260217.jsonl
│   │   └── index.json               # Audit index + checksums
│   ├── export/                      # Cached exports
│   │   ├── ideas.md                 # Latest markdown export
│   │   ├── ideas.json               # Latest JSON export
│   │   └── ideas.csv                # Latest CSV export
│   └── .gitignore                   # Git ignore patterns
```

---

## 3. Detection Algorithm

### 3.1 Pattern Matching

**Explicit Detection** (Flag-based):
```python
# Regex pattern for $idea flag
EXPLICIT_PATTERN = r"\$idea:\s*(.+?)(?=\$|$)"

# Example: "$idea: Add caching layer for faster queries"
# Extracts: "Add caching layer for faster queries"
```

**Implicit Detection** (Heuristic-based):
```python
IMPLICIT_PATTERNS = [
    r"new idea:\s*(.+?)(?:\n|$)",  # "New idea: ..."
    r"idea:\s*(.+?)(?:\n|$)",  # "Idea: ..."
    r"what if we\s+(.+?)(?:\n|$)",  # "What if we ..."
    r"consider(?:ing)?:\s*(.+?)(?:\n|$)",  # "Consider: ..."
    r"concept:\s*(.+?)(?:\n|$)",  # "Concept: ..."
    r"i[\'m ]*thinking\s+about\s+(.+?)(?:\n|$)",  # "I'm thinking about ..."
    r"(?:proposal|vision|roadmap):\s*(.+?)(?:\n|$)",
]
```

**Confidence Scoring**:
- Explicit flag: confidence = 0.99 (user intent is clear)
- Implicit patterns: confidence = 0.7-0.9 (based on pattern specificity)
- Manual override: user can set confidence to 1.0 or 0.0

### 3.2 Detection Workflow

```
1. Receive: User prompt text
2. Tokenize: Split by sentences/paragraphs
3. Match Explicit: Check for $idea flag
   - If found: Extract, set confidence=0.99
4. Match Implicit: Check regex patterns
   - For each pattern: Extract if match, assign confidence
5. Dedup Check: Hash text, compare with existing ideas
   - If exact match exists: Skip (already stored)
   - If similar (>90%): Flag for review
6. Validate: Check schema
   - Text length: 50-5000 chars
   - Required fields: text, created_at, source
   - Optional fields: tags, context
7. Extract Metadata:
   - Source: from session context
   - Tags: auto-detect (lowercase 1-3 word phrases)
   - Context: preceding 128 chars
8. Store: Write to JSONL + git commit
9. Index: Update full-text + metadata indices
10. Return: Idea ID + metadata
```

---

## 4. Storage & Persistence

### 4.1 JSONL Append-Only Log

**Design Rationale**:
- Simple, human-readable format
- Efficient append (tail to file)
- Natural git compatibility
- Enables audit trail (one line per idea)
- Easily parseable by tools/scripts

**Write Process**:
```python
def store_idea(idea: IdeaObject, path: str) -> str:
    """
    1. Serialize idea to JSON
    2. Append newline + JSON to ideas.jsonl
    3. Fsync for durability
    4. Create git commit
    5. Update indices
    6. Return idea ID
    """
    json_line = json.dumps(idea.to_dict()) + "\n"
    with open(path + "/ideas.jsonl", "a") as f:
        f.write(json_line)
        f.flush()
        os.fsync(f.fileno())

    git_commit(f"idea: {idea.id} {idea.text[:50]}")
    update_indices(idea)
    return idea.id
```

### 4.2 Git Integration

**Commit Strategy**:
- One commit per idea (immediate, not batched)
- Commit message: `idea: {id} {short_text}`
- Metadata: idea ID in commit body
- Tags: optional git tag for significant ideas

**Audit Trail**:
- Full history via `git log .thegent/ideas/`
- Recover any past version: `git show <commit>:.thegent/ideas/ideas.jsonl`
- Integrity check: `git fsck --full`

**Example Commit**:
```
commit abc123def456
Author: thegent <system@thegent.local>
Date:   Mon Feb 16 14:30:25 2026 +0000

    idea: idea_20260216_143022_abc123 Add lazy-loading to DAG compiler

    source: session_abc123
    tags: performance, compiler, dax
    confidence: 0.99
```

### 4.3 Checksum & Integrity

**SHA-256 Checksums**:
- Hash of idea JSON object
- Stored in `checksum` field
- Verify on read: `sha256(idea_json) == idea.checksum`

**Deduplication**:
- Hash of idea text
- Check against existing: `text_hash in dedup_index`
- Prevent exact duplicates

---

## 5. Indexing Strategy

### 5.1 Full-Text Index

**Implementation** (Python):
```python
class FullTextIndex:
    def __init__(self):
        self.inverted_index = {}  # word → [idea_ids]
        self.doc_freqs = {}  # word → count

    def index_idea(self, idea: IdeaObject):
        """Add idea to full-text index."""
        tokens = tokenize(idea.text.lower())
        for token in tokens:
            if token not in stopwords:
                self.inverted_index.setdefault(token, [])
                self.inverted_index[token].append(idea.id)

    def search(self, query: str) -> List[str]:
        """Search index, return matching idea IDs."""
        tokens = tokenize(query.lower())
        results = self.inverted_index.get(tokens[0], [])
        for token in tokens[1:]:
            results = [id for id in results if id in self.inverted_index.get(token, [])]
        return results
```

**Index File** (`.thegent/ideas/ideas.index.json`):
```json
{
  "version": "1.0",
  "timestamp": "2026-02-16T14:30:25Z",
  "word_count": 1234,
  "idea_count": 156,
  "inverted_index": {
    "lazy": ["idea_1", "idea_45", "idea_78"],
    "loading": ["idea_1", "idea_23"],
    "compiler": ["idea_1", "idea_56", "idea_89"],
    ...
  }
}
```

### 5.2 Metadata Indices

```json
{
  "date_index": {
    "2026-02-16": ["idea_1", "idea_2", "idea_3"],
    "2026-02-17": ["idea_4", "idea_5"]
  },
  "tag_index": {
    "performance": ["idea_1", "idea_5", "idea_23"],
    "compiler": ["idea_1", "idea_45"],
    "dax": ["idea_1"]
  },
  "project_index": {
    "thegent": ["idea_1", "idea_2", ...],
    "atoms": ["idea_10", "idea_11", ...]
  },
  "status_index": {
    "seed": ["idea_1", "idea_2", ...],
    "implemented": ["idea_50", "idea_51", ...]
  }
}
```

---

## 6. Query Language & Search

### 6.1 Search Syntax

**Simple Search**:
```bash
thegent ideas search "lazy loading"
# Finds ideas matching all words: lazy AND loading
```

**Tag Filtering**:
```bash
thegent ideas search "cache" --tag performance
# Finds ideas matching "cache" tagged with "performance"
```

**Date Range**:
```bash
thegent ideas search "api" --since 1w
# Finds ideas matching "api" from last 7 days
```

**Multiple Filters**:
```bash
thegent ideas search "design" --tag architecture --since 2w --limit 5
# Find 5 most recent ideas matching "design" with tag "architecture" from last 2 weeks
```

### 6.2 Query Processing

```python
def execute_query(query_string: str, filters: Dict) -> List[IdeaObject]:
    """
    1. Parse query string (tokenize, handle quotes)
    2. Search full-text index for matching idea IDs
    3. Apply metadata filters:
       - date: filter by timestamp range
       - tag: filter by tags (AND logic)
       - project: filter by project
    4. Sort by relevance (tf-idf) or date
    5. Paginate (limit, offset)
    6. Return idea objects
    """
    # Pseudo-code:
    matching_ids = full_text_search(query_string)
    for idea_id in matching_ids:
        idea = load_idea(idea_id)
        if matches_all_filters(idea, filters):
            yield idea
```

---

## 7. CLI Interface

### 7.1 Command Reference

#### `thegent ideas collect`
Collect ideas from current or recent sessions.

```bash
# Collect all recent ideas
$ thegent ideas collect

# Collect from specific time range
$ thegent ideas collect --since 24h

# Collect with git commit
$ thegent ideas collect --git-commit
```

#### `thegent ideas list`
List ideas with optional filtering.

```bash
# List all ideas
$ thegent ideas list

# List recent ideas (limit 10)
$ thegent ideas list --limit 10

# List ideas by tag
$ thegent ideas list --tag performance

# List with details
$ thegent ideas list --verbose

# List and export to file
$ thegent ideas list --output ideas.json
```

#### `thegent ideas search`
Full-text search ideas.

```bash
# Simple search
$ thegent ideas search "lazy loading"

# Search with tag filter
$ thegent ideas search "api" --tag design

# Search with date range
$ thegent ideas search "algorithm" --since 1w --until now

# Search with pagination
$ thegent ideas search "feature" --limit 5 --offset 0

# Search output format
$ thegent ideas search "cache" --format json
$ thegent ideas search "cache" --format csv
```

#### `thegent ideas get`
Retrieve specific idea by ID.

```bash
# Get idea by ID
$ thegent ideas get idea_20260216_143022_abc123

# Get with full details
$ thegent ideas get idea_20260216_143022_abc123 --verbose

# Get as JSON
$ thegent ideas get idea_20260216_143022_abc123 --format json
```

#### `thegent ideas export`
Export ideas to various formats.

```bash
# Export to JSON
$ thegent ideas export --format json --output ideas.json

# Export to Markdown
$ thegent ideas export --format markdown --output ideas.md

# Export to CSV
$ thegent ideas export --format csv --output ideas.csv

# Export with filters
$ thegent ideas export --format json --tag performance --since 1w
```

---

## 8. MCP Integration

### 8.1 MCP Tools

#### `thegent_idea_collect`
Collect ideas from sessions.

```json
{
  "name": "thegent_idea_collect",
  "description": "Collect ideas from Claude/Cursor/Codex sessions",
  "inputSchema": {
    "type": "object",
    "properties": {
      "since": {
        "type": "string",
        "description": "Time range (e.g., '6h', '1d', '1w')",
        "default": "6h"
      },
      "git_commit": {
        "type": "boolean",
        "description": "Create git commit for collected ideas",
        "default": false
      }
    }
  }
}
```

**Response**:
```json
{
  "status": "success",
  "collected": 5,
  "ideas": [
    {
      "id": "idea_20260216_143022_abc123",
      "text": "Add lazy-loading to DAG compiler...",
      "created_at": "2026-02-16T14:30:22Z",
      "tags": ["performance", "compiler"]
    },
    ...
  ]
}
```

#### `thegent_idea_search`
Search ideas.

```json
{
  "name": "thegent_idea_search",
  "description": "Search collected ideas",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Search query"
      },
      "tag": {
        "type": "string",
        "description": "Filter by tag"
      },
      "since": {
        "type": "string",
        "description": "Time range"
      },
      "limit": {
        "type": "integer",
        "description": "Max results",
        "default": 10
      }
    },
    "required": ["query"]
  }
}
```

#### `thegent_idea_get`
Get specific idea.

```json
{
  "name": "thegent_idea_get",
  "description": "Retrieve idea by ID",
  "inputSchema": {
    "type": "object",
    "properties": {
      "id": {
        "type": "string",
        "description": "Idea ID"
      }
    },
    "required": ["id"]
  }
}
```

#### `thegent_idea_list`
List ideas.

```json
{
  "name": "thegent_idea_list",
  "description": "List ideas with optional filters",
  "inputSchema": {
    "type": "object",
    "properties": {
      "tag": {
        "type": "string",
        "description": "Filter by tag"
      },
      "since": {
        "type": "string",
        "description": "Time range"
      },
      "limit": {
        "type": "integer",
        "description": "Max results",
        "default": 10
      }
    }
  }
}
```

### 8.2 MCP Resources

```
thegent://ideas
  - List all ideas (paginated)

thegent://ideas/{id}
  - Get specific idea

thegent://ideas/recent
  - Get 10 most recent ideas

thegent://ideas/by-tag/{tag}
  - Get ideas with specific tag
```

---

## 9. Hook Integration

### 9.1 UserPromptSubmit Hook

**Location**: `hooks/idea-seed-detector.sh`

```bash
#!/bin/bash
# Hook: UserPromptSubmit event
# Purpose: Detect and store ideas from user prompts

PROMPT="$1"      # User prompt text
SESSION_ID="$2"  # Current session ID
WORKSPACE="$3"   # Current workspace

# Call detection system (Python)
thegent ideas collect --from-prompt "$PROMPT" \
    --session "$SESSION_ID" \
    --workspace "$WORKSPACE"

# Exit with status
exit $?
```

**Trigger**: After user submits prompt, before it's sent to model

---

## 10. Performance Targets

| Operation | Target | Approach |
|-----------|--------|----------|
| **Detect idea** | <10ms | Pattern matching (no I/O) |
| **Store idea** | <50ms | Sequential write + fsync |
| **Search 1000 ideas** | <100ms | Inverted index (no disk I/O) |
| **Full export** | <500ms | Stream writing + buffering |
| **Git commit** | <100ms | Batch commits if needed |
| **Index rebuild** | <1s | Incremental indexing |

---

## 11. Error Handling

### 11.1 Detection Errors

```python
class DetectionError(Exception):
    """Base detection error."""

    pass


class InvalidIdeaError(DetectionError):
    """Idea doesn't meet minimum requirements."""

    # Too short, invalid schema, etc.


class DuplicateIdeaError(DetectionError):
    """Idea already exists."""

    # User can choose to skip or merge


class PatternMatchError(DetectionError):
    """Pattern matching failed."""

    # Log and continue
```

### 11.2 Storage Errors

```python
class StorageError(Exception):
    """Base storage error."""

    pass


class WriteError(StorageError):
    """Failed to write to JSONL."""

    # Retry with backoff


class GitError(StorageError):
    """Git operation failed."""

    # Abort, notify user


class ChecksumError(StorageError):
    """Checksum mismatch on read."""

    # Data corruption, abort
```

---

## 12. Extensibility

### 12.1 Custom Detection Patterns

Users can add custom patterns to `~/.claude/idea-patterns.yaml`:

```yaml
patterns:
  custom_flag:
    pattern: '@ideate:\s*(.+?)(?=@|$)'
    confidence: 0.95

  brainstorm:
    pattern: 'brainstorm[ing]*:\s*(.+?)(?:\n|$)'
    confidence: 0.85
```

### 12.2 Plugin System

Allow plugins to hook into idea detection:

```python
# plugins/custom_detector.py
def detect_ideas(prompt: str) -> List[IdeaObject]:
    """Custom detection logic."""
    ideas = []
    # Custom detection...
    return ideas


register_detector(detect_ideas)
```

---

**Design Document Status**: Complete
**Last Updated**: 2026-02-16
**Next Phase**: Implementation Tasks
