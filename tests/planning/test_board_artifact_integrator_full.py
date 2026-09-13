"""Comprehensive tests for thegent.planning.board_artifact_integrator module."""

from __future__ import annotations

from pathlib import Path

try:
    import orjson as json
except ImportError:
    import json


class TestBoardArtifactParserCsv:
    """Tests for BoardArtifactParser.parse_csv method."""

    def test_parse_basic_csv(self, tmp_path: Path) -> None:
        """Basic CSV parsing works."""
        from thegent.planning.board_artifact_integrator import BoardArtifactParser

        csv_file = tmp_path / "test.csv"
        csv_file.write_text(
            "id,title,status,priority,source,effort,depends_on,evidence\n"
            "TST-001,Test Task,BACKLOG,P0,BOARD,M,-,ref1.md\n"
        )
        parser = BoardArtifactParser()
        items = parser.parse_csv(csv_file)
        assert len(items) == 1
        assert items[0]["id"] == "TST-001"
        assert items[0]["title"] == "Test Task"

    def test_parse_csv_missing_optional_columns(self, tmp_path: Path) -> None:
        """CSV with only required columns parses with defaults."""
        from thegent.planning.board_artifact_integrator import BoardArtifactParser

        csv_file = tmp_path / "test.csv"
        csv_file.write_text("id,title\nTST-001,Test\n")
        parser = BoardArtifactParser()
        items = parser.parse_csv(csv_file)
        assert len(items) == 1
        assert items[0]["status"] == "BACKLOG"
        assert items[0]["priority"] == "P2"

    def test_parse_csv_multiple_rows(self, tmp_path: Path) -> None:
        """Multiple rows parse correctly."""
        from thegent.planning.board_artifact_integrator import BoardArtifactParser

        csv_file = tmp_path / "test.csv"
        csv_file.write_text("id,title,status,priority\nTST-001,Task1,BACKLOG,P0\nTST-002,Task2,IN_PROGRESS,P1\n")
        parser = BoardArtifactParser()
        items = parser.parse_csv(csv_file)
        assert len(items) == 2

    def test_parse_csv_depends_on_normalization(self, tmp_path: Path) -> None:
        """depends_on '-' is converted to None."""
        from thegent.planning.board_artifact_integrator import BoardArtifactParser

        csv_file = tmp_path / "test.csv"
        csv_file.write_text("id,title,status,priority,depends_on\nTST-001,Task1,BACKLOG,P0,-\n")
        parser = BoardArtifactParser()
        items = parser.parse_csv(csv_file)
        assert items[0]["depends_on"] is None

    def test_parse_csv_file_not_found(self, tmp_path: Path) -> None:
        """Non-existent file returns empty list."""
        from thegent.planning.board_artifact_integrator import BoardArtifactParser

        parser = BoardArtifactParser()
        items = parser.parse_csv(tmp_path / "nonexistent.csv")
        assert items == []


class TestBoardArtifactParserJson:
    """Tests for BoardArtifactParser.parse_json method."""

    def test_parse_json_list_format(self, tmp_path: Path) -> None:
        """JSON list format parses correctly."""
        from thegent.planning.board_artifact_integrator import BoardArtifactParser

        json_file = tmp_path / "test.json"
        json_file.write_text(
            json.dumps(
                [
                    {
                        "id": "TST-001",
                        "title": "Task1",
                        "status": "BACKLOG",
                        "priority": "P0",
                    }
                ]
            ).decode("utf-8")
        )
        parser = BoardArtifactParser()
        items = parser.parse_json(json_file)
        assert len(items) == 1
        assert items[0]["id"] == "TST-001"

    def test_parse_json_dict_format(self, tmp_path: Path) -> None:
        """JSON dict with 'items' key parses correctly."""
        from thegent.planning.board_artifact_integrator import BoardArtifactParser

        json_file = tmp_path / "test.json"
        json_file.write_text(json.dumps({"items": [{"id": "TST-001", "title": "Task1"}]}).decode("utf-8"))
        parser = BoardArtifactParser()
        items = parser.parse_json(json_file)
        assert len(items) == 1

    def test_parse_json_invalid(self, tmp_path: Path) -> None:
        """Invalid JSON returns empty list."""
        from thegent.planning.board_artifact_integrator import BoardArtifactParser

        json_file = tmp_path / "test.json"
        json_file.write_text("not valid json")
        parser = BoardArtifactParser()
        items = parser.parse_json(json_file)
        assert items == []


class TestBoardArtifactParserMarkdown:
    """Tests for BoardArtifactParser.parse_markdown method."""

    def test_parse_markdown_basic(self, tmp_path: Path) -> None:
        """Basic markdown table parsing works."""
        from thegent.planning.board_artifact_integrator import BoardArtifactParser

        md_file = tmp_path / "test.md"
        md_file.write_text(
            "# Board\n\n"
            "| ID | Title | Status | Priority |\n"
            "|----|-------|--------|----------|\n"
            "| TST-001 | Task1 | BACKLOG | P0 |\n"
        )
        parser = BoardArtifactParser()
        items = parser.parse_markdown(md_file)
        assert len(items) == 1
        assert items[0]["id"] == "TST-001"

    def test_parse_markdown_no_table(self, tmp_path: Path) -> None:
        """Markdown without table returns empty list."""
        from thegent.planning.board_artifact_integrator import BoardArtifactParser

        md_file = tmp_path / "test.md"
        md_file.write_text("# Just some text\n\nNo table here.")
        parser = BoardArtifactParser()
        items = parser.parse_markdown(md_file)
        assert items == []

    def test_parse_markdown_strikethrough(self, tmp_path: Path) -> None:
        """Strikethrough is removed from IDs."""
        from thegent.planning.board_artifact_integrator import BoardArtifactParser

        md_file = tmp_path / "test.md"
        md_file.write_text(
            "# Board\n\n| ID | Title | Status |\n|----|-------|--------|\n| ~~TST-001~~ | Task1 | COMPLETED |\n"
        )
        parser = BoardArtifactParser()
        items = parser.parse_markdown(md_file)
        assert items[0]["id"] == "TST-001"
        assert items[0]["status"] == "COMPLETED"


class TestBoardArtifactParserHelpers:
    """Tests for BoardArtifactParser helper methods."""

    def test_clean_strikethrough_simple(self) -> None:
        """Simple strikethrough is cleaned."""
        from thegent.planning.board_artifact_integrator import BoardArtifactParser

        parser = BoardArtifactParser()
        result = parser._clean_strikethrough("~~text~~")
        assert result == "text"

    def test_clean_strikethrough_no_change(self) -> None:
        """Text without strikethrough is unchanged."""
        from thegent.planning.board_artifact_integrator import BoardArtifactParser

        parser = BoardArtifactParser()
        result = parser._clean_strikethrough("normal text")
        assert result == "normal text"


class TestBoardArtifactIntegratorInit:
    """Tests for BoardArtifactIntegrator initialization."""

    def test_init_with_path(self, tmp_path: Path) -> None:
        """Initializes with provided path."""
        from thegent.planning.board_artifact_integrator import BoardArtifactIntegrator

        integrator = BoardArtifactIntegrator(board_artifacts_dir=tmp_path)
        assert integrator.board_artifacts_dir == tmp_path

    def test_auto_discover_finds_directory(self, tmp_path: Path) -> None:
        """Auto-discovery finds cliproxyapi-plusplus directory."""
        from thegent.planning.board_artifact_integrator import BoardArtifactIntegrator

        cliproxy_dir = tmp_path / "cliproxyapi-plusplus" / "docs" / "planning"
        cliproxy_dir.mkdir(parents=True)
        old_cwd = Path.cwd()
        try:
            import os

            os.chdir(tmp_path)
            integrator = BoardArtifactIntegrator()
            assert integrator.board_artifacts_dir == cliproxy_dir
        finally:
            os.chdir(old_cwd)


class TestBoardArtifactIntegratorFindArtifacts:
    """Tests for BoardArtifactIntegrator.find_board_artifacts method."""

    def test_finds_csv_execution_board(self, tmp_path: Path) -> None:
        """Finds execution board CSV."""
        from thegent.planning.board_artifact_integrator import BoardArtifactIntegrator

        board_dir = tmp_path / "planning"
        board_dir.mkdir()
        (board_dir / "CLIPROXYAPI_2000_ITEM_EXECUTION_BOARD_2026-02-22.csv").write_text("id,title\nT1,Task1\n")
        integrator = BoardArtifactIntegrator(board_artifacts_dir=board_dir)
        artifacts = integrator.find_board_artifacts()
        assert "execution_board_csv" in artifacts

    def test_finds_json_execution_board(self, tmp_path: Path) -> None:
        """Finds execution board JSON."""
        from thegent.planning.board_artifact_integrator import BoardArtifactIntegrator

        board_dir = tmp_path / "planning"
        board_dir.mkdir()
        (board_dir / "CLIPROXYAPI_2000_ITEM_EXECUTION_BOARD_2026-02-22.json").write_text(
            json.dumps([{"id": "T1", "title": "Task1"}]).decode("utf-8")
        )
        integrator = BoardArtifactIntegrator(board_artifacts_dir=board_dir)
        artifacts = integrator.find_board_artifacts()
        assert "execution_board_json" in artifacts

    def test_finds_github_import(self, tmp_path: Path) -> None:
        """Finds GitHub import CSV."""
        from thegent.planning.board_artifact_integrator import BoardArtifactIntegrator

        board_dir = tmp_path / "planning"
        board_dir.mkdir()
        (board_dir / "GITHUB_PROJECT_IMPORT_CLIPROXYAPI_2000_2026-02-22.csv").write_text("id,title\nT1,Task1\n")
        integrator = BoardArtifactIntegrator(board_artifacts_dir=board_dir)
        artifacts = integrator.find_board_artifacts()
        assert any("github_import_csv" in k for k in artifacts)


class TestBoardArtifactIntegratorIngest:
    """Tests for BoardArtifactIntegrator.ingest_artifacts method."""

    def test_ingest_empty_directory(self, tmp_path: Path) -> None:
        """Empty directory returns empty list."""
        from thegent.planning.board_artifact_integrator import BoardArtifactIntegrator

        integrator = BoardArtifactIntegrator(board_artifacts_dir=tmp_path)
        items = integrator.ingest_artifacts()
        assert items == []

    def test_ingest_json_precedence(self, tmp_path: Path) -> None:
        """JSON takes precedence over CSV."""
        from thegent.planning.board_artifact_integrator import BoardArtifactIntegrator

        board_dir = tmp_path / "planning"
        board_dir.mkdir()
        (board_dir / "CLIPROXYAPI_2000_ITEM_EXECUTION_BOARD_2026-02-22.csv").write_text(
            "id,title,status\nT1,CSVTask,IN_PROGRESS\n"
        )
        (board_dir / "CLIPROXYAPI_2000_ITEM_EXECUTION_BOARD_2026-02-22.json").write_text(
            json.dumps([{"id": "T1", "title": "JSONTask", "status": "BACKLOG"}]).decode("utf-8")
        )
        integrator = BoardArtifactIntegrator(board_artifacts_dir=board_dir)
        items = integrator.ingest_artifacts()
        assert items[0]["title"] == "JSONTask"


class TestBoardArtifactIntegratorToWorkstream:
    """Tests for BoardArtifactIntegrator.to_workstream_format method."""

    def test_empty_list_returns_empty_string(self) -> None:
        """Empty list returns empty string."""
        from thegent.planning.board_artifact_integrator import BoardArtifactIntegrator

        integrator = BoardArtifactIntegrator()
        result = integrator.to_workstream_format([])
        assert result == ""

    def test_single_item_format(self) -> None:
        """Single item is formatted correctly."""
        from thegent.planning.board_artifact_integrator import BoardArtifactIntegrator

        integrator = BoardArtifactIntegrator()
        items = [{"id": "TST-001", "title": "Task1", "status": "BACKLOG", "priority": "P0"}]
        result = integrator.to_workstream_format(items)
        assert "| TST-001 |" in result
        assert "Task1" in result

    def test_completed_item_strikethrough(self) -> None:
        """Completed items have strikethrough."""
        from thegent.planning.board_artifact_integrator import BoardArtifactIntegrator

        integrator = BoardArtifactIntegrator()
        items = [{"id": "TST-001", "title": "Task1", "status": "COMPLETED", "priority": "P0"}]
        result = integrator.to_workstream_format(items)
        assert "~~TST-001~~" in result

    def test_sorted_by_priority(self) -> None:
        """Items are sorted by priority."""
        from thegent.planning.board_artifact_integrator import BoardArtifactIntegrator

        integrator = BoardArtifactIntegrator()
        items = [
            {"id": "TST-002", "title": "Task2", "status": "BACKLOG", "priority": "P1"},
            {"id": "TST-001", "title": "Task1", "status": "BACKLOG", "priority": "P0"},
        ]
        result = integrator.to_workstream_format(items)
        p0_pos = result.find("TST-001")
        p1_pos = result.find("TST-002")
        assert p0_pos < p1_pos


class TestCreateBoardArtifactIntegrator:
    """Tests for create_board_artifact_integrator factory function."""

    def test_creates_integrator(self, tmp_path: Path) -> None:
        """Factory creates BoardArtifactIntegrator instance."""
        from thegent.planning.board_artifact_integrator import (
            BoardArtifactIntegrator,
            create_board_artifact_integrator,
        )

        integrator = create_board_artifact_integrator(board_artifacts_dir=tmp_path)
        assert isinstance(integrator, BoardArtifactIntegrator)
        assert integrator.board_artifacts_dir == tmp_path
