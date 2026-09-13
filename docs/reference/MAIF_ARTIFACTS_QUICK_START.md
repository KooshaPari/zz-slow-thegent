# MAIF Artifacts - Quick Start Guide

**Status**: Phase 1 Complete | **Last Updated**: 2026-02-18

## 5-Minute Setup

```python
from thegent.artifacts import ArtifactAPI
from thegent.maif import SigningKey

# 1. Initialize
signing_key = SigningKey.generate()
verifying_key = signing_key.get_public_key()
api = ArtifactAPI(signing_key, verifying_key)

# 2. Create artifact (choose type)
artifact = await api.generators.code.create_code_change(
    agent_id="my-agent",
    session_id="session-123",
    file_path="src/main.py",
    change_type=CodeChangeType.FEATURE,
    before_content=b"old",
    after_content=b"new",
)

# 3. Store
artifact_id = await api.store_artifact(artifact)

# 4. Retrieve
artifact = await api.retrieve_artifact(artifact_id)

# 5. Verify
is_valid = await api.verify_artifact(artifact)
```

## Artifact Types at a Glance

### Code

```python
# Code change
CodeChangeArtifact.create(
    maif, file_path="src/file.py", change_type=CodeChangeType.BUG_FIX, affected_symbols=["function_name"]
)

# File operation
FileOperationArtifact.create(maif, operation_type=FileOperationType.CREATE, source_path="src/new_file.py")
```

### Tool

```python
# Generic tool
ToolInvocationArtifact.create(
    maif,
    tool_type=ToolType.MCP,
    tool_name="file_read",
    arguments={"path": "/file"},
    result_status=ToolResultStatus.SUCCESS,
)

# MCP call (specialized)
MCPCallArtifact.create(maif, mcp_server="filesystem", mcp_tool="read", call_status=ToolResultStatus.SUCCESS)
```

### Decision

```python
# Decision point
DecisionArtifact.create(
    maif, decision_type=DecisionType.ROUTING, options_considered=["opt-a", "opt-b"], selected_option="opt-a"
)

# Branch point
BranchingPointArtifact.create(
    maif, condition="retry_count < max_retries", condition_result=True, true_branch="retry", false_branch="fail"
)
```

## Common Operations

### Query by Category

```python
code_artifacts = await api.list_by_category(ArtifactCategory.CODE)
tool_artifacts = await api.list_by_category(ArtifactCategory.TOOL)
decision_artifacts = await api.list_by_category(ArtifactCategory.DECISION)
```

### Query by Tag

```python
critical = await api.list_by_tag("critical")
security = await api.list_by_tag("security")
```

### Search

```python
results = await api.search_artifacts("permission denied")
```

### List Session

```python
artifacts = await api.list_session_artifacts("session-123")
```

### Dependency Chain

```python
chain = await api.get_dependency_chain(artifact_id)
related = await api.list_related_artifacts(artifact_id)
```

### Verify Chain

```python
is_valid, msg = await api.verify_session_chain("session-123")
```

## Adding Tags & Dependencies

```python
# After creating artifact
artifact.add_tag("feature")
artifact.add_tag("async")
artifact.add_dependency("artifact-id-1")
artifact.add_related_artifact("artifact-id-2")

await api.store_artifact(artifact)
```

## Statistics

```python
stats = await api.get_stats()
# {
#   "storage": {
#       "total_artifacts": 42,
#       "sessions": 5,
#       "categories": {...},
#       "tags": {...}
#   },
#   "registry": {
#       "total_types": 6,
#       "types": [...],
#       "categories": {...}
#   }
# }
```

## Enums Reference

### CodeChangeType

- EDIT, REFACTOR, BUG_FIX, FEATURE, FORMATTING

### FileOperationType

- CREATE, DELETE, RENAME, MOVE, COPY

### ToolType

- MCP, API, CLI, SUBPROCESS, DATABASE

### ToolResultStatus

- SUCCESS, PARTIAL, FAILURE, TIMEOUT, UNKNOWN

### DecisionType

- ROUTING, RESOURCE_ALLOCATION, STRATEGY_SELECTION, PARAMETER_CHOICE, ERROR_RECOVERY

### ArtifactCategory

- CODE, TOOL, DECISION, SYSTEM

## Integration with MAIF

```python
from thegent.maif import MAIFArtifactGenerator

# Low-level MAIF artifact
maif_gen = MAIFArtifactGenerator(signing_key)
maif = maif_gen.create_artifact(
    action_type=ActionType.CODE_CHANGE,
    agent_id="agent",
    session_id="session",
    input_data=b"before",
    output_data=b"after",
)

# Convert to specialized artifact
artifact = CodeChangeArtifact.create(maif, ...)

# Convert back to MAIF
maif_back = artifact.to_maif_artifact()
```

## Phase 2 Preview

Phase 2 will add:

- Remote storage with Supermemory L4
- Lifecycle hooks (auto-capture on tool use, writes)
- Performance optimizations

No API changes needed - just swap storage backend:

```python
# Phase 2 (when available)
from thegent.artifacts.storage import SupermemoryArtifactStorage

storage = SupermemoryArtifactStorage(base_url="...", api_key="...")
api = ArtifactAPI(signing_key, verifying_key, storage=storage)
```

## Files to Check

- **Implementation**: `src/thegent/artifacts/`
- **Tests**: `tests/unit/artifacts/` (to be created)
- **Documentation**: `docs/reference/MAIF_ARTIFACTS_PHASE1_IMPLEMENTATION.md`
- **MAIF Foundation**: `src/thegent/maif/`

## Error Handling

```python
try:
    artifact = await api.retrieve_artifact(artifact_id)
    if not artifact:
        print("Artifact not found")

    is_valid = await api.verify_artifact(artifact)
    if not is_valid:
        print("Signature verification failed")
except Exception as e:
    print(f"Error: {e}")
```

## Performance Notes

- Artifact creation: <1ms (MAIF-limited)
- Storage (in-memory): <1ms
- Retrieval: <1ms
- Verification: <10ms
- Session chain verify: O(n) where n = artifacts in session

## Next Steps

1. Write unit tests in `tests/unit/artifacts/`
2. Add integration tests with MAIF foundation
3. Phase 2: Implement Supermemory storage backend
4. Phase 3: Add lifecycle hooks for automatic capture
