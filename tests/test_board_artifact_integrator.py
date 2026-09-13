"""Tests for board artifact integrator module.

@trace WL-158
"""

from pathlib import Path

import orjson as json
import pytest

from thegent.planning.board_artifact_integrator import (
    BoardArtifactIntegrator,
    BoardArtifactParser,
    create_board_artifact_integrator,
)


class TestBoardArtifactParser:
    """Tests for BoardArtifactParser."""

    def test_parse_csv_basic(self, tmp_path: Path) -> None:
        """Test parsing basic CSV board artifact."""
        csv_file = tmp_path / "board.csv"
        csv_file.write_text(
            "id,title,status,priority,source,effort,depends_on,evidence\n"
            "CAB-001,First task,BACKLOG,P0,BOARD,S,-,doc1.md\n"
            "CAB-002,Second task,IN_PROGRESS,P1,BOARD,M,CAB-001,doc2.md\n"
        )

        parser = BoardArtifactParser()
        items = parser.parse_csv(csv_file)

        assert len(items) == 2
        assert items[0]["id"] == "CAB-001"
        assert items[0]["title"] == "First task"
        assert items[0]["status"] == "BACKLOG"
        assert items[0]["priority"] == "P0"
        assert items[0]["depends_on"] is None

        assert items[1]["id"] == "CAB-002"
        assert items[1]["depends_on"] == "CAB-001"

    def test_parse_json_list(self, tmp_path: Path) -> None:
        """Test parsing JSON board artifact (list format)."""
        json_file = tmp_path / "board.json"
        json_file.write_text(
            json.dumps(
                [
                    {"id": "JB-001", "title": "Task A", "status": "BACKLOG", "priority": "P1"},
                    {"id": "JB-002", "title": "Task B", "status": "COMPLETED", "priority": "P2"},
                ]
            )
        ).decode()

        parser = BoardArtifactParser()
        items = parser.parse_json(json_file)

        assert len(items) == 2
        assert items[0]["id"] == "JB-001"
        assert items[1]["status"] == "COMPLETED"

    def test_parse_json_dict_with_items(self, tmp_path: Path) -> None:
        """Test parsing JSON board artifact (dict with items key)."""
        json_file = tmp_path / "board.json"
        json_file.write_text(
            json.dumps(
                {
                    "items": [
                        {"id": "JD-001", "title": "Task X", "priority": "P0"},
                        {"id": "JD-002", "title": "Task Y", "priority": "P1"},
                    ]
                }
            )
        ).decode()

        parser = BoardArtifactParser()
        items = parser.parse_json(json_file)

        assert len(items) == 2
        assert items[0]["id"] == "JD-001"

    def test_parse_markdown_table(self, tmp_path: Path) -> None:
        """Test parsing Markdown board artifact with table."""
        md_file = tmp_path / "board.md"
        md_file.write_text(
            "# Board\n\n"
            "| ID | Title | Status | Priority | Source | Effort | Depends | Evidence |\n"
            "|----|----|--------|----------|--------|--------|---------|----------|\n"
            "| MD-001 | Task Alpha | BACKLOG | P0 | BOARD | M | - | ref1 |\n"
            "| MD-002 | Task Beta | IN_PROGRESS | P1 | BOARD | L | MD-001 | ref2 |\n"
            "| ~~MD-003~~ | Task Gamma | COMPLETED | P2 | BOARD | S | - | ref3 |\n"
        )

        parser = BoardArtifactParser()
        items = parser.parse_markdown(md_file)

        assert len(items) == 3
        assert items[0]["id"] == "MD-001"
        assert items[0]["title"] == "Task Alpha"
        assert items[1]["depends_on"] == "MD-001"
        # Completed item still parsed, strikethrough removed
        assert items[2]["id"] == "MD-003"
        assert items[2]["status"] == "COMPLETED"

    def test_parse_csv_missing_columns(self, tmp_path: Path) -> None:
        """Test parsing CSV with missing optional columns."""
        csv_file = tmp_path / "board.csv"
        csv_file.write_text("id,title,status,priority\nTEST-001,Task,BACKLOG,P1\n")

        parser = BoardArtifactParser()
        items = parser.parse_csv(csv_file)

        assert len(items) == 1
        assert items[0]["id"] == "TEST-001"
        assert items[0]["source"] == "BOARD"  # Default
        assert items[0]["depends_on"] is None

    def test_parse_json_invalid_file(self, tmp_path: Path) -> None:
        """Test parsing invalid JSON file."""
        json_file = tmp_path / "invalid.json"
        json_file.write_text("not valid json {]")

        parser = BoardArtifactParser()
        items = parser.parse_json(json_file)

        assert items == []

    def test_parse_markdown_no_table(self, tmp_path: Path) -> None:
        """Test parsing Markdown with no table."""
        md_file = tmp_path / "no_table.md"
        md_file.write_text("# Just Prose\n\nNo table here.")

        parser = BoardArtifactParser()
        items = parser.parse_markdown(md_file)

        assert items == []


class TestBoardArtifactIntegrator:
    """Tests for BoardArtifactIntegrator."""

    @pytest.fixture
    def board_dir(self, tmp_path: Path) -> Path:
        """Create a board artifacts directory with sample files."""
        board_dir = tmp_path / "board-artifacts"
        board_dir.mkdir()

        # Create sample execution board CSV
        csv_file = board_dir / "CLIPPROXYAPI_2000_ITEM_EXECUTION_BOARD_2026-02-22.csv"
        csv_file.write_text(
            "id,title,status,priority,source,effort,depends_on,evidence\n"
            "CLI-001,Integration task 1,BACKLOG,P0,BOARD,M,-,doc1.md\n"
            "CLI-002,Integration task 2,BACKLOG,P1,BOARD,S,CLI-001,doc2.md\n"
        )

        return board_dir

    def test_find_board_artifacts_csv(self, board_dir: Path) -> None:
        """Test finding board artifacts (CSV)."""
        integrator = BoardArtifactIntegrator(board_artifacts_dir=board_dir)
        artifacts = integrator.find_board_artifacts()

        assert "execution_board_csv" in artifacts
        assert artifacts["execution_board_csv"].name == "CLIPPROXYAPI_2000_ITEM_EXECUTION_BOARD_2026-02-22.csv"

    def test_find_board_artifacts_json(self, board_dir: Path) -> None:
        """Test finding board artifacts (JSON takes priority)."""
        json_file = board_dir / "CLIPPROXYAPI_2000_ITEM_EXECUTION_BOARD_2026-02-22.json"
        json_file.write_text(json.dumps([{"id": "J-001", "title": "JSON task"}]).decode())

        integrator = BoardArtifactIntegrator(board_artifacts_dir=board_dir)
        artifacts = integrator.find_board_artifacts()

        assert "execution_board_json" in artifacts
        assert "execution_board_csv" in artifacts

    def test_find_board_artifacts_github_import(self, board_dir: Path) -> None:
        """Test finding GitHub import CSV."""
        import_file = board_dir / "GITHUB_PROJECT_IMPORT_CLIPPROXYAPI_2000_2026-02-22.csv"
        import_file.write_text("id,title\nGH-001,GitHub task\n")

        integrator = BoardArtifactIntegrator(board_artifacts_dir=board_dir)
        artifacts = integrator.find_board_artifacts()

        assert "github_import_csv" in artifacts

    def test_ingest_artifacts_csv(self, board_dir: Path) -> None:
        """Test ingesting board artifacts from CSV."""
        integrator = BoardArtifactIntegrator(board_artifacts_dir=board_dir)
        items = integrator.ingest_artifacts()

        assert len(items) == 2
        assert items[0]["id"] == "CLI-001"
        assert items[0]["title"] == "Integration task 1"
        assert items[1]["depends_on"] == "CLI-001"

    def test_ingest_artifacts_json_precedence(self, board_dir: Path) -> None:
        """Test that JSON takes precedence over CSV."""
        # Create JSON with different content
        json_file = board_dir / "CLIPPROXYAPI_2000_ITEM_EXECUTION_BOARD_2026-02-22.json"
        json_file.write_text(json.dumps([{"id": "JSON-001", "title": "JSON task", "status": "BACKLOG"}]).decode())

        integrator = BoardArtifactIntegrator(board_artifacts_dir=board_dir)
        items = integrator.ingest_artifacts()

        assert len(items) == 1
        assert items[0]["id"] == "JSON-001"

    def test_ingest_artifacts_empty_dir(self, tmp_path: Path) -> None:
        """Test ingesting from empty directory."""
        integrator = BoardArtifactIntegrator(board_artifacts_dir=tmp_path)
        items = integrator.ingest_artifacts()

        assert items == []

    def test_to_workstream_format_basic(self, board_dir: Path) -> None:
        """Test converting items to workstream format."""
        integrator = BoardArtifactIntegrator(board_artifacts_dir=board_dir)
        items = integrator.ingest_artifacts()

        result = integrator.to_workstream_format(items)

        assert "| CLI-001 |" in result
        assert "| CLI-002 |" in result
        assert "| Source | Priority | Effort | Status | Depends |" in result

    def test_to_workstream_format_completed_strikethrough(self) -> None:
        """Test that completed items are marked with strikethrough."""
        items = [
            {
                "id": "ITEM-001",
                "title": "Completed task",
                "status": "COMPLETED",
                "source": "BOARD",
                "priority": "P0",
                "effort": "M",
            }
        ]

        integrator = BoardArtifactIntegrator()
        result = integrator.to_workstream_format(items)

        assert "~~ITEM-001~~" in result

    def test_to_workstream_format_empty_list(self) -> None:
        """Test converting empty list to workstream format."""
        integrator = BoardArtifactIntegrator()
        result = integrator.to_workstream_format([])

        assert result == ""

    def test_create_board_artifact_integrator_factory(self, tmp_path: Path) -> None:
        """Test factory function."""
        integrator = create_board_artifact_integrator(board_artifacts_dir=tmp_path)

        assert isinstance(integrator, BoardArtifactIntegrator)
        assert integrator.board_artifacts_dir == tmp_path

    def test_integrator_auto_discover_cliproxy_dir(self, tmp_path: Path) -> None:
        """Test auto-discovery of cliproxyapi-plusplus directory."""
        # Create the expected directory structure
        cliproxy_dir = tmp_path / "cliproxyapi-plusplus" / "docs" / "planning"
        cliproxy_dir.mkdir(parents=True)

        # Create CSV file
        csv_file = cliproxy_dir / "CLIPPROXYAPI_2000_ITEM_EXECUTION_BOARD_2026-02-22.csv"
        csv_file.write_text(
            "id,title,status,priority,source,effort,depends_on,evidence\n"
            "AUTO-001,Auto-discovered,BACKLOG,P1,BOARD,M,-,doc.md\n"
        )

        # Change to tmp_path to test auto-discovery
        import os

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            integrator = BoardArtifactIntegrator()
            items = integrator.ingest_artifacts()

            assert len(items) == 1
            assert items[0]["id"] == "AUTO-001"
        finally:
            os.chdir(old_cwd)


@pytest.mark.requirement("WL-158")
class TestWL158Integration:
    """Tests for WL-158 acceptance criteria."""

    def test_wl158_board_artifact_ingestion(self, tmp_path: Path) -> None:
        """Test that board artifacts can be ingested and mapped to workstream items.

        WL-158 Acceptance Criteria:
        - Board artifacts ready in `cliproxyapi-plusplus/docs/planning/`
        - Must support: MD, CSV, JSON formats
        - Must map to workstream items with ID, title, priority, effort, status, depends_on
        """
        board_dir = tmp_path / "cliproxyapi-plusplus" / "docs" / "planning"
        board_dir.mkdir(parents=True)

        # Create all three artifact formats
        csv_file = board_dir / "CLIPPROXYAPI_2000_ITEM_EXECUTION_BOARD_2026-02-22.csv"
        csv_file.write_text(
            "id,title,status,priority,source,effort,depends_on,evidence\n"
            "CAB-001,CSV artifact task,BACKLOG,P0,BOARD,M,-,ref1.md\n"
        )

        json_file = board_dir / "CLIPPROXYAPI_2000_ITEM_EXECUTION_BOARD_2026-02-22.json"
        json_file.write_text(
            json.dumps(
                [{"id": "JAB-001", "title": "JSON artifact task", "status": "BACKLOG", "priority": "P1"}]
            ).decode()
        )

        md_file = board_dir / "CLIPPROXYAPI_2000_ITEM_EXECUTION_BOARD_2026-02-22.md"
        md_file.write_text(
            "# Board\n\n"
            "| ID | Title | Status | Priority | Source | Effort | Depends | Evidence |\n"
            "|----|----|--------|----------|--------|--------|---------|----------|\n"
            "| MAB-001 | MD artifact task | BACKLOG | P2 | BOARD | S | - | ref3.md |\n"
        )

        import_file = board_dir / "GITHUB_PROJECT_IMPORT_CLIPPROXYAPI_2000_2026-02-22.csv"
        import_file.write_text("id,title\nGHI-001,GitHub import task\n")

        # Test ingestion of each format
        integrator_csv = BoardArtifactIntegrator(board_artifacts_dir=board_dir)
        # JSON has priority, so we verify by removing JSON file
        json_file.unlink()
        items = integrator_csv.ingest_artifacts()
        assert len(items) == 1
        assert items[0]["id"] == "CAB-001"

        # Verify workstream format output
        ws_format = integrator_csv.to_workstream_format(items)
        assert "| CAB-001 |" in ws_format
        assert "CSV artifact task" in ws_format
        assert "P0" in ws_format

    def test_wl158_board_artifact_formats_compatibility(self, tmp_path: Path) -> None:
        """Test that all required artifact formats are supported.

        WL-158 Evidence:
        - `CLIPPROXYAPI_2000_ITEM_EXECUTION_BOARD_2026-02-22.md`
        - `CLIPPROXYAPI_2000_ITEM_EXECUTION_BOARD_2026-02-22.csv`
        - `CLIPPROXYAPI_2000_ITEM_EXECUTION_BOARD_2026-02-22.json`
        - `GITHUB_PROJECT_IMPORT_CLIPPROXYAPI_2000_2026-02-22.csv`
        """
        parser = BoardArtifactParser()

        # Test CSV parsing
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("id,title\nC-1,Task\n")
        csv_items = parser.parse_csv(csv_file)
        assert len(csv_items) == 1

        # Test JSON parsing
        json_file = tmp_path / "test.json"
        json_file.write_text(json.dumps([{"id": "J-1", "title": "Task"}]).decode())
        json_items = parser.parse_json(json_file)
        assert len(json_items) == 1

        # Test MD parsing (with minimum required columns for board table)
        md_file = tmp_path / "test.md"
        md_file.write_text("| ID | Title | Status |\n|-----|-------|--------|\n| M-1 | Task | BACKLOG |\n")
        md_items = parser.parse_markdown(md_file)
        assert len(md_items) == 1
