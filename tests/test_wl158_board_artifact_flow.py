"""Tests for WL-158: Unified Workstream Integration for CLIProxyAPI++ Board Artifacts.

Verifies that board artifacts (MD, CSV, JSON) can be loaded, parsed, and integrated
into the thegent unified workstream loop.
"""

from pathlib import Path

import orjson as json
import pytest

from thegent.planning.board_artifact_loader import (
    BoardArtifactLoader,
    BoardItem,
    ExecutionSlice,
)


@pytest.fixture
def board_artifacts_dir(tmp_path: Path) -> Path:
    """Create temporary board artifacts directory with test data."""
    board_dir = tmp_path / "cliproxyapi-plusplus" / "docs" / "planning"
    board_dir.mkdir(parents=True)

    # Create test CSV file
    csv_content = """board_id,item_title,status,priority,lead_agent,mapped_wl,slice,effort_estimate,completion_pct
CLIPROXY-001,Core Routing & Auth Framework,In Progress,P0,routing-agent,WL-001,A,M,45
CLIPROXY-002,Provider Type Registry,Completed,P0,routing-agent,WL-002,A,S,100
CLIPROXY-020,Anthropic Provider Adapter,In Progress,P1,provider-agent,WL-020,B,M,35
CLIPROXY-158,Board Artifact Integration,In Progress,P1,workstream-agent,WL-158,C,M,25
CLIPROXY-159,Cross-Repo Board Sync,Backlog,P2,workstream-agent,WL-159,C,S,0
CLIPROXY-160,Automatic Workstream Reflection,Backlog,P1,workstream-agent,WL-160,C,M,0"""

    csv_file = board_dir / "CLIPROXYAPI_2000_ITEM_EXECUTION_BOARD_2026-02-22.csv"
    csv_file.write_text(csv_content)

    # Create test JSON file
    json_data = {
        "board_metadata": {
            "name": "CLIProxyAPI 2000-Item Execution Board",
            "generated_date": "2026-02-22T00:00:00Z",
            "version": "1.0",
            "total_items": 2000,
        },
        "execution_slices": [
            {
                "slice_id": "A",
                "name": "Core Routing & Auth",
                "item_count": 120,
                "completion_pct": 45,
                "lead_agent": "routing-agent",
                "mapped_wl_range": "WL-001..WL-015",
            },
            {
                "slice_id": "B",
                "name": "Provider Adapters",
                "item_count": 280,
                "completion_pct": 28,
                "lead_agent": "provider-agent",
                "mapped_wl_range": "WL-020..WL-050",
            },
            {
                "slice_id": "C",
                "name": "Workstream Integration",
                "item_count": 95,
                "completion_pct": 0,
                "lead_agent": "workstream-agent",
                "mapped_wl_range": "WL-158..WL-162",
            },
        ],
    }

    json_file = board_dir / "CLIPROXYAPI_2000_ITEM_EXECUTION_BOARD_2026-02-22.json"
    json_file.write_text(json.dumps(json_data, option=json.OPT_INDENT_2).decode())

    # Create test markdown file
    md_content = """# CLIProxyAPI 2000-Item Execution Board
**Generated:** 2026-02-22

## Execution Status Summary

| Status | Count |
|--------|-------|
| Backlog | 1200 |
| In Progress | 150 |
| Review | 80 |
| Completed | 570 |
"""
    md_file = board_dir / "CLIPROXYAPI_2000_ITEM_EXECUTION_BOARD_2026-02-22.md"
    md_file.write_text(md_content)

    return board_dir


class TestBoardArtifactLoader:
    """Test BoardArtifactLoader functionality."""

    def test_loader_initialization(self, board_artifacts_dir: Path) -> None:
        """Test loader can be initialized with board directory."""
        loader = BoardArtifactLoader(board_artifacts_dir)
        assert loader.board_dir == board_artifacts_dir
        assert loader.items == []
        assert loader.slices == []

    def test_load_all_artifacts(self, board_artifacts_dir: Path) -> None:
        """Test loading all available board artifacts."""
        loader = BoardArtifactLoader(board_artifacts_dir)
        result = loader.load_all()

        assert result["success"] is True
        assert len(result["loaded"]) >= 2  # At least JSON and CSV
        assert len(result["errors"]) == 0

    def test_load_json_artifact(self, board_artifacts_dir: Path) -> None:
        """Test loading JSON board artifact with metadata and slices."""
        loader = BoardArtifactLoader(board_artifacts_dir)
        loader.load_all()

        # Verify metadata loaded
        assert loader.metadata["name"] == "CLIProxyAPI 2000-Item Execution Board"
        assert loader.metadata["version"] == "1.0"

        # Verify slices loaded
        assert len(loader.slices) == 3
        assert loader.slices[0].slice_id == "A"
        assert loader.slices[0].name == "Core Routing & Auth"
        assert loader.slices[0].completion_pct == 45
        assert loader.slices[2].mapped_wl_range == "WL-158..WL-162"

    def test_load_csv_artifact(self, board_artifacts_dir: Path) -> None:
        """Test loading CSV board artifact with board items."""
        loader = BoardArtifactLoader(board_artifacts_dir)
        loader.load_all()

        # Verify items loaded
        assert len(loader.items) == 6
        assert loader.items[0].board_id == "CLIPROXY-001"
        assert loader.items[0].mapped_wl == "WL-001"
        assert loader.items[0].completion_pct == 45

        # Verify WL-158 item
        wl158_item = next(
            (item for item in loader.items if item.mapped_wl == "WL-158"), None
        )
        assert wl158_item is not None
        assert wl158_item.board_id == "CLIPROXY-158"
        assert wl158_item.status == "In Progress"
        assert wl158_item.slice_id == "C"

    def test_map_to_workstream(self, board_artifacts_dir: Path) -> None:
        """Test mapping board items to thegent WORK_STREAM.md structure."""
        loader = BoardArtifactLoader(board_artifacts_dir)
        loader.load_all()

        wl_map = loader.map_to_workstream()

        # Verify structure
        assert "wl_map" in wl_map
        assert "summary" in wl_map
        assert "timestamp" in wl_map

        # Verify summary
        assert wl_map["summary"]["total_items"] == 6
        assert wl_map["summary"]["total_slices"] == 3
        assert wl_map["summary"]["wl_ids_covered"] == 6

        # Verify specific WL mappings
        assert "WL-001" in wl_map["wl_map"]
        assert "WL-158" in wl_map["wl_map"]
        assert "WL-160" in wl_map["wl_map"]

    def test_wl158_specific_mapping(self, board_artifacts_dir: Path) -> None:
        """Test specific mapping for WL-158."""
        loader = BoardArtifactLoader(board_artifacts_dir)
        loader.load_all()
        wl_map = loader.map_to_workstream()

        wl158_data = wl_map["wl_map"]["WL-158"]
        assert wl158_data["wl_id"] == "WL-158"
        assert wl158_data["lead_agent"] == "workstream-agent"
        assert wl158_data["completion_pct"] == 25
        assert wl158_data["slice"]["slice_id"] == "C"
        assert wl158_data["slice"]["name"] == "Workstream Integration"
        assert len(wl158_data["board_items"]) == 1
        assert wl158_data["board_items"][0]["board_id"] == "CLIPROXY-158"

    def test_completion_status(self, board_artifacts_dir: Path) -> None:
        """Test aggregated completion status across slices."""
        loader = BoardArtifactLoader(board_artifacts_dir)
        loader.load_all()

        status = loader.get_completion_status()

        # Verify structure
        assert "slices" in status
        assert "overall_completion_pct" in status
        assert "timestamp" in status

        # Verify slice A
        assert status["slices"]["A"]["name"] == "Core Routing & Auth"
        assert status["slices"]["A"]["completion_pct"] == 45
        assert status["slices"]["A"]["wl_range"] == "WL-001..WL-015"

        # Verify slice C (Workstream Integration)
        assert status["slices"]["C"]["name"] == "Workstream Integration"
        assert status["slices"]["C"]["completion_pct"] == 0
        assert status["slices"]["C"]["wl_range"] == "WL-158..WL-162"

        # Verify overall completion (average of 45, 28, 0)
        assert status["overall_completion_pct"] == 24

    def test_load_all_malformed_json_keeps_state_deterministic(
        self, board_artifacts_dir: Path
    ) -> None:
        loader = BoardArtifactLoader(board_artifacts_dir)

        # Preload a good state.
        first = loader.load_all()
        assert first["success"] is True
        initial_metadata = dict(loader.metadata)
        initial_slices = list(loader.slices)

        # Corrupt the JSON artifact and rerun.
        json_file = (
            board_artifacts_dir
            / "CLIPROXYAPI_2000_ITEM_EXECUTION_BOARD_2026-02-22.json"
        )
        json_file.write_text("{bad json", encoding="utf-8")
        second = loader.load_all()

        assert second["success"] is False
        assert any("JSON load error" in err for err in second["errors"])
        assert any(str(json_file) in err for err in second["errors"])
        assert any("JSONDecodeError" in err for err in second["errors"])
        # Existing slices/metadata remain intact because parsing is isolated.
        assert loader.metadata == initial_metadata
        assert loader.slices == initial_slices

    def test_load_all_malformed_json_with_valid_csv_loads_items(
        self, board_artifacts_dir: Path
    ) -> None:
        json_file = (
            board_artifacts_dir
            / "CLIPROXYAPI_2000_ITEM_EXECUTION_BOARD_2026-02-22.json"
        )
        json_file.write_text("{bad json", encoding="utf-8")

        loader = BoardArtifactLoader(board_artifacts_dir)
        result = loader.load_all()

        assert result["success"] is False
        assert len(loader.items) == 6
        assert loader.slices == []
        assert loader.metadata == {}

    def test_load_all_keeps_state_clean_on_malformed_json(
        self, board_artifacts_dir: Path
    ) -> None:
        """Malformed JSON should report error without mutating slices/metadata."""
        json_file = (
            board_artifacts_dir
            / "CLIPROXYAPI_2000_ITEM_EXECUTION_BOARD_2026-02-22.json"
        )
        json_file.write_text('{"board_metadata": {"name": "bad"', encoding="utf-8")

        loader = BoardArtifactLoader(board_artifacts_dir)
        result = loader.load_all()

        assert result["success"] is False
        assert any(str(json_file) in err for err in result["errors"])
        assert loader.metadata == {}
        assert loader.slices == []
        # CSV still loads successfully and remains independent
        assert len(loader.items) == 6

    def test_load_all_keeps_state_clean_on_partial_csv_failure(
        self, board_artifacts_dir: Path
    ) -> None:
        """CSV parse failure should not preserve already-parsed rows."""
        csv_file = (
            board_artifacts_dir / "CLIPROXYAPI_2000_ITEM_EXECUTION_BOARD_2026-02-22.csv"
        )
        csv_file.write_text(
            "\n".join(
                [
                    "board_id,item_title,status,priority,lead_agent,mapped_wl,slice,effort_estimate,completion_pct",
                    "CLIPROXY-001,Good Item,In Progress,P0,agent,WL-001,A,M,10",
                    "CLIPROXY-002,Bad Item,In Progress,P0,agent,WL-002,A,M,not-a-number",
                ]
            ),
            encoding="utf-8",
        )

        loader = BoardArtifactLoader(board_artifacts_dir)
        result = loader.load_all()

        assert result["success"] is False
        assert any(str(csv_file) in err for err in result["errors"])
        assert loader.items == []
        # JSON still loads successfully and remains independent
        assert len(loader.slices) == 3


class TestBoardItemDataClass:
    """Test BoardItem data class."""

    def test_board_item_creation(self) -> None:
        """Test creating a BoardItem."""
        item = BoardItem(
            board_id="CLIPROXY-158",
            item_title="Board Artifact Integration",
            status="In Progress",
            priority="P1",
            lead_agent="workstream-agent",
            mapped_wl="WL-158",
            slice_id="C",
            effort_estimate="M",
            completion_pct=25,
        )

        assert item.board_id == "CLIPROXY-158"
        assert item.mapped_wl == "WL-158"
        assert item.completion_pct == 25


class TestExecutionSliceDataClass:
    """Test ExecutionSlice data class."""

    def test_execution_slice_creation(self) -> None:
        """Test creating an ExecutionSlice."""
        slice_obj = ExecutionSlice(
            slice_id="C",
            name="Workstream Integration",
            item_count=95,
            completion_pct=0,
            lead_agent="workstream-agent",
            mapped_wl_range="WL-158..WL-162",
        )

        assert slice_obj.slice_id == "C"
        assert slice_obj.name == "Workstream Integration"
        assert slice_obj.mapped_wl_range == "WL-158..WL-162"


@pytest.mark.requirement("WL-158")
class TestWL158Integration:
    """Integration tests for WL-158 acceptance criteria."""

    def test_wl158_artifacts_exist(self, board_artifacts_dir: Path) -> None:
        """Verify all required board artifact formats exist."""
        assert (
            board_artifacts_dir / "CLIPROXYAPI_2000_ITEM_EXECUTION_BOARD_2026-02-22.md"
        ).exists()
        assert (
            board_artifacts_dir / "CLIPROXYAPI_2000_ITEM_EXECUTION_BOARD_2026-02-22.csv"
        ).exists()
        assert (
            board_artifacts_dir
            / "CLIPROXYAPI_2000_ITEM_EXECUTION_BOARD_2026-02-22.json"
        ).exists()

    def test_wl158_workstream_mapping(self, board_artifacts_dir: Path) -> None:
        """Verify WL-158 is mapped and integrated into workstream."""
        loader = BoardArtifactLoader(board_artifacts_dir)
        loader.load_all()
        wl_map = loader.map_to_workstream()

        # Verify WL-158 exists in mapping
        assert "WL-158" in wl_map["wl_map"]

        # Verify execution slice C is mapped
        wl158 = wl_map["wl_map"]["WL-158"]
        assert wl158["slice"] is not None
        assert wl158["slice"]["slice_id"] == "C"
        assert wl158["lead_agent"] == "workstream-agent"

    def test_wl158_active_execution_slices_mapped(
        self, board_artifacts_dir: Path
    ) -> None:
        """Verify active execution slices are mapped into thegent WL cadence."""
        loader = BoardArtifactLoader(board_artifacts_dir)
        loader.load_all()
        status = loader.get_completion_status()

        # Verify slice C (Workstream Integration) with WL-158..WL-162 mapping
        assert "C" in status["slices"]
        assert status["slices"]["C"]["wl_range"] == "WL-158..WL-162"
        assert status["slices"]["C"]["lead_agent"] == "workstream-agent"
