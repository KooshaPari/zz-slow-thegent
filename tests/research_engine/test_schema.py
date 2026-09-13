# tests/research_engine/test_schema.py
# @trace FR-RE-002
from datetime import UTC, datetime


def test_research_item_roundtrip() -> None:
    from research_engine.schema import ResearchItem

    item = ResearchItem(
        slug="abc123def456",
        source="hn",
        url="https://news.ycombinator.com/item?id=1",
        title="Test Item",
        summary="A summary",
        score=100,
        tags=["python", "mcp"],
        fetched_at=datetime.now(UTC),
        relevance=0.85,
    )
    assert item.slug == "abc123def456"
    assert item.source == "hn"
    assert item.relevance == 0.85


def test_research_item_slug_from_url() -> None:
    from research_engine.schema import ResearchItem

    item = ResearchItem.from_url(
        url="https://news.ycombinator.com/item?id=42",
        source="hn",
        title="Test",
        summary="",
        score=0,
        tags=[],
        fetched_at=datetime.now(UTC),
        relevance=0.0,
    )
    assert len(item.slug) == 12
    assert all(c in "0123456789abcdef" for c in item.slug)
