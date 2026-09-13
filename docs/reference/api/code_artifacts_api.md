# code_artifacts API Reference

> **Source**: `src/thegent/artifacts/code_artifacts.py`

Code-Related Artifacts - Code changes and file operations.

Provides specialized artifacts for:

- Code edits and modifications
- File operations (create, delete, move)

---

## CodeChangeArtifact

Artifact for code modifications.

Tracks:

- File path and language
- Change type and description
- Affected functions/classes
- Test coverage impact

**Inherits from**: `BaseArtifact`

### Methods

#### CodeChangeArtifact.create

```python
create(cls: Any, maif: MAIFArtifact, file_path: str, change_type: CodeChangeType, language: Any)
```

Create code change artifact.

**Parameters**:

- `maif`: Base MAIF artifact
- `file_path`: Path to modified file
- `change_type`: Type of change
- `language`: Programming language
- `**kwargs`: Additional fields

**Returns**: CodeChangeArtifact instance

---

---

## CodeChangeType

Types of code changes.

**Inherits from**: `str, Enum`

---

## FileOperationArtifact

Artifact for file system operations.

Tracks:

- Operation type (create, delete, rename, etc.)
- Source and destination paths
- File metadata (size, type)
- Permission changes

**Inherits from**: `BaseArtifact`

### Methods

#### FileOperationArtifact.create

```python
create(cls: Any, maif: MAIFArtifact, operation_type: FileOperationType, source_path: str, dest_path: Any)
```

Create file operation artifact.

**Parameters**:

- `maif`: Base MAIF artifact
- `operation_type`: Type of operation
- `source_path`: Source file path
- `dest_path`: Destination path (if applicable)
- `**kwargs`: Additional fields

**Returns**: FileOperationArtifact instance

---

---

## FileOperationType

Types of file operations.

**Inherits from**: `str, Enum`

---

## create

```python
create(cls: Any, maif: MAIFArtifact, operation_type: FileOperationType, source_path: str, dest_path: Any)
```

Create file operation artifact.

**Parameters**:

- `maif`: Base MAIF artifact
- `operation_type`: Type of operation
- `source_path`: Source file path
- `dest_path`: Destination path (if applicable)
- `**kwargs`: Additional fields

**Returns**: FileOperationArtifact instance

---
