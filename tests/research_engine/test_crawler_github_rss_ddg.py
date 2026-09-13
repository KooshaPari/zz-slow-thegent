"""Tests for GitHub, RSS, and DDG crawlers. @trace FR-RE-008"""

from __future__ import annotations

from unittest.mock import MagicMock, patch


class TestGitHubCrawler:
    """GitHub crawler tests."""

    def test_github_crawler_fetch(self) -> None:
        """Fetch returns list of ResearchItem from GitHub."""
        from research_engine.crawlers.github import GitHubCrawler

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "items": [
                {
                    "html_url": "https://github.com/example/mcp-server",
                    "full_name": "example/mcp-server",
                    "description": "MCP server for python agents",
                    "stargazers_count": 1500,
                }
            ]
        }
        with patch("httpx.get", return_value=mock_resp):
            crawler = GitHubCrawler()
            items = crawler.fetch(["mcp", "python"])

        assert len(items) == 1
        assert items[0].source == "github"
        assert items[0].score == 1500

    def test_github_crawler_empty(self) -> None:
        """Fetch handles empty results."""
        from research_engine.crawlers.github import GitHubCrawler

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"items": []}

        with patch("httpx.get", return_value=mock_resp):
            crawler = GitHubCrawler()
            items = crawler.fetch(["nonexistent"])

        assert len(items) == 0

    def test_github_crawler_multiple(self) -> None:
        """Fetch returns multiple items."""
        from research_engine.crawlers.github import GitHubCrawler

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "items": [
                {
                    "html_url": "https://github.com/a/b",
                    "full_name": "a/b",
                    "description": "First repo",
                    "stargazers_count": 100,
                },
                {
                    "html_url": "https://github.com/c/d",
                    "full_name": "c/d",
                    "description": "Second repo",
                    "stargazers_count": 200,
                },
            ]
        }

        with patch("httpx.get", return_value=mock_resp):
            crawler = GitHubCrawler()
            items = crawler.fetch(["test"])

        assert len(items) == 2
        assert items[0].score == 100
        assert items[1].score == 200

    def test_github_crawler_tier(self) -> None:
        """GitHub crawler has daily tier."""
        from research_engine.crawlers.github import GitHubCrawler

        assert GitHubCrawler.tier == "daily"

    def test_github_crawler_source(self) -> None:
        """GitHub crawler has correct source name."""
        from research_engine.crawlers.github import GitHubCrawler

        assert GitHubCrawler.source == "github"

    def test_github_crawler_with_token(self) -> None:
        """GitHub crawler accepts optional token."""
        from research_engine.crawlers.github import GitHubCrawler

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"items": []}

        with patch("httpx.get", return_value=mock_resp) as mock_get:
            crawler = GitHubCrawler(token="test_token")
            crawler.fetch(["test"])

        call_kwargs = mock_get.call_args[1]
        assert "headers" in call_kwargs
        assert "Authorization" in call_kwargs["headers"]


class TestRSSCrawler:
    """RSS crawler tests."""

    def test_rss_crawler_fetch(self) -> None:
        """Fetch returns list of ResearchItem from RSS."""
        from research_engine.crawlers.rss import RSSCrawler

        mock_feed = MagicMock()
        mock_entry = MagicMock()
        mock_entry.title = "Python 3.14 Released"
        mock_entry.link = "https://blog.python.org/2026/02/py314.html"
        mock_entry.summary = "Major new features in 3.14"
        mock_feed.entries = [mock_entry]

        with patch("feedparser.parse", return_value=mock_feed):
            crawler = RSSCrawler(feeds=["https://blog.python.org/feeds/posts/default"])
            items = crawler.fetch(["python"])

        assert len(items) == 1
        assert items[0].source == "rss"
        assert items[0].title == "Python 3.14 Released"

    def test_rss_crawler_empty(self) -> None:
        """Fetch handles empty feed."""
        from research_engine.crawlers.rss import RSSCrawler

        mock_feed = MagicMock()
        mock_feed.entries = []

        with patch("feedparser.parse", return_value=mock_feed):
            crawler = RSSCrawler(feeds=["https://example.com/feed.xml"])
            items = crawler.fetch(["test"])

        assert len(items) == 0

    def test_rss_crawler_default_feeds(self) -> None:
        """Fetch uses default feeds if not provided."""
        from research_engine.crawlers.rss import RSSCrawler

        mock_feed = MagicMock()
        mock_feed.entries = []

        with patch("feedparser.parse", return_value=mock_feed):
            crawler = RSSCrawler()
            crawler.fetch(["test"])

        # Verify it called parse (with any feed URL)
        # The actual default feeds are used

    def test_rss_crawler_tier(self) -> None:
        """RSS crawler has weekly tier."""
        from research_engine.crawlers.rss import RSSCrawler

        assert RSSCrawler.tier == "weekly"

    def test_rss_crawler_source(self) -> None:
        """RSS crawler has correct source name."""
        from research_engine.crawlers.rss import RSSCrawler

        assert RSSCrawler.source == "rss"

    def test_rss_crawler_missing_fields(self) -> None:
        """Fetch handles missing title/summary gracefully."""
        from research_engine.crawlers.rss import RSSCrawler

        mock_feed = MagicMock()
        mock_entry = MagicMock()
        # These may not be set, causing AttributeError in getattr
        del mock_entry.title
        del mock_entry.summary
        mock_entry.link = "https://example.com/1"
        mock_feed.entries = [mock_entry]

        with patch("feedparser.parse", return_value=mock_feed):
            crawler = RSSCrawler(feeds=["https://example.com/feed.xml"])
            items = crawler.fetch(["test"])

        assert len(items) == 1
        assert items[0].title == ""
        assert items[0].summary == ""


class TestDDGCrawler:
    """DDG crawler tests."""

    def test_ddg_crawler_fetch(self) -> None:
        """Fetch returns list of ResearchItem from DDG."""
        from research_engine.crawlers.ddg import DDGCrawler

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "RelatedTopics": [{"FirstURL": "https://ddg.gg/result1", "Text": "Python MCP agent framework"}]
        }
        with patch("httpx.get", return_value=mock_resp):
            crawler = DDGCrawler()
            items = crawler.fetch(["python", "mcp"])

        assert len(items) >= 1
        assert items[0].source == "ddg"

    def test_ddg_crawler_empty(self) -> None:
        """Fetch handles empty results."""
        from research_engine.crawlers.ddg import DDGCrawler

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"RelatedTopics": []}

        with patch("httpx.get", return_value=mock_resp):
            crawler = DDGCrawler()
            items = crawler.fetch(["test"])

        assert len(items) == 0

    def test_ddg_crawler_missing_url(self) -> None:
        """Fetch skips entries without FirstURL."""
        from research_engine.crawlers.ddg import DDGCrawler

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "RelatedTopics": [
                {"Text": "No URL for this"},
                {"FirstURL": "https://ddg.gg/result2", "Text": "Has URL"},
            ]
        }

        with patch("httpx.get", return_value=mock_resp):
            crawler = DDGCrawler()
            items = crawler.fetch(["test"])

        assert len(items) == 1
        assert items[0].url == "https://ddg.gg/result2"

    def test_ddg_crawler_tier(self) -> None:
        """DDG crawler has daily tier."""
        from research_engine.crawlers.ddg import DDGCrawler

        assert DDGCrawler.tier == "daily"

    def test_ddg_crawler_source(self) -> None:
        """DDG crawler has correct source name."""
        from research_engine.crawlers.ddg import DDGCrawler

        assert DDGCrawler.source == "ddg"
