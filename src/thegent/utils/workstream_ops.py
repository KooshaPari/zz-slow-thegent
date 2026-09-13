"""Automated work stream operations (read, parse, update)."""

import contextlib
import logging
import os
import tempfile
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import IO, Any

try:
    import fcntl
except ImportError:  # pragma: no cover - platform-specific
    fcntl = None  # type: ignore[assignment]

from thegent.commands.workstream import (
    lint_workstream_schema,
    normalize_workstream_sections,
)
from thegent.utils.helpers import safe_read_file
from thegent.utils.reusable_helpers import ReusableHelpers

logger = logging.getLogger(__name__)


def _lock_path_for(path: Path) -> Path:
    """Return lockfile path for a workstream markdown target."""
    return path.with_name(f".{path.name}.lock")


@contextlib.contextmanager
def _locked_file_access(path: Path) -> Iterator[None]:
    """Lock and synchronize workstream writes across concurrent claim/complete calls."""
    if fcntl is None:
        raise RuntimeError("workstream lock requires fcntl; flock is unavailable on this platform")

    lock_path = _lock_path_for(path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_file: IO[Any]
    lock_file = open(lock_path, "a+", encoding="utf-8")  # noqa: SIM115
    try:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally:
        with contextlib.suppress(Exception):
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            lock_file.close()


def _atomic_write(path: Path, content: str) -> bool:
    """Write *content* atomically via a temp file rename."""
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        os.replace(tmp_path, path)
        return True
    except Exception:
        with contextlib.suppress(Exception):
            tmp_path.unlink()
        raise


class WorkStreamOps:
    """Automated operations on work stream files."""

    def __init__(self, base_dir: Path | None = None) -> None:
        """Initialize work stream operations.

        Args:
            base_dir: Base directory for work stream files
        """
        self.base_dir = base_dir or Path.cwd()
        self.work_stream_path = self.find_work_stream()

    def find_work_stream(self) -> Path:
        """Find the work stream file in common locations."""
        locations = [
            self.base_dir / "docs" / "reference" / "WORK_STREAM.md",
            self.base_dir / "WORK_STREAM.md",
            self.base_dir / "docs" / "WORK_STREAM.md",
        ]
        for loc in locations:
            if loc.exists():
                return loc
        return locations[0]  # Default

    @ReusableHelpers.error_handler
    def read_backlog(self) -> list[dict[str, Any]]:
        """Read all items from BACKLOG section.

        Returns:
            List of backlog items with id, title, priority, depends
        """
        content = safe_read_file(self.work_stream_path)
        if not content:
            logger.warning(f"Work stream file not found or empty: {self.work_stream_path}")
            return []

        lines = content.splitlines()
        backlog_start = None
        next_section_start = None

        for i, line in enumerate(lines):
            if "## BACKLOG" in line:
                backlog_start = i
            elif backlog_start is not None and line.startswith("## "):
                next_section_start = i
                break

        if backlog_start is None:
            return []

        items = []
        # Skip header and separator
        for i in range(backlog_start + 1, next_section_start or len(lines)):
            line = lines[i]
            if line.startswith("|") and "| ID |" not in line and "|----" not in line:
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) >= 2:
                    raw_id = parts[0]
                    if raw_id.startswith("~~") and raw_id.endswith("~~"):
                        continue
                    item_id = raw_id.strip("~").strip()
                    if item_id and not item_id.startswith("*"):
                        items.append(
                            {
                                "id": item_id,
                                "title": parts[1] if len(parts) > 1 else "",
                                "source": parts[2] if len(parts) > 2 else "",
                                "priority": parts[3] if len(parts) > 3 else "P2",
                                "depends": parts[4] if len(parts) > 4 else "-",
                            }
                        )

        return items

    @ReusableHelpers.error_handler
    def claim_item(self, item_id: str, agent_id: str) -> bool:
        """Claim an item by adding it to CLAIMED section.

        Args:
            item_id: Work item ID
            agent_id: Agent identifier

        Returns:
            True if successful
        """
        if not self.work_stream_path.exists():
            return False

        try:
            with _locked_file_access(self.work_stream_path):
                content = safe_read_file(self.work_stream_path)
                if not content:
                    return False

                lines = content.splitlines()
                claimed_idx = None
                for i, line in enumerate(lines):
                    if "## CLAIMED" in line:
                        claimed_idx = i
                        break

                if claimed_idx is None:
                    # Create CLAIMED section if missing
                    lines.append("")
                    lines.append("## CLAIMED")
                    lines.append("")
                    lines.append("| ID | Agent | Claimed At |")
                    lines.append("|----|-------|------------|")
                    claimed_idx = len(lines) - 3

                # Find insertion point (after table header)
                insert_at = claimed_idx + 1
                for i in range(claimed_idx + 1, len(lines)):
                    if lines[i].startswith("## "):
                        insert_at = i
                        break
                    if lines[i].startswith("|") and "| ID |" not in lines[i] and "|----" not in lines[i]:
                        insert_at = i + 1

                timestamp = datetime.now(UTC).isoformat()
                claim_line = f"| {item_id} | {agent_id} | {timestamp} |"
                lines.insert(insert_at, claim_line)

                return _atomic_write(self.work_stream_path, "\n".join(lines) + "\n")
        except BlockingIOError:
            logger.warning(
                "Could not acquire claim lock for %s; another writer is active.",
                self.work_stream_path,
            )
            return False
        except RuntimeError as exc:
            logger.error("Could not claim item due lock setup error: %s", exc)
            return False

    @ReusableHelpers.error_handler
    def complete_item(self, item_id: str, agent_id: str) -> bool:
        """Mark an item as complete.

        Args:
            item_id: Work item ID
            agent_id: Agent identifier

        Returns:
            True if successful
        """
        if not self.work_stream_path.exists():
            return False

        try:
            with _locked_file_access(self.work_stream_path):
                content = safe_read_file(self.work_stream_path)
                if not content:
                    return False

                # Strike through in backlog
                updated = content.replace(f"| {item_id} |", f"| ~~{item_id}~~ |")
                lines = updated.splitlines()

                # Add to COMPLETED section
                completed_idx = None
                for i, line in enumerate(lines):
                    if "## COMPLETED" in line:
                        completed_idx = i
                        break

                if completed_idx is None:
                    lines.append("")
                    lines.append("## COMPLETED")
                    lines.append("")
                    lines.append("| ID | Agent | Completed At |")
                    lines.append("|----|-------|--------------|")
                    completed_idx = len(lines) - 3

                insert_at = completed_idx + 1
                for i in range(completed_idx + 1, len(lines)):
                    if lines[i].startswith("## "):
                        insert_at = i
                        break
                    if lines[i].startswith("|") and "| ID |" not in lines[i] and "|----" not in lines[i]:
                        insert_at = i + 1

                timestamp = datetime.now(UTC).isoformat()
                complete_line = f"| {item_id} | {agent_id} | {timestamp} |"
                lines.insert(insert_at, complete_line)

                return _atomic_write(self.work_stream_path, "\n".join(lines) + "\n")
        except BlockingIOError:
            logger.warning(
                "Could not acquire complete lock for %s; another writer is active.",
                self.work_stream_path,
            )
            return False
        except RuntimeError as exc:
            logger.error("Could not complete item due lock setup error: %s", exc)
            return False

    def get_progress(self) -> dict[str, int]:
        """Calculate progress statistics.

        Returns:
            Dictionary with counts of total, completed, and backlog items.
        """
        content = safe_read_file(self.work_stream_path)
        if not content:
            return {"total": 0, "completed": 0, "backlog": 0}

        backlog = self.read_backlog()
        completed_count = content.count("~~") // 2

        return {
            "total": len(backlog) + completed_count,
            "completed": completed_count,
            "backlog": len(backlog),
        }

    def lint_schema(self) -> list[str]:
        """Return structural schema lint errors for the current WORK_STREAM file."""
        if not self.work_stream_path.exists():
            return ["work stream file does not exist"]
        return lint_workstream_schema(self.work_stream_path)

    def sort_and_normalize(self) -> str:
        """Sort WL sections and normalize status formatting."""
        if not self.work_stream_path.exists():
            raise FileNotFoundError(f"work stream file not found: {self.work_stream_path}")
        return normalize_workstream_sections(self.work_stream_path)
