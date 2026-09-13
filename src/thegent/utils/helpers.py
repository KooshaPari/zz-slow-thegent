"""Reusable helper functions for common patterns."""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def normalize_path(path: str | Path) -> Path:
    """Normalize a path to a Path object, handling both absolute and relative paths.

    Args:
        path: Path string or Path object

    Returns:
        Normalized Path object
    """
    path_obj = Path(path) if isinstance(path, str) else path

    # Expand user and resolve
    return path_obj.expanduser().resolve()


def batch_file_operations(
    operations: list[tuple[str, Any]],
    batch_size: int = 10,
) -> list[Any]:
    """Batch file operations to reduce tool calls.

    Args:
        operations: List of (operation_type, params) tuples
        batch_size: Number of operations per batch

    Returns:
        List of results from operations
    """
    results = []
    for i in range(0, len(operations), batch_size):
        batch = operations[i : i + batch_size]
        batch_results = []
        for op_type, params in batch:
            try:
                if op_type == "read":
                    path = normalize_path(params)
                    batch_results.append(path.read_text())
                elif op_type == "write":
                    path, content = params
                    path = normalize_path(path)
                    path.write_text(content)
                    batch_results.append(True)
                elif op_type == "exists":
                    path = normalize_path(params)
                    batch_results.append(path.exists())
                else:
                    batch_results.append(None)
            except Exception as e:  # noqa: PERF203 - intentional per-item error handling
                logger.error(f"Error in batch operation {op_type}: {e}")
                batch_results.append(None)
        results.extend(batch_results)
    return results


def safe_read_file(path: str | Path, encoding: str = "utf-8") -> str | None:
    """Safely read a file with error handling.

    Args:
        path: Path to file
        encoding: File encoding

    Returns:
        File contents or None if error
    """
    try:
        path = normalize_path(path)
        return path.read_text(encoding=encoding)
    except Exception as e:
        logger.error(f"Error reading file {path}: {e}")
        return None


def safe_read_file_with_version(path: str | Path, encoding: str = "utf-8") -> tuple[str | None, str | None]:
    """Safely read a file and return its content and OCC version (hash).

    Args:
        path: Path to file
        encoding: File encoding

    Returns:
        Tuple of (content, version). Version is "none" if file doesn't exist.
    """
    import hashlib

    try:
        path = normalize_path(path)
        if not path.exists():
            return None, "none"

        content = path.read_text(encoding=encoding)
        version = hashlib.sha256(content.encode(encoding)).hexdigest()
        return content, version
    except Exception as e:
        logger.error(f"Error reading file {path} with version: {e}")
        return None, None


def read_file_chunk(path: str | Path, offset: int = 0, limit: int | None = None, encoding: str = "utf-8") -> str | None:
    """Read a chunk of a file with offset and limit.

    Args:
        path: Path to file
        offset: Byte offset to start reading from
        limit: Maximum number of bytes to read (None for all)
        encoding: File encoding

    Returns:
        File chunk contents or None if error
    """
    try:
        path = normalize_path(path)
        with open(path, "rb") as f:
            f.seek(offset)
            data = f.read(limit) if limit is not None else f.read()
        return data.decode(encoding, errors="replace")
    except Exception as e:
        logger.error(f"Error reading file chunk {path} (offset={offset}, limit={limit}): {e}")
        return None


def read_file_lines(
    path: str | Path,
    start_line: int = 0,
    num_lines: int | None = None,
    encoding: str = "utf-8",
) -> list[str] | None:
    """Read specific lines from a file efficiently without loading the whole file into memory.

    Args:
        path: Path to file
        start_line: Line number to start from (0-indexed)
        num_lines: Number of lines to read (None for all remaining)
        encoding: File encoding

    Returns:
        List of lines or None if error
    """
    import itertools

    try:
        path = normalize_path(path)
        with open(path, encoding=encoding) as f:
            # Skip lines efficiently
            lines_it = itertools.islice(f, start_line, start_line + num_lines if num_lines is not None else None)
            return list(lines_it)
    except Exception as e:
        logger.error(f"Error reading file lines {path} (start={start_line}, num={num_lines}): {e}")
        return None


def read_file_optimized(
    path: str | Path,
    offset: int = 0,
    limit: int | None = None,
    max_lines: int | None = None,
    max_size_mb: int = 1,
    encoding: str = "utf-8",
) -> str | None:
    """Read a file with optimization and safety limits for large files.

    If no limit or max_lines is provided and the file exceeds max_size_mb,
    it will be truncated to avoid excessive memory usage.

    Args:
        path: Path to file
        offset: Byte offset to start reading from
        limit: Maximum number of bytes to read
        max_lines: Maximum number of lines to read (applied after offset)
        max_size_mb: Maximum size in MB to read if no limit is specified
        encoding: File encoding

    Returns:
        File contents or None if error
    """
    try:
        path = normalize_path(path)
        if not path.exists():
            return None

        if max_lines is not None:
            lines = read_file_lines(path, start_line=0, num_lines=max_lines, encoding=encoding)
            return "".join(lines) if lines is not None else None

        file_size = path.stat().st_size

        # Determine actual limit
        actual_limit = limit
        if actual_limit is None:
            max_bytes = max_size_mb * 1024 * 1024
            if file_size > max_bytes:
                logger.warning(f"File {path} is large ({file_size} bytes). Truncating to {max_bytes} bytes.")
                actual_limit = max_bytes

        return read_file_chunk(path, offset=offset, limit=actual_limit, encoding=encoding)
    except Exception as e:
        logger.error(f"Error reading optimized file {path}: {e}")
        return None


def read_file_tail(path: str | Path, num_lines: int = 10, encoding: str = "utf-8") -> list[str] | None:
    """Read the last N lines from a file efficiently.

    Args:
        path: Path to file
        num_lines: Number of lines to read from the end
        encoding: File encoding

    Returns:
        List of lines or None if error
    """
    try:
        path = normalize_path(path)
        if not path.exists():
            return None

        file_size = path.stat().st_size
        if file_size == 0:
            return []

        # Start with a buffer size proportional to num_lines (approx 100 chars per line)
        buffer_size = min(file_size, num_lines * 100 + 512)
        lines: list[str] = []

        with open(path, "rb") as f:
            f.seek(0, 2)  # Seek to end
            pos = file_size

            while pos > 0 and len(lines) <= num_lines:
                read_size = min(pos, buffer_size)
                pos -= read_size
                f.seek(pos)
                chunk = f.read(read_size).decode(encoding, errors="replace")

                # Split and filter empty if at the very end of file
                new_lines = chunk.splitlines()

                # If we read multiple chunks, handle line merging
                if lines:
                    # Merge last line of current chunk with first line of previous chunks
                    if not chunk.endswith(("\n", "\r")):
                        lines[0] = new_lines[-1] + lines[0]
                        lines = new_lines[:-1] + lines
                    else:
                        lines = new_lines + lines
                else:
                    lines = new_lines

                # Double buffer size for next iteration if needed
                buffer_size = min(pos, buffer_size * 2)

        return lines[-num_lines:]
    except Exception as e:
        logger.error(f"Error reading file tail {path} (num={num_lines}): {e}")
        return None


def safe_write_file(
    path: str | Path,
    content: str,
    expected_version: str | None = None,
    encoding: str = "utf-8",
) -> bool:
    """Safely write a file with error handling and optional OCC version check.

    Args:
        path: Path to file
        content: Content to write
        expected_version: Optional version (hash) to check before writing
        encoding: File encoding

    Returns:
        True if successful, False otherwise
    """
    import hashlib

    try:
        path = normalize_path(path)

        if expected_version:
            if not path.exists():
                current_version = "none"
            else:
                # Hash the decoded text bytes so OCC is stable across LF/CRLF differences.
                current_text = path.read_text(encoding=encoding)
                current_version = hashlib.sha256(current_text.encode(encoding)).hexdigest()

            if current_version != expected_version:
                logger.error(f"OCC violation for {path}: expected {expected_version}, got {current_version}")
                return False

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding=encoding)
        return True
    except Exception as e:
        logger.error(f"Error writing file {path}: {e}")
        return False


def read_json(path: str | Path) -> Any:
    """Read and parse a JSON file. Raises FileNotFoundError or ValueError on error."""
    import json

    p = normalize_path(path)
    content = p.read_text(encoding="utf-8")
    return json.loads(content)


def write_json(path: str | Path, data: Any, *, indent: int = 2) -> None:
    """Serialize *data* as JSON and write to *path*, creating parent dirs as needed."""
    import json

    p = normalize_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=indent))


def find_project_root(start: str | Path | None = None) -> Path:
    """Walk up from *start* (default: cwd) to find a directory containing pyproject.toml.

    Raises FileNotFoundError if no project root is found.
    """
    current = normalize_path(start) if start else Path.cwd()
    for directory in [current, *current.parents]:
        if (directory / "pyproject.toml").exists():
            return directory
    raise FileNotFoundError(f"No pyproject.toml found in {current} or any parent directory")
