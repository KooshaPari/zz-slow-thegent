"""Test BaseCrawler ABC and CrawlerRegistry."""
# @trace FR-RE-004

from datetime import UTC, datetime

from research_engine.schema import ResearchItem


def test_registry_register_and_get() -> None:
    """Test registering a crawler and retrieving it by tier."""
    from research_engine.crawlers.base import BaseCrawler
    from research_engine.crawlers.registry import CrawlerRegistry

    class FakeCrawler(BaseCrawler):
        source = "other"
        tier = "hourly"

        def fetch(self, topics: list[str]) -> list[ResearchItem]:
            return [
                ResearchItem.from_url(
                    url="https://fake.com/1",
                    source="other",
                    title="Fake Item",
                    summary="fake",
                    score=1,
                    tags=topics[:1],
                    fetched_at=datetime.now(UTC),
                    relevance=0.5,
                )
            ]

    registry = CrawlerRegistry()
    registry.register(FakeCrawler())
    crawlers = registry.get_by_tier("hourly")
    assert len(crawlers) == 1
    items = crawlers[0].fetch(["python"])
    assert items[0].source == "other"


def test_registry_get_all() -> None:
    """Test retrieving all registered crawlers."""
    from research_engine.crawlers.base import BaseCrawler
    from research_engine.crawlers.registry import CrawlerRegistry

    class A(BaseCrawler):
        source = "hn"
        tier = "hourly"

        def fetch(self, _topics: list[str]) -> list[ResearchItem]:
            return []

    class B(BaseCrawler):
        source = "arxiv"
        tier = "daily"

        def fetch(self, _topics: list[str]) -> list[ResearchItem]:
            return []

    r = CrawlerRegistry()
    r.register(A())
    r.register(B())
    assert len(r.get_all()) == 2
