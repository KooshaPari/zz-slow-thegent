# MAIF Action Artifacts - Phase 1 Implementation

**Status**: ✅ Complete
**Date**: 2026-02-18
**Priority**: P1
**Depends**: WP-3002

## Overview

Phase 1 of MAIF Action Artifacts implements the core foundation for domain-specific artifact types, storage, and APIs. Builds on top of the existing MAIF cryptographic foundation (`src/thegent/maif/`).

## Architecture

```
thegent/artifacts/
├── __init__.py           # Package exports
├── base.py              # BaseArtifact + metadata model
├── code_artifacts.py    # CodeChangeArtifact, FileOperationArtifact
├── tool_artifacts.py    # ToolInvocationArtifact, MCPCallArtifact
├── decision_artifacts.py # DecisionArtifact, BranchingPointArtifact
├── storage.py           # ArtifactStorage interface + MemoryArtifactStorage
├── registry.py          # ArtifactRegistry + factory
├── generators.py        # Specialized generators for each type
└── api.py              # High-level ArtifactAPI
```

## Components

### 1. Base Artifact Class

**File**: `base.py`

Provides foundation extending `MAIFArtifact` with:

- **Artifact Metadata**: Category, tags, dependencies, custom fields
- **Classification**: Organize artifacts by purpose (code, tool, decision)
- **Dependency Tracking**: Link related artifacts
- **Serialization**: Convert to/from dict for storage

```python
from thegent.artifacts import BaseArtifact, ArtifactMetadata, ArtifactCategory

# Create artifact from MAIF
metadata = ArtifactMetadata(
    category=ArtifactCategory.CODE, tags=["refactor", "performance"], dependencies=["artifact-id-1"]
)
artifact = BaseArtifact.from_maif_artifact(maif, category=ArtifactCategory.CODE, metadata=metadata.model_dump())

# Serialize for storage
artifact_dict = artifact.to_dict()

# Retrieve relationships
artifact.add_dependency("artifact-id-2")
artifact.add_tag("critical")
```

### 2. Concrete Artifact Types

#### Code Artifacts (`code_artifacts.py`)

**CodeChangeArtifact**: Track code modifications
- File path and language
- Change type (edit, refactor, bug fix, feature, formatting)
- Affected symbols (functions, classes)
- Test coverage impact
- Lint violations

**FileOperationArtifact**: Track file operations
- Operation type (create, delete, rename, move, copy)
- Source and destination paths
- File metadata (size, permissions)
- Backup information
- Content hashes for integrity

#### Tool Artifacts (`tool_artifacts.py`)

**ToolInvocationArtifact**: Track external tool calls
- Tool type (MCP, API, CLI, subprocess, database)
- Input arguments and parameters
- Execution result and status
- Performance metrics (latency, memory)
- Retry information

**MCPCallArtifact**: Specialized for MCP interactions
- Server and tool names
- Request/response schemas
- Error handling and validation
- Latency and backoff tracking

#### Decision Artifacts (`decision_artifacts.py`)

**DecisionArtifact**: Track agent decisions
- Decision type (routing, resource allocation, strategy, parameter choice, error recovery)
- Options considered and scoring
- Decision criteria and rationale
- Confidence score
- Outcome and feedback

**BranchingPointArtifact**: Track conditional branching
- Condition evaluated
- True/false branch descriptions
- Which branch was taken
- Fallback information

### 3. Storage Layer

**File**: `storage.py`

#### Abstract Interface

```python
class ArtifactStorage(ABC):
    async def store(artifact: BaseArtifact) -> str
    async def retrieve(artifact_id: str) -> Optional[BaseArtifact]
    async def delete(artifact_id: str) -> bool
    async def list_by_session(session_id: str) -> List[BaseArtifact]
    async def list_by_category(category: ArtifactCategory) -> List[BaseArtifact]
    async def list_by_tag(tag: str) -> List[BaseArtifact]
    async def search(query: str) -> List[BaseArtifact]
```

#### In-Memory Implementation

`MemoryArtifactStorage` for Phase 1:
- Stores artifacts in Python dict
- Maintains indices for fast lookup
- Supports queries by session, category, tags
- Full-text search in descriptions and metadata

```python
from thegent.artifacts import MemoryArtifactStorage

storage = MemoryArtifactStorage()
artifact_id = await storage.store(artifact)
retrieved = await storage.retrieve(artifact_id)
session_artifacts = await storage.list_by_session("session-1")
```

### 4. Artifact Registry

**File**: `registry.py`

Central registry for artifact types:

```python
from thegent.artifacts import get_registry

registry = get_registry()

# Get artifact class
CodeChangeClass = registry.get_artifact_class("code_change")

# List all types
types = registry.list_types()
# ['code_change', 'file_operation', 'tool_invocation', 'mcp_call', 'decision', 'branching_point']

# Deserialize artifact
artifact = registry.deserialize(artifact_dict)

# Get types by category
code_types = registry.get_by_category(ArtifactCategory.CODE)
```

### 5. Artifact Generators

**File**: `generators.py`

Specialized factories for creating domain-specific artifacts:

```python
from thegent.artifacts import ArtifactGeneratorFactory
from thegent.maif import SigningKey

signing_key = SigningKey.generate()
maif_generator = MAIFArtifactGenerator(signing_key)
factory = ArtifactGeneratorFactory(maif_generator)

# Create code change
code_artifact = factory.code.create_code_change(
    agent_id="agent-1",
    session_id="session-1",
    file_path="src/main.py",
    change_type=CodeChangeType.FEATURE,
    before_content=b"old code",
    after_content=b"new code",
    language="python",
    tags=["feature", "async"],
)

# Create tool invocation
tool_artifact = factory.tool.create_tool_invocation(
    agent_id="agent-1",
    session_id="session-1",
    tool_type=ToolType.MCP,
    tool_name="file_read",
    arguments={"path": "/path/to/file"},
    result_status=ToolResultStatus.SUCCESS,
    result_output="file contents",
)

# Create decision
decision_artifact = factory.decision.create_decision(
    agent_id="agent-1",
    session_id="session-1",
    decision_type=DecisionType.ROUTING,
    options_considered=["option-a", "option-b"],
    selected_option="option-a",
    rationale="Option A has lower cost",
)
```

### 6. High-Level API

**File**: `api.py`

Unified interface for all artifact operations:

```python
from thegent.artifacts import ArtifactAPI

api = ArtifactAPI(signing_key=signing_key, verifying_key=verifying_key, storage=storage)

# Create and store
artifact = await api.generators.code.create_code_change(...)
artifact_id = await api.store_artifact(artifact)

# Retrieve and verify
artifact = await api.retrieve_artifact(artifact_id)
is_valid = await api.verify_artifact(artifact)

# Verify entire session chain
is_valid, message = await api.verify_session_chain("session-1")

# Query operations
session_artifacts = await api.list_session_artifacts("session-1")
code_artifacts = await api.list_by_category(ArtifactCategory.CODE)
decision_artifacts = await api.list_by_tag("critical")
search_results = await api.search_artifacts("permission denied")

# Dependency tracking
dependency_chain = await api.get_dependency_chain(artifact_id)
related = await api.list_related_artifacts(artifact_id)

# Statistics
stats = await api.get_stats()
```

## Usage Example: Complete Workflow

```python
from thegent.artifacts import ArtifactAPI, CodeChangeType, FileOperationType, ToolType, ToolResultStatus, DecisionType
from thegent.maif import SigningKey

# Initialize
signing_key = SigningKey.generate()
verifying_key = signing_key.get_public_key()
api = ArtifactAPI(signing_key, verifying_key)

# Track a code change
code_artifact = await api.generators.code.create_code_change(
    agent_id="claude-agent",
    session_id="session-abc123",
    file_path="src/utils.py",
    change_type=CodeChangeType.BUG_FIX,
    before_content=open("src/utils.py", "rb").read(),
    after_content=b"fixed version",
    language="python",
    affected_symbols=["parse_config"],
    tags=["bug-fix", "security"],
)
await api.store_artifact(code_artifact)

# Track file operation
file_op = await api.generators.code.create_file_operation(
    agent_id="claude-agent",
    session_id="session-abc123",
    operation_type=FileOperationType.CREATE,
    source_path="src/tests/test_utils.py",
    before_content=b"",
    after_content=b"test code",
)
await api.store_artifact(file_op)

# Track tool call
tool_artifact = await api.generators.tool.create_mcp_call(
    agent_id="claude-agent",
    session_id="session-abc123",
    mcp_server="file_system",
    mcp_tool="read_file",
    call_status=ToolResultStatus.SUCCESS,
    request_parameters={"path": "src/utils.py"},
    input_data=b"",
    output_data=b"file content",
)
await api.store_artifact(tool_artifact)

# Track decision
decision = await api.generators.decision.create_decision(
    agent_id="claude-agent",
    session_id="session-abc123",
    decision_type=DecisionType.STRATEGY_SELECTION,
    options_considered=["quick_fix", "thorough_refactor"],
    selected_option="quick_fix",
    rationale="Priority is correctness, time budget allows thorough testing",
    confidence_score=0.85,
)
await api.store_artifact(decision)

# Verify session chain
is_valid, msg = await api.verify_session_chain("session-abc123")
print(f"Session valid: {is_valid} - {msg}")

# Query artifacts
artifacts = await api.list_session_artifacts("session-abc123")
print(f"Total artifacts: {len(artifacts)}")

code_changes = await api.list_by_category(ArtifactCategory.CODE)
print(f"Code artifacts: {len(code_changes)}")

security_artifacts = await api.list_by_tag("security")
print(f"Security-related: {len(security_artifacts)}")

# Statistics
stats = await api.get_stats()
print(stats)
```

## Key Features

✅ **Cryptographic Signing**: All artifacts signed with RSA-2048-SHA256
✅ **Hash Chaining**: Immutable audit trail with chain verification
✅ **Type Safety**: Pydantic-based validation and serialization
✅ **Fast Lookup**: Indexed by session, category, tags
✅ **Dependency Tracking**: Link related artifacts and track causality
✅ **Full-Text Search**: Query by description and custom metadata

## Phase 2+ Roadmap

| Phase | Focus | Timeline |
|-------|-------|----------|
| **Phase 1** (Current) | Base classes, artifact types, memory storage | ✅ Complete |
| **Phase 2** | Supermemory L4 integration | WIP |
| **Phase 3** | Event hooks (auto-capture on tool use, file writes) | Planned |
| **Phase 4** | Analytics and dashboards | Planned |
| **Phase 5** | Replay engine integration | Planned |

## Testing

Tests should cover:
- Artifact creation with all specialized types
- Serialization/deserialization round-trips
- Hash chain verification
- Signature verification
- Storage and retrieval
- Query operations (by session, category, tag)
- Dependency tracking
- Concurrent operations

## Acceptance Criteria

- [x] BaseArtifact class with metadata
- [x] 6 concrete artifact types (2 code, 2 tool, 2 decision)
- [x] ArtifactStorage interface + MemoryArtifactStorage
- [x] ArtifactRegistry with factory methods
- [x] Specialized generators for each type
- [x] High-level ArtifactAPI with full CRUD and queries
- [x] Integration with MAIF cryptographic foundation
- [x] Type-safe Pydantic models for all artifacts

## References

- `src/thegent/artifacts/` - Implementation directory
- `src/thegent/maif/` - Cryptographic foundation
- `docs/research/MAIF_ACTION_ARTIFACTS.md` - Research document
- `docs/research/SESSION_RESEARCH_FRAGMENTS_EXPANDED.md` - Requirements
