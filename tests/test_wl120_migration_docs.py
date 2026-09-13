"""Tests verifying WL-120 migration documentation exists.

# @trace WL-120 B90-W2-F1
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestCliDagExtractionDocs:
    """docs/changes/cli-dag-extraction/ must exist with required files."""

    # @trace WL-120 B90-W2-F1

    def test_proposal_exists(self) -> None:
        """docs/changes/cli-dag-extraction/proposal.md must exist."""
        proposal = ROOT / "docs" / "changes" / "cli-dag-extraction" / "proposal.md"
        assert proposal.exists(), f"Missing migration proposal: {proposal}"

    def test_design_exists(self) -> None:
        """docs/changes/cli-dag-extraction/design.md must exist."""
        design = ROOT / "docs" / "changes" / "cli-dag-extraction" / "design.md"
        assert design.exists(), f"Missing migration design: {design}"

    def test_tasks_exists(self) -> None:
        """docs/changes/cli-dag-extraction/tasks.md must exist."""
        tasks = ROOT / "docs" / "changes" / "cli-dag-extraction" / "tasks.md"
        assert tasks.exists(), f"Missing migration tasks: {tasks}"

    def test_proposal_mentions_wl120(self) -> None:
        """proposal.md must reference WL-120."""
        proposal = ROOT / "docs" / "changes" / "cli-dag-extraction" / "proposal.md"
        content = proposal.read_text(encoding="utf-8")
        assert "WL-120" in content or "wl-120" in content.lower(), (
            "cli-dag-extraction/proposal.md must reference WL-120"
        )

    def test_proposal_mentions_cli_dag(self) -> None:
        """proposal.md must mention cli_dag.py extraction."""
        proposal = ROOT / "docs" / "changes" / "cli-dag-extraction" / "proposal.md"
        content = proposal.read_text(encoding="utf-8")
        assert "cli_dag" in content or "cli.py" in content, (
            "cli-dag-extraction/proposal.md must describe the CLI DAG extraction"
        )


class TestMcpServerExtractionDocs:
    """docs/changes/mcp-server-extraction/ must exist with required files."""

    # @trace WL-120 B90-W2-F1

    def test_proposal_exists(self) -> None:
        """docs/changes/mcp-server-extraction/proposal.md must exist."""
        proposal = ROOT / "docs" / "changes" / "mcp-server-extraction" / "proposal.md"
        assert proposal.exists(), f"Missing migration proposal: {proposal}"

    def test_design_exists(self) -> None:
        """docs/changes/mcp-server-extraction/design.md must exist."""
        design = ROOT / "docs" / "changes" / "mcp-server-extraction" / "design.md"
        assert design.exists(), f"Missing migration design: {design}"

    def test_tasks_exists(self) -> None:
        """docs/changes/mcp-server-extraction/tasks.md must exist."""
        tasks = ROOT / "docs" / "changes" / "mcp-server-extraction" / "tasks.md"
        assert tasks.exists(), f"Missing migration tasks: {tasks}"

    def test_proposal_mentions_server(self) -> None:
        """proposal.md must mention server.py or mcp."""
        proposal = ROOT / "docs" / "changes" / "mcp-server-extraction" / "proposal.md"
        content = proposal.read_text(encoding="utf-8")
        assert "server.py" in content or "mcp" in content.lower(), (
            "mcp-server-extraction/proposal.md must describe server.py extraction"
        )

    def test_design_mentions_tool_groups(self) -> None:
        """design.md must document extracted tool groups."""
        design = ROOT / "docs" / "changes" / "mcp-server-extraction" / "design.md"
        content = design.read_text(encoding="utf-8")
        assert "tools_" in content, (
            "mcp-server-extraction/design.md must list extracted tool group modules"
        )
