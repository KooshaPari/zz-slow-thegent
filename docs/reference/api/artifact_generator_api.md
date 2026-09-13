# artifact_generator API Reference

> **Source**: `src/thegent/maif/artifact_generator.py`

MAIF Artifact Generator - Creating and signing artifacts.

Implements the MAIFArtifactGenerator class for creating cryptographically signed
MAIF artifacts with hash chain tracking.

---

## MAIFArtifactGenerator

Generator for creating signed MAIF artifacts with hash chain tracking.

### Methods

#### MAIFArtifactGenerator.**init**

```python
__init__(self: Any, signer: SigningKey)
```

Initialize the artifact generator.

**Parameters**:

- `signer`: SigningKey instance for signing artifacts.

---

#### MAIFArtifactGenerator.create_artifact

```python
create_artifact(self: Any, action_type: ActionType, agent_id: str, session_id: str, input_data: bytes, output_data: bytes, metadata: Any)
```

Create a signed MAIF artifact with hash chain.

**Parameters**:

- `action_type`: Type of action (ActionType enum)
- `agent_id`: Identifier of the agent performing the action
- `session_id`: Session identifier for grouping artifacts
- `input_data`: Input bytes (e.g., file before edit)
- `output_data`: Output bytes (e.g., file after edit)
- `metadata`: Optional metadata dictionary

**Returns**: MAIFArtifact instance with signature and hash chain.

---

#### MAIFArtifactGenerator.get_last_hash

```python
get_last_hash(self: Any, session_id: str)
```

Get the last artifact hash for a session.

**Parameters**:

- `session_id`: Session identifier.

**Returns**: Hash of the last artifact in the session, or empty string if no artifacts.

---

#### MAIFArtifactGenerator.reset_session

```python
reset_session(self: Any, session_id: str)
```

Reset hash chain for a session.

**Parameters**:

- `session_id`: Session identifier.

---

---

## create_artifact

```python
create_artifact(self: Any, action_type: ActionType, agent_id: str, session_id: str, input_data: bytes, output_data: bytes, metadata: Any)
```

Create a signed MAIF artifact with hash chain.

**Parameters**:

- `action_type`: Type of action (ActionType enum)
- `agent_id`: Identifier of the agent performing the action
- `session_id`: Session identifier for grouping artifacts
- `input_data`: Input bytes (e.g., file before edit)
- `output_data`: Output bytes (e.g., file after edit)
- `metadata`: Optional metadata dictionary

**Returns**: MAIFArtifact instance with signature and hash chain.

**Raises**:

- `ValueError`: If parameters are invalid.

---

## get_last_hash

```python
get_last_hash(self: Any, session_id: str)
```

Get the last artifact hash for a session.

**Parameters**:

- `session_id`: Session identifier.

**Returns**: Hash of the last artifact in the session, or empty string if no artifacts.

---

## reset_session

```python
reset_session(self: Any, session_id: str)
```

Reset hash chain for a session.

**Parameters**:

- `session_id`: Session identifier.

---
