"""Tests for arXiv crawler. @trace FR-RE-007"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch


def _make_result(title: str, url: str, abstract: str = "") -> MagicMock:
    """Create mock arXiv result."""
    r = MagicMock()
    r.title = title
    r.entry_id = url
    r.summary = abstract
    r.updated = datetime.now(UTC)
    return r


def test_arxiv_fetch() -> None:
    """Fetch returns list of ResearchItem from arXiv."""
    from research_engine.crawlers.arxiv_crawler import ArxivCrawler

    result = _make_result("LLM Agent Governance", "https://arxiv.org/abs/2501.00001", "abstract text")

    with patch("arxiv.Search") as mock_search:
        mock_search.return_value.results.return_value = iter([result])
        crawler = ArxivCrawler()
        items = crawler.fetch(["llm", "agent"])

    assert len(items) == 1
    assert items[0].source == "arxiv"
    assert items[0].url == "https://arxiv.org/abs/2501.00001"


def test_arxiv_fetch_empty() -> None:
    """Fetch handles empty results."""
    from research_engine.crawlers.arxiv_crawler import ArxivCrawler

    with patch("arxiv.Search") as mock_search:
        mock_search.return_value.results.return_value = iter([])
        crawler = ArxivCrawler()
        items = crawler.fetch(["nonexistent"])

    assert len(items) == 0


def test_arxiv_fetch_multiple() -> None:
    """Fetch returns multiple items."""
    from research_engine.crawlers.arxiv_crawler import ArxivCrawler

    results = [
        _make_result("Paper 1", "https://arxiv.org/abs/2501.00001", "abstract 1"),
        _make_result("Paper 2", "https://arxiv.org/abs/2501.00002", "abstract 2"),
    ]

    with patch("arxiv.Search") as mock_search:
        mock_search.return_value.results.return_value = iter(results)
        crawler = ArxivCrawler()
        items = crawler.fetch(["ai"])

    assert len(items) == 2
    assert items[0].url == "https://arxiv.org/abs/2501.00001"
    assert items[1].url == "https://arxiv.org/abs/2501.00002"


def test_arxiv_fetch_tags() -> None:
    """Fetch populates tags from topic matches."""
    from research_engine.crawlers.arxiv_crawler import ArxivCrawler

    result = _make_result(
        "Machine learning for agents",
        "https://arxiv.org/abs/2501.00001",
        "This paper discusses machine learning approaches for agents",
    )

    with patch("arxiv.Search") as mock_search:
        mock_search.return_value.results.return_value = iter([result])
        crawler = ArxivCrawler()
        items = crawler.fetch(["machine", "learning", "agents"])

    assert "machine" in items[0].tags or "learning" in items[0].tags or "agents" in items[0].tags


def test_arxiv_tier() -> None:
    """arXiv crawler has daily tier."""
    from research_engine.crawlers.arxiv_crawler import ArxivCrawler

    assert ArxivCrawler.tier == "daily"


def test_arxiv_source() -> None:
    """arXiv crawler has correct source name."""
    from research_engine.crawlers.arxiv_crawler import ArxivCrawler

    assert ArxivCrawler.source == "arxiv"


def test_arxiv_relevance() -> None:
    """Fetch calculates relevance score."""
    from research_engine.crawlers.arxiv_crawler import ArxivCrawler

    result = _make_result("Agent and learning", "https://arxiv.org/abs/2501.00001", "About agents and learning")

    with patch("arxiv.Search") as mock_search:
        mock_search.return_value.results.return_value = iter([result])
        crawler = ArxivCrawler()
        items = crawler.fetch(["agent", "learning"])

    assert items[0].relevance > 0.0
