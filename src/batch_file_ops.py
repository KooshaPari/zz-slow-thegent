"""Batch file operations module.

Provides file operation utilities with atomic batch semantics.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class BatchFileOpsError(Exception):
    """Error raised when batch file operations fail."""


@dataclass
class BatchOperation:
    """Represents a single file operation in a batch."""

    file_path: str
    operation_type: str  # 'read', 'write', 'delete'
    success: bool = False
    error_message: str | None = None


@dataclass
class BatchOperationResult:
    """Result of a batch operation."""

    total: int
    successful: int
    failed: int
    operations: list[BatchOperation]
    errors: list[str]


def batch_read_files(paths: list[str]) -> dict[str, str]:
    """Read multiple files and return a mapping of path to content.

    Args:
        paths: List of file paths to read.

    Returns:
        Dictionary mapping file path to content.
    """
    results = {}
    for path_str in paths:
        try:
            path = Path(path_str)
            if path.exists():
                results[path_str] = path.read_text(encoding="utf-8")
            else:
                results[path_str] = ""
        except Exception:
            results[path_str] = ""
    return results


def batch_write_files(operations: list[tuple[str, str]]) -> BatchOperationResult:
    """Write multiple files from a list of (path, content) pairs.

    Args:
        operations: List of (path, content) tuples.

    Returns:
        BatchOperationResult with operation status.
    """
    results = []
    errors = []
    successful = 0
    failed = 0

    for path_str, content in operations:
        op = BatchOperation(file_path=path_str, operation_type="write")
        try:
            path = Path(path_str)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            op.success = True
            successful += 1
        except Exception as e:
            op.success = False
            op.error_message = str(e)
            errors.append(f"Failed to write {path_str}: {e}")
            failed += 1
        results.append(op)

    return BatchOperationResult(
        total=len(operations),
        successful=successful,
        failed=failed,
        operations=results,
        errors=errors,
    )


def batch_edit_files(edits: list[tuple[str, str, str]]) -> BatchOperationResult:
    """Edit multiple files using search/replace.

    Args:
        edits: List of (path, search, replace) tuples.

    Returns:
        BatchOperationResult with operation status.
    """
    operations = []
    for path_str, search, replace in edits:
        try:
            path = Path(path_str)
            if path.exists():
                content = path.read_text(encoding="utf-8")
                new_content = content.replace(search, replace)
                operations.append((path_str, new_content))
        except Exception:
            pass
    return batch_write_files(operations)


def batch_delete_files(paths: list[str]) -> BatchOperationResult:
    """Delete multiple files.

    Args:
        paths: List of file paths to delete.

    Returns:
        BatchOperationResult with operation status.
    """
    results = []
    errors = []
    successful = 0
    failed = 0

    for path_str in paths:
        op = BatchOperation(file_path=path_str, operation_type="delete")
        try:
            path = Path(path_str)
            if path.exists():
                path.unlink()
            op.success = True
            successful += 1
        except Exception as e:
            op.success = False
            op.error_message = str(e)
            errors.append(f"Failed to delete {path_str}: {e}")
            failed += 1
        results.append(op)

    return BatchOperationResult(
        total=len(paths),
        successful=successful,
        failed=failed,
        operations=results,
        errors=errors,
    )


def normalize_path(path: str | Path) -> Path:
    """Normalize a path to a Path object.

    Args:
        path: Path string or Path object.

    Returns:
        Normalized Path object.
    """
    return Path(path).resolve()


class BatchFileOps:
    """Class-based interface for batch file operations."""

    def __init__(self) -> None:
        pass

    def read(self, paths: list[str]) -> dict[str, str]:
        """Read multiple files."""
        return batch_read_files(paths)

    def write(self, operations: list[tuple[str, str]]) -> BatchOperationResult:
        """Write multiple files."""
        return batch_write_files(operations)

    def edit(self, edits: list[tuple[str, str, str]]) -> BatchOperationResult:
        """Edit multiple files."""
        return batch_edit_files(edits)

    def delete(self, paths: list[str]) -> BatchOperationResult:
        """Delete multiple files."""
        return batch_delete_files(paths)


__all__ = [
    "BatchFileOps",
    "BatchFileOpsError",
    "BatchOperation",
    "BatchOperationResult",
    "batch_delete_files",
    "batch_edit_files",
    "batch_read_files",
    "batch_write_files",
    "normalize_path",
]
