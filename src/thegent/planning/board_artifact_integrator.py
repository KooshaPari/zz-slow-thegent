"""Board artifact integrator for parsing and integrating board artifacts."""

from __future__ import annotations

import csv
import logging
import re
from pathlib import Path
from typing import Any, ClassVar

try:
    import orjson as json
except ImportError:
    import json

logger = logging.getLogger(__name__)


class BoardArtifactParser:
    """Parser for board artifacts in various formats."""

    REQUIRED_COLUMNS: ClassVar[frozenset[str]] = frozenset({"id", "title"})
    OPTIONAL_COLUMNS: ClassVar[frozenset[str]] = frozenset(
        {"status", "priority", "source", "effort", "depends_on", "evidence"}
    )
    ALL_COLUMNS: ClassVar[frozenset[str]] = REQUIRED_COLUMNS | OPTIONAL_COLUMNS

    DEFAULT_VALUES: ClassVar[dict[str, Any]] = {
        "status": "BACKLOG",
        "priority": "P2",
        "source": "BOARD",
        "effort": "M",
        "depends_on": None,
        "evidence": None,
    }

    def parse_csv(self, file_path: Path) -> list[dict[str, Any]]:
        """Parse a CSV board artifact file.

        Args:
            file_path: Path to CSV file.

        Returns:
            List of parsed item dictionaries.
        """
        items = []
        try:
            with open(file_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    item = self._normalize_row(row)
                    if item and item.get("id"):
                        items.append(item)
        except Exception as e:
            logger.error(f"Error parsing CSV {file_path}: {e}")
        return items

    def parse_json(self, file_path: Path) -> list[dict[str, Any]]:
        """Parse a JSON board artifact file.

        Supports both list format and dict with 'items' key.

        Args:
            file_path: Path to JSON file.

        Returns:
            List of parsed item dictionaries.
        """
        items = []
        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.loads(f.read())

            if isinstance(data, list):
                items_data = data
            elif isinstance(data, dict) and "items" in data:
                items_data = data["items"]
            else:
                logger.warning(f"Unexpected JSON structure in {file_path}")
                return []

            for item in items_data:
                normalized = self._normalize_json_item(item)
                if normalized.get("id"):
                    items.append(normalized)
        except Exception as e:
            logger.error(f"Error parsing JSON {file_path}: {e}")
        return items

    def parse_markdown(self, file_path: Path) -> list[dict[str, Any]]:
        """Parse a Markdown board artifact file with table.

        Args:
            file_path: Path to Markdown file.

        Returns:
            List of parsed item dictionaries.
        """
        items = []
        try:
            content = file_path.read_text(encoding="utf-8")
            table = self._extract_markdown_table(content)
            if not table:
                return []

            headers = [h.strip().lower().replace(" ", "_") for h in table[0]]
            id_idx = next((i for i, h in enumerate(headers) if "id" in h), None)
            title_idx = next((i for i, h in enumerate(headers) if "title" in h), None)

            if id_idx is None or title_idx is None:
                logger.warning(
                    f"Markdown table missing ID or Title column in {file_path}"
                )
                return []

            for row in table[1:]:
                if not row or len(row) <= max(id_idx, title_idx):
                    continue

                item: dict[str, Any] = {}
                item["id"] = self._clean_strikethrough(row[id_idx].strip())
                item["title"] = row[title_idx].strip()

                for i, header in enumerate(headers):
                    if i < len(row) and header in self.ALL_COLUMNS:
                        value = row[i].strip()
                        item[header] = (
                            self._clean_strikethrough(value)
                            if value
                            else self.DEFAULT_VALUES.get(header)
                        )

                for col in self.ALL_COLUMNS:
                    if col not in item:
                        item[col] = self.DEFAULT_VALUES.get(col)

                if item.get("depends_on") == "-" or item.get("depends_on") == "":
                    item["depends_on"] = None

                if item.get("id"):
                    items.append(item)
        except Exception as e:
            logger.error(f"Error parsing Markdown {file_path}: {e}")
        return items

    def _extract_markdown_table(self, content: str) -> list[list[str]] | None:
        """Extract table data from markdown content.

        Args:
            content: Markdown content string.

        Returns:
            List of rows, each row is a list of cell strings, or None if no table found.
        """
        lines = content.split("\n")
        table_lines: list[int] = []

        for i, line in enumerate(lines):
            if "|" in line and line.strip().startswith("|"):
                if not re.match(r"^\|[\s\-:|]+\|$", line.strip()):
                    table_lines.append(i)

        if not table_lines:
            return None

        rows = []
        for line_idx in table_lines:
            line = lines[line_idx]
            cells = [c.strip() for c in line.split("|")[1:-1]]
            rows.append(cells)

        return rows

    def _normalize_row(self, row: dict[str, str]) -> dict[str, Any]:
        """Normalize a CSV row to standard item format.

        Args:
            row: Raw CSV row dictionary.

        Returns:
            Normalized item dictionary.
        """
        item: dict[str, Any] = {}

        for col in self.ALL_COLUMNS:
            value = row.get(col, "").strip()
            if col in row:
                if col == "depends_on" and (value in {"-", ""}):
                    value = None
                item[col] = value if value else self.DEFAULT_VALUES.get(col)
            else:
                item[col] = self.DEFAULT_VALUES.get(col)

        for col in self.REQUIRED_COLUMNS:
            if col not in row or not row[col].strip():
                return {}

        return item

    def _normalize_json_item(self, item: dict[str, Any]) -> dict[str, Any]:
        """Normalize a JSON item to standard item format.

        Args:
            item: Raw JSON item dictionary.

        Returns:
            Normalized item dictionary.
        """
        normalized: dict[str, Any] = {}

        for col in self.ALL_COLUMNS:
            value = item.get(col, item.get(col.replace("_", "")))
            if value is None or value == "":
                normalized[col] = self.DEFAULT_VALUES.get(col)
            elif col == "depends_on" and (value in {"-", ""}):
                normalized[col] = None
            else:
                normalized[col] = value

        for col in self.REQUIRED_COLUMNS:
            if col not in item or not item[col]:
                return {}

        return normalized

    def _clean_strikethrough(self, text: str) -> str:
        """Remove strikethrough formatting from text.

        Args:
            text: Text that may contain strikethrough (~~text~~).

        Returns:
            Text with strikethrough markers removed.
        """
        return re.sub(r"~~(.+?)~~", r"\1", text)


class BoardArtifactIntegrator:
    """Integrator for board artifacts from various sources."""

    EXECUTION_BOARD_PATTERNS: ClassVar[list[str]] = [
        r"CLIPROXYAPI_(\d+)_ITEM_EXECUTION_BOARD_(\d{4}-\d{2}-\d{2})\.(csv|json|md)",
        r"EXECUTION_BOARD_(\d{4}-\d{2}-\d{2})\.(csv|json|md)",
    ]

    GITHUB_IMPORT_PATTERN = (
        r"GITHUB_PROJECT_IMPORT_([A-Z0-9_]+)_(\d{4}-\d{2}-\d{2})\.csv"
    )

    def __init__(self, board_artifacts_dir: Path | str | None = None) -> None:
        """Initialize the board artifact integrator.

        Args:
            board_artifacts_dir: Directory containing board artifacts.
                                 If None, auto-discovers cliproxyapi-plusplus/docs/planning/.
        """
        if board_artifacts_dir is None:
            self.board_artifacts_dir = self._auto_discover_dir()
        else:
            self.board_artifacts_dir = Path(board_artifacts_dir)
        self.parser = BoardArtifactParser()

    def _auto_discover_dir(self) -> Path:
        """Auto-discover the board artifacts directory.

        Returns:
            Path to discovered directory or current directory as fallback.
        """

        cwd = Path.cwd()

        cliproxy_path = cwd / "cliproxyapi-plusplus" / "docs" / "planning"
        if cliproxy_path.exists():
            return cliproxy_path

        for parent in cwd.parents:
            cliproxy_path = parent / "cliproxyapi-plusplus" / "docs" / "planning"
            if cliproxy_path.exists():
                return cliproxy_path

        return cwd

    def find_board_artifacts(self) -> dict[str, Path]:
        """Find all board artifacts in the configured directory.

        Returns:
            Dictionary mapping artifact type to file path.
        """
        artifacts: dict[str, Path] = {}

        if not self.board_artifacts_dir.exists():
            return artifacts

        execution_board_csv: Path | None = None
        execution_board_json: Path | None = None
        execution_board_md: Path | None = None

        github_import_csvs: list[Path] = []

        for file_path in self.board_artifacts_dir.iterdir():
            if not file_path.is_file():
                continue

            filename = file_path.name

            if re.match(self.EXECUTION_BOARD_PATTERNS[0], filename) or re.match(
                self.EXECUTION_BOARD_PATTERNS[1], filename
            ):
                if filename.endswith(".csv"):
                    execution_board_csv = file_path
                elif filename.endswith(".json"):
                    execution_board_json = file_path
                elif filename.endswith(".md"):
                    execution_board_md = file_path

            elif re.match(self.GITHUB_IMPORT_PATTERN, filename):
                github_import_csvs.append(file_path)

        if execution_board_json:
            artifacts["execution_board_json"] = execution_board_json
        if execution_board_md:
            artifacts["execution_board_md"] = execution_board_md
        if execution_board_csv:
            artifacts["execution_board_csv"] = execution_board_csv

        for i, ghub_path in enumerate(github_import_csvs):
            artifacts[f"github_import_csv_{i}"] = ghub_path

        return artifacts

    def ingest_artifacts(self) -> list[dict[str, Any]]:
        """Ingest all board artifacts and return unified list of items.

        JSON takes precedence over CSV, which takes precedence over Markdown.

        Returns:
            List of all items from board artifacts.
        """
        artifacts = self.find_board_artifacts()
        all_items: dict[str, dict[str, Any]] = {}

        if "github_import_csv_0" in artifacts:
            items = self.parser.parse_csv(artifacts["github_import_csv_0"])
            for item in items:
                all_items[item["id"]] = item

        if "execution_board_csv" in artifacts:
            items = self.parser.parse_csv(artifacts["execution_board_csv"])
            for item in items:
                if item["id"] not in all_items:
                    all_items[item["id"]] = item

        if "execution_board_json" in artifacts:
            items = self.parser.parse_json(artifacts["execution_board_json"])
            for item in items:
                all_items[item["id"]] = item

        if "execution_board_md" in artifacts:
            items = self.parser.parse_markdown(artifacts["execution_board_md"])
            for item in items:
                if item["id"] not in all_items:
                    all_items[item["id"]] = item

        return list(all_items.values())

    def to_workstream_format(self, items: list[dict[str, Any]]) -> str:
        """Convert items to workstream markdown format.

        Args:
            items: List of work items.

        Returns:
            Markdown string in workstream format.
        """
        if not items:
            return ""

        lines = [
            "# Unified Work Stream",
            "",
            "| ID | Title | Status | Priority | Effort | Source | Depends |",
            "|----|----|--------|----------|--------|--------|---------|",
        ]

        for item in sorted(
            items, key=lambda x: (x.get("priority", "P9"), x.get("id", ""))
        ):
            item_id = item.get("id", "")

            if item.get("status") == "COMPLETED":
                item_id = f"~~{item_id}~~"

            title = item.get("title", "")
            status = item.get("status", "BACKLOG")
            priority = item.get("priority", "P2")
            effort = item.get("effort", "M")
            source = item.get("source", "BOARD")
            depends = item.get("depends_on") or "-"

            lines.append(
                f"| {item_id} | {title} | {status} | {priority} | {effort} | {source} | {depends} |"
            )

        return "\n".join(lines)


def create_board_artifact_integrator(
    board_artifacts_dir: Path | None = None,
) -> BoardArtifactIntegrator:
    """Factory function to create a BoardArtifactIntegrator.

    Args:
        board_artifacts_dir: Optional directory for board artifacts.

    Returns:
        New BoardArtifactIntegrator instance.
    """
    return BoardArtifactIntegrator(board_artifacts_dir=board_artifacts_dir)


__all__ = [
    "BoardArtifactIntegrator",
    "BoardArtifactParser",
    "create_board_artifact_integrator",
]
