"""
Batch file operations for thegent.

This module provides grouping for file reads and writes using native Rust (thegent-fs).
It includes transaction-like semantics for atomic batches and progress callbacks.
"""

from __future__ import annotations

import logging
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

from thegent.utils.path_utils import ensure_dir, normalize_path

# Native Rust extension (required)
try:
    import thegent_fs  # type: ignore[reportMissingImports]
except ImportError:
    raise ImportError("thegent-fs not available - install with: pip install thegent-fs")

logger = logging.getLogger(__name__)


@dataclass
class BatchOperation:
    """Represents a single file operation in a batch."""

    file_path: Path
    operation_type: str  # 'read', 'write', 'delete'
    success: bool = False
    error_message: str | None = None
    result: Any | None = None
    timestamp: str | None = None


@dataclass
class BatchResult:
    """Result of a batch operation."""

    total: int
    successful: int
    failed: int
    operations: list[BatchOperation]
    errors: list[str]
    backup_dir: Path | None = None
    duration_ms: float = 0.0


class BatchFileOperations:
    """Class for grouped file reads and writes with atomic semantics."""

    def __init__(self, create_backups: bool = True) -> None:
        self.create_backups = create_backups
        self.backup_dir: Path | None = None

    def _get_backup_dir(self) -> Path:
        """Ensure a backup directory exists for the current batch."""
        if not self.backup_dir:
            temp_root = Path(tempfile.gettempdir()) / "thegent_backups"
            ensure_dir(temp_root)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            self.backup_dir = temp_root / timestamp
            ensure_dir(self.backup_dir)
        return self.backup_dir

    def _backup_file(self, file_path: Path) -> Path | None:
        """Back up a file before modification."""
        if not file_path.exists():
            return None

        backup_root = self._get_backup_dir()
        # Create a unique name for the backup file
        relative = str(file_path).replace("/", "_").replace("\\", "_").replace(":", "_")
        backup_path = backup_root / relative
        thegent_fs.fs_copy_file(str(file_path), str(backup_path), True)
        return backup_path

    def batch_read(
        self,
        paths: list[Path | str],
        on_progress: Callable[[int, int], None] | None = None,
    ) -> dict[Path, str]:
        """Read multiple files and return a mapping of path to content."""
        results = {}
        total = len(paths)
        for i, path_str in enumerate(paths):
            path = normalize_path(path_str)
            results[path] = path.read_text(encoding="utf-8")
            if on_progress:
                on_progress(i + 1, total)
        return results

    def batch_write(
        self,
        operations: list[tuple[Path | str, str]],
        atomic: bool = True,
        on_progress: Callable[[int, int], None] | None = None,
    ) -> BatchResult:
        """Write multiple files from a list of (path, content) pairs."""
        start_time = time.perf_counter()
        total = len(operations)
        successful = 0
        failed = 0
        ops_results = []
        errors = []
        backups: dict[Path, Path | None] = {}

        try:
            # Pre-backup if atomic
            if atomic and self.create_backups:
                for path_str, _ in operations:
                    path = normalize_path(path_str)
                    backups[path] = self._backup_file(path)

            for i, (path_str, content) in enumerate(operations):
                path = normalize_path(path_str)
                op = BatchOperation(
                    file_path=path,
                    operation_type="write",
                    timestamp=datetime.now().isoformat(),
                )
                try:
                    # Backup individually if not already done by atomic pre-pass
                    if not atomic and self.create_backups:
                        self._backup_file(path)

                    ensure_dir(path.parent)
                    path.write_text(content, encoding="utf-8")
                    op.success = True
                    successful += 1
                except Exception as e:
                    op.error_message = str(e)
                    errors.append(f"Failed to write {path}: {e}")
                    failed += 1
                    if atomic:
                        raise  # Trigger rollback
                finally:
                    ops_results.append(op)
                    if on_progress:
                        on_progress(i + 1, total)

        except Exception:
            if atomic:
                self._rollback(backups)

        duration_ms = (time.perf_counter() - start_time) * 1000
        return BatchResult(
            total=total,
            successful=successful,
            failed=failed,
            operations=ops_results,
            errors=errors,
            backup_dir=self.backup_dir,
            duration_ms=duration_ms,
        )

    def _rollback(self, backups: dict[Path, Path | None]) -> None:
        """Roll back changes using backups."""
        for original, backup in backups.items():
            self._restore_backup(original, backup)

    def _restore_backup(self, original: Path, backup: Path | None) -> None:
        """Restore one file from backup during rollback, logging failures."""
        try:
            if backup and backup.exists():
                thegent_fs.fs_copy_file(str(backup), str(original), True)
            elif original.exists():
                # If it didn't exist before, delete it
                original.unlink()
        except Exception as e:
            logger.error(f"Rollback failed for {original}: {e}")
