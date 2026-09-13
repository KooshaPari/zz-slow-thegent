"""Tests for Reddit crawler. @trace FR-RE-006"""

from __future__ import annotations

from unittest.mock import MagicMock, patch


def _make_submission(title: str, url: str, score: int, selftext: str = "") -> MagicMock:
    """Create mock Reddit submission."""
    s = MagicMock()
    s.title = title
    s.url = url
    s.score = score
    s.selftext = selftext
    s.id = "abc123"
    return s


def test_reddit_crawler_fetch() -> None:
    """Fetch returns list of ResearchItem from Reddit."""
    from research_engine.crawlers.reddit import RedditCrawler

    sub = _make_submission("Python AI agents discussion", "https://reddit.com/r/python/abc", 300)

    mock_reddit = MagicMock()
    mock_reddit.subreddit.return_value.search.return_value = [sub]

    with patch("praw.Reddit", return_value=mock_reddit):
        crawler = RedditCrawler(client_id="x", client_secret="y", user_agent="test")
        items = crawler.fetch(["python", "ai"])

    assert len(items) >= 1
    assert items[0].source == "reddit"
    assert items[0].score == 300


def test_reddit_crawler_multiple_subreddits() -> None:
    """Fetch searches across multiple subreddits."""
    from research_engine.crawlers.reddit import RedditCrawler

    sub1 = _make_submission("Python discussion", "https://reddit.com/r/python/1", 100)
    sub2 = _make_submission("ML article", "https://reddit.com/r/MachineLearning/2", 200)

    mock_reddit = MagicMock()
    mock_reddit.subreddit.return_value.search.return_value = [sub1, sub2]

    with patch("praw.Reddit", return_value=mock_reddit):
        crawler = RedditCrawler(client_id="x", client_secret="y", user_agent="test")
        items = crawler.fetch(["python"])

    assert len(items) >= 2


def test_reddit_crawler_empty() -> None:
    """Fetch handles empty search results."""
    from research_engine.crawlers.reddit import RedditCrawler

    mock_reddit = MagicMock()
    mock_reddit.subreddit.return_value.search.return_value = []

    with patch("praw.Reddit", return_value=mock_reddit):
        crawler = RedditCrawler(client_id="x", client_secret="y", user_agent="test")
        items = crawler.fetch(["nonexistent"])

    assert len(items) == 0


def test_reddit_crawler_with_selftext() -> None:
    """Fetch includes selftext in summary."""
    from research_engine.crawlers.reddit import RedditCrawler

    sub = _make_submission(
        "Python agents",
        "https://reddit.com/r/python/123",
        50,
        "Detailed self post content",
    )

    mock_reddit = MagicMock()
    mock_reddit.subreddit.return_value.search.return_value = [sub]

    with patch("praw.Reddit", return_value=mock_reddit):
        crawler = RedditCrawler(client_id="x", client_secret="y", user_agent="test")
        items = crawler.fetch(["python"])

    assert "Detailed self post content" in items[0].summary


def test_reddit_crawler_tier() -> None:
    """Reddit crawler has hourly tier."""
    from research_engine.crawlers.reddit import RedditCrawler

    assert RedditCrawler.tier == "hourly"


def test_reddit_crawler_source() -> None:
    """Reddit crawler has correct source name."""
    from research_engine.crawlers.reddit import RedditCrawler

    assert RedditCrawler.source == "reddit"


def test_reddit_crawler_tags() -> None:
    """Fetch populates tags from topic matches."""
    from research_engine.crawlers.reddit import RedditCrawler

    sub = _make_submission("Python and machine learning", "https://reddit.com/r/1", 100, "")

    mock_reddit = MagicMock()
    mock_reddit.subreddit.return_value.search.return_value = [sub]

    with patch("praw.Reddit", return_value=mock_reddit):
        crawler = RedditCrawler(client_id="x", client_secret="y", user_agent="test")
        items = crawler.fetch(["python", "ml"])

    assert "python" in items[0].tags
