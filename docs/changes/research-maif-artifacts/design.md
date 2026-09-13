# Research: MAIF Action Artifacts — Design

**Status**: Architecture Ready | **Version**: 1.0 | **Date**: 2026-02-18

---

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [Component Design](#2-component-design)
3. [Data Model](#3-data-model)
4. [API Design](#4-api-design)
5. [Integration Points](#5-integration-points)
6. [Error Handling](#6-error-handling)
7. [Performance & Scalability](#7-performance--scalability)
8. [Security Considerations](#8-security-considerations)

---

## 1. System Architecture

### High-Level Block Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    thegent Agent System                     │
└─────────────────────────────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
    CodeChange   FileOp        Decision
        │             │             │
        └─────────────┼─────────────┘
                      │
            ┌─────────▼─────────┐
            │ Action Dispatcher │
            └────────┬──────────┘
                     │
            ┌────────▼──────────┐
            │ MAIF Artifact Gen │ ← Generate with timestamp, signature
            └────────┬──────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
   L1 (Memory)  L2 (Disk)    L3/L4 (Supermemory)
   Hot Cache    Warm Cache    Long-term + Immutable
```

### Layers & Responsibilities

| Layer | System | Role |
|-------|--------|------|
| **L1** | In-memory cache (LRU) | Hot artifacts for current session |
| **L2** | Local disk cache | Warm artifacts for replay |
| **L3** | Supermemory Knowledge Graph | Context relationships for replay |
| **L4** | Supermemory Documents API | Immutable artifact storage |

---

## 2. Component Design

### 2.1 MAIF Artifact Generator

**Responsibility**: Create signed artifacts from agent actions.

```python
# thegent/src/thegent/maif/artifact_generator.py


class MAIFArtifactGenerator:
    def __init__(self, signer: SigningKey):
        self.signer = signer
        self.last_hash: dict[str, str] = {}  # session_id -> last_artifact_hash

    def create_artifact(
        self,
        action_type: ActionType,
        agent_id: str,
        session_id: str,
        input_data: bytes,
        output_data: bytes,
        metadata: dict | None = None,
    ) -> MAIFArtifact:
        """Create a signed MAIF artifact with hash chain."""
        prev_hash = self.last_hash.get(session_id, "")

        artifact = MAIFArtifact(
            id=uuid.uuid4().hex,
            timestamp=int(time.time()),
            action_type=action_type,
            agent_id=agent_id,
            session_id=session_id,
            input_hash=self._hash(input_data),
            output_hash=self._hash(output_data),
            previous_hash=prev_hash,
            metadata=metadata or {},
        )

        # Sign the artifact
        artifact_bytes = self._serialize(artifact)
        artifact.signature = self.signer.sign(artifact_bytes).hex()

        # Update hash chain
        self.last_hash[session_id] = self._hash(artifact_bytes)

        return artifact

    def _hash(self, data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def _serialize(self, artifact: MAIFArtifact) -> bytes:
        # Deterministic serialization for hashing
        return json.dumps(
            artifact.model_dump(exclude={"signature"}),
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
```

### 2.2 Hash Chain Validator

**Responsibility**: Verify artifact chains and detect tampering.

```python
# thegent/src/thegent/maif/hash_chain.py


class HashChainValidator:
    def __init__(self):
        self.chain_heads: dict[str, str] = {}  # session_id -> latest_artifact_hash

    def verify_chain(
        self,
        artifacts: list[MAIFArtifact],
    ) -> tuple[bool, str]:
        """Verify integrity of artifact chain."""
        session_id = artifacts[0].session_id

        for i, artifact in enumerate(artifacts):
            # Check previous hash matches
            if i == 0:
                expected_prev = ""
            else:
                expected_prev = self._hash(self._serialize(artifacts[i - 1]))

            if artifact.previous_hash != expected_prev:
                return False, f"Artifact {i}: hash chain broken"

            # Verify signature
            if not self._verify_signature(artifact):
                return False, f"Artifact {i}: signature invalid"

        # Update chain head
        self.chain_heads[session_id] = self._hash(self._serialize(artifacts[-1]))

        return True, "OK"

    def _verify_signature(self, artifact: MAIFArtifact) -> bool:
        """Verify artifact signature."""
        artifact_copy = artifact.model_copy()
        artifact_copy.signature = ""

        message = self._serialize(artifact_copy)
        signature_bytes = bytes.fromhex(artifact.signature)

        # Verify with public key
        return self._public_key.verify(message, signature_bytes)

    def _hash(self, data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def _serialize(self, artifact: MAIFArtifact) -> bytes:
        return json.dumps(
            artifact.model_dump(exclude={"signature"}),
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
```

### 2.3 MAIF Storage (L4 Integration)

**Responsibility**: Persist artifacts to Supermemory L4.

```python
# thegent/src/thegent/maif/storage.py

class MAIFStorage:
    def __init__(self, supermemory_client: SupermemoryClient):
        self.client = supermemory_client
        self.local_cache = {}  # Fallback cache

    async def store(self, artifact: MAIFArtifact) -> str:
        """Store artifact in L4 with fallback to local cache."""
        try:
            # Try L4 first
            doc_id = await self.client.store_document(
                artifact.model_dump(),
                metadata={
                    "session_id": artifact.session_id,
                    "agent_id": artifact.agent_id,
                    "timestamp": artifact.timestamp,
                    "action_type": artifact.action_type.value,
                },
            )
            return doc_id
        except Exception as e:
            logger.warning(f"L4 store failed: {e}, falling back to local cache")
            # Fallback to local cache
            local_id = artifact.id
            self.local_cache[local_id] = artifact
            return local_id

    async def retrieve(\n        self,\n        artifact_id: str,\n    ) -> MAIFArtifact | None:\n        \"\"\"Retrieve artifact from L4 or fallback cache.\"\"\"\n        try:\n            # Try L4 first\n            doc = await self.client.get_document(artifact_id)\n            return MAIFArtifact.model_validate(doc)\n        except Exception:\n            # Fallback to local cache\n            return self.local_cache.get(artifact_id)\n    \n    async def retrieve_by_session(\n        self,\n        session_id: str,\n    ) -> list[MAIFArtifact]:\n        \"\"\"Retrieve all artifacts for a session.\"\"\"\n        try:\n            docs = await self.client.query(\n                f\"session_id:{session_id}\",\n                limit=10000,\n            )\n            return [\n                MAIFArtifact.model_validate(doc)\n                for doc in docs\n            ]\n        except Exception:\n            # Fallback to local cache filtering\n            return [\n                a for a in self.local_cache.values()\n                if a.session_id == session_id\n            ]\n```

### 2.4 Action Hooks

**Responsibility**: Intercept actions and trigger artifact creation.

```bash
# hooks/maif-artifact-hooks.sh

#!/bin/bash

# Hook: PostToolUse for Write/Edit/Delete operations
# Creates MAIF artifacts for file changes

source "$(dirname "$0")/lib/common.sh"

ARTIFACT_GENERATOR="${CLAUDE_PLUGIN_ROOT}/thegent_maif_gen"

main() {
    local tool_name="$1"
    local tool_result="$2"

    case "$tool_name" in
        Write)
            create_artifact "FileOperation" "write" "$tool_result"
            ;;
        Edit)
            create_artifact "FileOperation" "edit" "$tool_result"
            ;;
        Bash)
            # Only for significant system calls
            if is_significant_call "$tool_result"; then
                create_artifact "SystemCall" "bash" "$tool_result"
            fi
            ;;
    esac
}

create_artifact() {
    local action_type="$1"
    local operation="$2"
    local result="$3"

    python3 "$ARTIFACT_GENERATOR" \\
        --action-type "$action_type" \\
        --operation "$operation" \\
        --result "$result" \\
        --session-id "${CLAUDE_SESSION_ID}" \\
        --agent-id "${CLAUDE_AGENT_ID}" \\
        || echo "Artifact creation failed (non-fatal)"
}

is_significant_call() {
    local result="$1"
    # Filter out trivial calls (ls, pwd, etc.)
    [[ "$result" =~ (mkdir|rm|cp|mv|git|pytest|build) ]]
}

main "$@"
```

---

## 3. Data Model

### 3.1 MAIFArtifact Struct

```python
# thegent/src/thegent/maif/models.py

from enum import Enum
from typing import Optional
from pydantic import BaseModel


class ActionType(str, Enum):
    CODE_CHANGE = "code_change"
    FILE_OPERATION = "file_operation"
    SYSTEM_CALL = "system_call"
    DECISION = "decision"
    ERROR = "error"


class MAIFArtifact(BaseModel):
    id: str
    timestamp: int  # Unix epoch seconds
    action_type: ActionType
    agent_id: str
    session_id: str

    input_hash: str  # SHA-256 hex
    output_hash: str  # SHA-256 hex

    signature: str  # Hex-encoded RSA-2048 signature
    previous_hash: str  # Hash of previous artifact

    metadata: dict = {}

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "id": "a1b2c3d4e5f6g7h8i9j0",
                    "timestamp": 1708259184,
                    "action_type": "file_operation",
                    "agent_id": "agent-1",
                    "session_id": "session-xyz",
                    "input_hash": "abc123...",
                    "output_hash": "def456...",
                    "signature": "sig789...",
                    "previous_hash": "prev0ab...",
                    "metadata": {"file": "/path/to/file.py", "bytes": 1024},
                }
            ]
        }
```

### 3.2 Serialization Format

**For Hashing & Signing**: Deterministic JSON (sorted keys, compact spacing)

```json
{
  "action_type": "file_operation",
  "agent_id": "agent-1",
  "id": "a1b2c3d4e5f6g7h8i9j0",
  "input_hash": "abc123...",
  "metadata": {"file": "/path/to/file.py"},
  "output_hash": "def456...",
  "previous_hash": "prev0ab...",
  "session_id": "session-xyz",
  "timestamp": 1708259184
}
```

---

## 4. API Design

### 4.1 Artifact Creation

```python
# thegent_maif_gen CLI or function


async def create_artifact(
    action_type: ActionType,
    agent_id: str,
    session_id: str,
    input_data: bytes,
    output_data: bytes,
    metadata: dict | None = None,
) -> MAIFArtifact:
    """Create and store a MAIF artifact."""
    generator = MAIFArtifactGenerator(signer=get_signing_key())
    artifact = generator.create_artifact(action_type, agent_id, session_id, input_data, output_data, metadata)

    storage = MAIFStorage(supermemory_client)
    await storage.store(artifact)

    return artifact
```

### 4.2 Chain Verification

```python
async def verify_artifact_chain(
    session_id: str,
) -> tuple[bool, list[str]]:
    """Verify artifact chain for a session. Returns (is_valid, errors)."""
    storage = MAIFStorage(supermemory_client)
    artifacts = await storage.retrieve_by_session(session_id)

    validator = HashChainValidator()
    is_valid, message = validator.verify_chain(artifacts)

    errors = [] if is_valid else [message]
    return is_valid, errors
```

### 4.3 Audit Query

```python
async def query_artifacts(
    session_id: str | None = None,
    agent_id: str | None = None,
    timestamp_start: int | None = None,
    timestamp_end: int | None = None,
    limit: int = 1000,
) -> list[MAIFArtifact]:
    """Query artifacts by filters."""
    storage = MAIFStorage(supermemory_client)

    # Build query (Supermemory syntax)
    filters = []
    if session_id:
        filters.append(f"session_id:{session_id}")
    if agent_id:
        filters.append(f"agent_id:{agent_id}")
    if timestamp_start:
        filters.append(f"timestamp>={timestamp_start}")
    if timestamp_end:
        filters.append(f"timestamp<={timestamp_end}")

    query = " AND ".join(filters)
    return await storage.retrieve_by_query(query, limit)
```

---

## 5. Integration Points

### 5.1 Integration with Supermemory

- **L3 Integration**: Store decision context (relationships) in Knowledge Graph
- **L4 Integration**: Store immutable artifacts in Documents API
- **Metadata**: Use Supermemory metadata for indexing (session_id, agent_id, timestamp, action_type)

### 5.2 Integration with Simulation (WP-4007)

- Replay engine retrieves artifacts from L4
- Reconstructs context from L3
- Determines if replay is deterministic

### 5.3 Integration with Audit System

- Audit queries artifacts by session/agent/time
- Verifies chain integrity
- Generates compliance reports

---

## 6. Error Handling

### 6.1 Artifact Creation Failures

| Failure | Impact | Handling |
|---------|--------|----------|
| Signer unavailable | Critical | Queue for retry, alert |
| Supermemory L4 unavailable | High | Fallback to local cache, circuit breaker |
| Input/output data too large | Medium | Chunk and store separately |
| Hash collision (impossible) | Low | Alert, investigate |

### 6.2 Chain Verification Failures

| Failure | Impact | Handling |
|---------|--------|----------|
| Hash mismatch | High | Quarantine session, alert |
| Signature invalid | Critical | Reject artifact, investigate |
| Missing artifact | Medium | Partial chain verification, log gap |

### 6.3 Storage Failures

| Failure | Impact | Handling |
|---------|--------|----------|
| L4 store fails | Medium | Retry with backoff, fallback to L2 |
| L4 retrieve fails | Low | Fallback to L2 cache |
| Network timeout | Medium | Retry, eventual consistency |

---

## 7. Performance & Scalability

### 7.1 Latency Targets

| Operation | Target | Baseline |
|-----------|--------|----------|
| Artifact creation | <1ms | Hashing: 0.1ms, Signing: 0.5ms, Store: 0.4ms |
| Chain verification (1000 artifacts) | <100ms | Hashing: 50ms, Signature verify: 40ms |
| Artifact retrieval | <100ms | L4 query: 80ms |
| Audit query (10k artifacts) | <500ms | L4 query: 400ms |

### 7.2 Storage Scaling

- **Artifact size**: ~1-5KB (JSON + signature)
- **Monthly artifacts (750k)**: ~1-5GB
- **Annual artifacts (9M)**: ~10-50GB
- **Cost** (Supermemory L4): ~$0.002/artifact → ~$1.5k/month

### 7.3 Caching Strategy

- **L1 (in-memory)**: Last 1000 artifacts per session
- **L2 (disk)**: Last 100k artifacts globally
- **L3 (Supermemory L3)**: Session relationships (indexed)
- **L4 (Supermemory L4)**: All artifacts (replicated, immutable)

---

## 8. Security Considerations

### 8.1 Cryptographic Approach

- **Signing**: RSA-2048 or Ed25519 (NIST-approved)
- **Hashing**: SHA-256 (FIPS-approved)
- **Key Management**: Secrets manager (AWS Secrets Manager, HashiCorp Vault)
- **Key Rotation**: Annual rotation, versioned keys

### 8.2 Tamper Detection

- **Hash Chain**: Sequential links detect any tampering
- **Signature Verification**: Rejects forged artifacts
- **Immutable Storage**: L4 prevents post-hoc modification

### 8.3 Access Control

- **Artifact Access**: Scoped to session owner and auditors
- **Chain Access**: Read-only for verification
- **Supermemory**: Project-scoped access via `x-sm-project` header

### 8.4 Data Privacy

- **PII Handling**: Encrypt sensitive metadata
- **Data Residency**: Ensure L4 respects data residency (EU, US, etc.)
- **Retention**: Archival after 30 days, deletion after 1 year (configurable)

---

## References

- [proposal.md](proposal.md) — Business case and scope
- [tasks.md](tasks.md) — Implementation checklist
- [SESSION_RESEARCH_FRAGMENTS_EXPANDED.md § 4](../SESSION_RESEARCH_FRAGMENTS_EXPANDED.md#4-maif-action-artifacts) — Research foundation
