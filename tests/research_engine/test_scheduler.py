"""TieredScheduler tests — hourly/daily/weekly job scheduling with research_engine.

@trace FR-RE-010
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from research_engine.schema import ResearchItem


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    """Create temporary database path."""
    return tmp_path / "test.db"


def test_scheduler_runs_hourly_job(db_path: Path) -> None:
    """Test that TieredScheduler executes hourly tier crawlers."""
    from research_engine.crawlers.base import BaseCrawler
    from research_engine.scheduler import TieredScheduler

    call_log: list[str] = []

    class SpyCrawler(BaseCrawler):
        """Test crawler that logs fetch calls."""

        source = "hn"
        tier = "hourly"

        def fetch(self, topics: list[str]) -> list[ResearchItem]:
            """Log fetch call and return empty list."""
            call_log.append("hn-fetch")
            return []

    scheduler = TieredScheduler(db_path=db_path, topics=["python"])
    scheduler.registry.register(SpyCrawler())
    scheduler._run_tier("hourly")
    assert "hn-fetch" in call_log


def test_scheduler_stores_items(db_path: Path) -> None:
    """Test that TieredScheduler persists fetched items to store."""
    from research_engine.crawlers.base import BaseCrawler
    from research_engine.scheduler import TieredScheduler

    from research_engine.store import ResearchStore

    class FixedCrawler(BaseCrawler):
        """Test crawler that returns a fixed item."""

        source = "hn"
        tier = "hourly"

        def fetch(self, topics: list[str]) -> list[ResearchItem]:
            """Return a test research item."""
            return [
                ResearchItem.from_url(
                    url="https://example.com/1",
                    source="hn",
                    title="Python AI",
                    summary="test",
                    score=100,
                    tags=["python"],
                    fetched_at=datetime.now(UTC),
                    relevance=0.9,
                )
            ]

    scheduler = TieredScheduler(db_path=db_path, topics=["python"])
    scheduler.registry.register(FixedCrawler())
    scheduler._run_tier("hourly")

    store = ResearchStore(db_path)
    results = store.get_recent(hours=1)
    assert len(results) == 1


def test_scheduler_start_stop(db_path: Path) -> None:
    """Test TieredScheduler lifecycle (start/stop)."""
    from research_engine.scheduler import TieredScheduler

    scheduler = TieredScheduler(db_path=db_path, topics=["python"])
    scheduler.start()
    assert scheduler._scheduler.running
    scheduler.stop()
    assert not scheduler._scheduler.running


def test_scheduler_multiple_tiers(db_path: Path) -> None:
    """Test TieredScheduler runs correct tier for registered crawlers."""
    from research_engine.crawlers.base import BaseCrawler
    from research_engine.scheduler import TieredScheduler

    calls: dict[str, int] = {"hourly": 0, "daily": 0, "weekly": 0}

    class HourlyCrawler(BaseCrawler):
        """Crawler registered for hourly tier."""

        source = "test_hourly"
        tier = "hourly"

        def fetch(self, topics: list[str]) -> list[ResearchItem]:
            """Increment hourly counter."""
            calls["hourly"] += 1
            return []

    class DailyCrawler(BaseCrawler):
        """Crawler registered for daily tier."""

        source = "test_daily"
        tier = "daily"

        def fetch(self, topics: list[str]) -> list[ResearchItem]:
            """Increment daily counter."""
            calls["daily"] += 1
            return []

    scheduler = TieredScheduler(db_path=db_path, topics=["python"])
    scheduler.registry.register(HourlyCrawler())
    scheduler.registry.register(DailyCrawler())

    scheduler._run_tier("hourly")
    assert calls["hourly"] == 1
    assert calls["daily"] == 0

    scheduler._run_tier("daily")
    assert calls["hourly"] == 1
    assert calls["daily"] == 1


def test_scheduler_multiple_crawlers_same_tier(db_path: Path) -> None:
    """Test TieredScheduler runs all crawlers in a tier."""
    from research_engine.crawlers.base import BaseCrawler
    from research_engine.scheduler import TieredScheduler

    from research_engine.store import ResearchStore

    class CrawlerA(BaseCrawler):
        """First test crawler."""

        source = "other"
        tier = "hourly"

        def fetch(self, topics: list[str]) -> list[ResearchItem]:
            """Return one item."""
            return [
                ResearchItem.from_url(
                    url="https://example.com/a",
                    source="other",
                    title="Item A",
                    summary="From crawler A",
                    score=10,
                    tags=["test"],
                    fetched_at=datetime.now(UTC),
                    relevance=0.5,
                )
            ]

    class CrawlerB(BaseCrawler):
        """Second test crawler."""

        source = "hn"
        tier = "hourly"

        def fetch(self, topics: list[str]) -> list[ResearchItem]:
            """Return one item."""
            return [
                ResearchItem.from_url(
                    url="https://example.com/b",
                    source="hn",
                    title="Item B",
                    summary="From crawler B",
                    score=20,
                    tags=["test"],
                    fetched_at=datetime.now(UTC),
                    relevance=0.7,
                )
            ]

    scheduler = TieredScheduler(db_path=db_path, topics=["python"])
    scheduler.registry.register(CrawlerA())
    scheduler.registry.register(CrawlerB())
    scheduler._run_tier("hourly")

    store = ResearchStore(db_path)
    results = store.get_recent(hours=1, limit=10)
    assert len(results) == 2
    assert {r.source for r in results} == {"other", "hn"}
