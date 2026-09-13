<DONE>
# MAIF Action Artifacts Research

> **Status**: Research Complete | **Version**: 1.0 | **Date**: 2026-02-18
> **Priority**: P1 | **Depends**: WP-3002

## Overview

MAIF (Model-Aware Information Flow) action artifacts provide signed, immutable records of agent actions for provenance tracking and verification.

## Artifact Structure

```json
{
  "artifact_id": "uuid-v4",
  "action_type": "mcp_call|tool_use|message|decision",
  "payload": {
    "request": { ... },
    "response": { ... },
    "metadata": { ... }
  },
  "signature": "base64(signed(payload + timestamp))",
  "timestamp": "2026-02-18T12:00:00Z",
  "agent_id": "thegent-v0.1.0",
  "session_id": "session-uuid",
  "chain_of_thought": "Reasoning trace for this action",
  "verification_key_id": "key-uuid",
  "previous_artifact_id": "uuid (optional, for chaining)"
}
```

## Signing Mechanism

### Key Generation

```python
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


def generate_signing_key():
    """Generate RSA key pair for signing."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=4096)

    public_key = private_key.public_key()

    # Store private key securely (KMS, vault, etc.)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.BestAvailableEncryption(b"password"),
    )

    return private_key, public_key
```

### Signing Algorithm

```python
import base64
import hashlib
import json
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding


def sign_artifact(artifact: dict, private_key: rsa.RSAPrivateKey) -> str:
    """Sign artifact with RSA private key."""
    # Create canonical payload
    canonical = json.dumps(
        {"payload": artifact["payload"], "timestamp": artifact["timestamp"], "agent_id": artifact["agent_id"]},
        sort_keys=True,
    )

    # Calculate SHA-256 hash
    message_hash = hashlib.sha256(canonical.encode()).digest()

    # Sign with PKCS#1 v1.5 padding
    signature = private_key.sign(message_hash, padding.PKCS1v15(), hashes.SHA256())

    return base64.b64encode(signature).decode()
```

### Verification Process

```python
def verify_artifact(artifact: dict, public_key: rsa.RSAPublicKey) -> bool:
    """Verify artifact signature."""
    signature = base64.b64decode(artifact["signature"])

    canonical = json.dumps(
        {"payload": artifact["payload"], "timestamp": artifact["timestamp"], "agent_id": artifact["agent_id"]},
        sort_keys=True,
    )

    message_hash = hashlib.sha256(canonical.encode()).digest()

    try:
        public_key.verify(signature, message_hash, padding.PKCS1v15(), hashes.SHA256())
        return True
    except:
        return False
```

## Storage & Retrieval

### Local Cache

```python
import sqlite3
from pathlib import Path
from typing import Optional


class MAIFArtifactStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database for artifacts."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS artifacts (
                artifact_id TEXT PRIMARY KEY,
                action_type TEXT,
                payload TEXT,
                signature TEXT,
                timestamp TEXT,
                agent_id TEXT,
                session_id TEXT,
                chain_of_thought TEXT,
                verification_key_id TEXT,
                previous_artifact_id TEXT
            )
        """)
        conn.commit()
        conn.close()

    def store(self, artifact: dict):
        """Store artifact in local cache."""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """
            INSERT INTO artifacts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                artifact["artifact_id"],
                artifact["action_type"],
                json.dumps(artifact["payload"]),
                artifact["signature"],
                artifact["timestamp"],
                artifact["agent_id"],
                artifact["session_id"],
                artifact["chain_of_thought"],
                artifact["verification_key_id"],
                artifact.get("previous_artifact_id"),
            ),
        )
        conn.commit()
        conn.close()

    def get(self, artifact_id: str) -> Optional[dict]:
        """Retrieve artifact by ID."""
        conn = sqlite3.connect(self.db_path)
        row = conn.execute("SELECT * FROM artifacts WHERE artifact_id = ?", (artifact_id,)).fetchone()
        conn.close()

        if row:
            return dict(zip([c[0] for c in conn.execute("PRAGMA table_info(artifacts)").fetchall()], row))
        return None
```

### Remote Provenance Server

```python
class RemoteProvenanceClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {api_key}"}

    async def submit_artifact(self, artifact: dict) -> str:
        """Submit artifact to remote server."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{self.base_url}/api/artifacts", json=artifact, headers=self.headers)
            resp.raise_for_status()
            return resp.json()["artifact_id"]

    async def verify_artifact(self, artifact_id: str) -> bool:
        """Verify artifact with remote server."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.base_url}/api/artifacts/{artifact_id}/verify", headers=self.headers)
            resp.raise_for_status()
            return resp.json()["valid"]
```

## Integration Points

### Hook System

```python
class MAIFHook:
    def __init__(self, artifact_store: MAIFArtifactStore):
        self.store = artifact_store

    async def on_mcp_call(self, call: MCPCall):
        """Record MCP call as MAIF artifact."""
        artifact = {
            "artifact_id": str(uuid.uuid4()),
            "action_type": "mcp_call",
            "payload": {"server": call.server, "tool": call.tool, "arguments": call.arguments},
            "timestamp": datetime.utcnow().isoformat(),
            "agent_id": "thegent",
            "session_id": current_session_id(),
            "chain_of_thought": current_reasoning_trace(),
        }

        # Sign and store
        artifact["signature"] = sign_artifact(artifact, private_key)
        self.store.store(artifact)
```

### Memory System

```python
class MAIFMemoryIntegration:
    async def store_with_provenance(self, memory: dict, artifacts: List[dict]) -> str:
        """Store memory with associated MAIF artifacts."""
        memory_id = await self._store_memory(memory)

        # Link artifacts to memory
        for artifact in artifacts:
            await self._link_artifact(memory_id, artifact["artifact_id"])

        return memory_id
```

### Governance Layer

```python
class MAIFGovernanceIntegration:
    async def verify_action(self, artifact_id: str) -> VerificationResult:
        """Verify action through governance layer."""
        artifact = await self.store.get(artifact_id)

        # Verify signature
        if not verify_artifact(artifact, public_key):
            return VerificationResult.INVALID_SIGNATURE

        # Check against governance policies
        policy_result = await self._check_policies(artifact)
        if not policy_result.allowed:
            return VerificationResult.POLICY_VIOLATION

        return VerificationResult.VALID
```

---

**EXTENSION_SUMMARY**

**Extended on:** 2026-02-18
**Extended by:** Claude Code

### Changes Made

1. **Created standalone research document** from MAIF_ARTIFACT_SPEC_DEPTH.md
2. **Defined artifact structure** with JSON schema
3. **Implemented signing mechanism** with RSA keys
4. **Added storage layer** (local SQLite + remote)
5. **Documented integration points** (hooks, memory, governance)

### Cross-References Added

- MAIF_ARTIFACT_SPEC_DEPTH.md
- WP-3002

### Practical Additions

- Complete Python implementations
- Verification logic
- Storage and retrieval
- Governance integration
