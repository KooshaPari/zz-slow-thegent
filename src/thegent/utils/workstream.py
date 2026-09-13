"""Automated work stream operations (read, parse, update)."""

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from thegent.utils.helpers import safe_read_file, safe_write_file

logger = logging.getLogger(__name__)


class WorkStreamOps:
    """Automated operations on work stream files."""

    def __init__(self, base_dir: Path | None = None) -> None:
        """Initialize work stream operations.

        Args:
            base_dir: Base directory for work stream files
        """
        self.base_dir = base_dir or Path.cwd()
        self.work_stream_path = self.base_dir / "docs" / "reference" / "WORK_STREAM.md"
        self.wbs_path = self.base_dir / "docs" / "plans" / "02-UNIFIED-WBS.md"

    def read_backlog(self) -> list[dict[str, Any]]:
        """Read all items from BACKLOG section.

        Returns:
            List of backlog items with id, title, priority, depends
        """
        content = safe_read_file(self.work_stream_path)
        if not content:
            return []

        lines = content.splitlines()
        backlog_start = None
        claimed_start = None

        for i, line in enumerate(lines):
            if "## BACKLOG" in line:
                backlog_start = i
            if "## CLAIMED" in line:
                claimed_start = i
                break

        if backlog_start is None:
            return []

        items = []
        for i in range(backlog_start + 2, claimed_start or len(lines)):
            line = lines[i]
            if line.startswith("|") and "| ID |" not in line and "|----" not in line:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 6:
                    item_id = parts[1]
                    title = parts[2]
                    priority = parts[4]
                    depends = parts[5]

                    if item_id and item_id != "(none)" and not item_id.startswith("*"):
                        items.append(
                            {
                                "id": item_id,
                                "title": title,
                                "priority": priority,
                                "depends": depends,
                            }
                        )

        return items

    def claim_item(self, item_id: str, agent_id: str) -> bool:
        """Claim an item by adding it to CLAIMED section.

        Args:
            item_id: Work item ID
            agent_id: Agent identifier

        Returns:
            True if successful
        """
        content = safe_read_file(self.work_stream_path)
        if not content:
            return False

        lines = content.splitlines()
        claimed_start = None

        for i, line in enumerate(lines):
            if "## CLAIMED" in line:
                claimed_start = i
                break

        if claimed_start is None:
            return False

        # Find insertion point (after header, before next section)
        insert_idx = claimed_start + 2
        for i in range(claimed_start + 1, len(lines)):
            if lines[i].startswith("##"):
                insert_idx = i
                break
            if lines[i].startswith("|") and "| ID |" not in lines[i] and "|----" not in lines[i]:
                insert_idx = i + 1

        # Create claim entry
        timestamp = datetime.now(UTC).isoformat()
        claim_line = f"| {item_id} | {agent_id} | {timestamp} |"

        # Insert claim
        lines.insert(insert_idx, claim_line)

        return safe_write_file(self.work_stream_path, "\n".join(lines) + "\n")

    def complete_item(self, item_id: str, agent_id: str) -> bool:
        """Mark an item as complete.

        Args:
            item_id: Work item ID
            agent_id: Agent identifier

        Returns:
            True if successful
        """
        content = safe_read_file(self.work_stream_path)
        if not content:
            return False

        lines = content.splitlines()

        # Remove from CLAIMED
        in_claimed = False
        new_lines = []
        for line in lines:
            if "## CLAIMED" in line:
                in_claimed = True
                new_lines.append(line)
                continue
            if in_claimed and line.startswith("##"):
                in_claimed = False
                new_lines.append(line)
                continue
            if in_claimed and f"| {item_id} |" in line:
                continue  # Skip this line
            new_lines.append(line)

        # Add to COMPLETED
        completed_start = None
        for i, line in enumerate(new_lines):
            if "## COMPLETED" in line:
                completed_start = i
                break

        if completed_start is None:
            # Add COMPLETED section
            new_lines.append("")
            new_lines.append("## COMPLETED")
            new_lines.append("")
            new_lines.append("| ID | Agent | Completed |")
            new_lines.append("|----|-------|-----------|")
            completed_start = len(new_lines) - 1

        timestamp = datetime.now(UTC).isoformat()
        complete_line = f"| {item_id} | {agent_id} | {timestamp} |"

        insert_idx = completed_start + 3
        new_lines.insert(insert_idx, complete_line)

        return safe_write_file(self.work_stream_path, "\n".join(new_lines) + "\n")
