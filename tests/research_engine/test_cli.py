"""Tests for research_engine CLI — @trace FR-RES-040"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from research_engine.cli import app

runner = CliRunner()


def test_topics_command() -> None:
    """Test topics command lists detected topics."""
    with patch("research_engine.cli.TopicExtractor") as mock_cls:
        mock_cls.return_value.extract.return_value = ["python", "rust"]
        result = runner.invoke(app, ["topics"])
    assert result.exit_code == 0
    assert "python" in result.output


def test_digest_command() -> None:
    """Test digest command generates markdown digest."""
    with (
        patch("research_engine.cli.ResearchStore") as mock_store_cls,
        patch("research_engine.cli.DigestGenerator") as mock_gen_cls,
    ):
        mock_store = MagicMock()
        mock_store_cls.return_value = mock_store
        mock_gen = MagicMock()
        mock_gen.generate.return_value = "## Digest\n\n- item"
        mock_gen_cls.return_value = mock_gen
        result = runner.invoke(app, ["digest"])
    assert result.exit_code == 0
    assert "Digest" in result.output


def test_search_command() -> None:
    """Test search command finds items by query."""
    with patch("research_engine.cli.ResearchStore") as mock_store_cls:
        mock_store = MagicMock()
        mock_store.search.return_value = []
        mock_store_cls.return_value = mock_store
        result = runner.invoke(app, ["search", "python"])
    assert result.exit_code == 0


def test_crawl_command() -> None:
    """Test crawl command triggers immediate crawl."""
    with (
        patch("research_engine.cli.TieredScheduler") as mock_sched_cls,
        patch("research_engine.cli.ResearchStore"),
    ):
        mock_sched = MagicMock()
        mock_sched_cls.return_value = mock_sched
        result = runner.invoke(app, ["crawl"])
    assert result.exit_code == 0


def test_sync_command() -> None:
    """Test sync command syncs to project-local DB."""
    with patch("research_engine.cli.ResearchStore") as mock_store_cls:
        mock_store = MagicMock()
        mock_store.mirror_to_project.return_value = 5
        mock_store_cls.return_value = mock_store
        result = runner.invoke(app, ["sync", "/tmp/test.db"])
    assert result.exit_code == 0
    assert "5" in result.output
