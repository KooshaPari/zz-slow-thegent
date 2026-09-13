"""Integration tests for research_engine end-to-end flow. @trace FR-RES-050"""

from datetime import UTC, datetime

import pytest

from research_engine.digest import DigestGenerator
from research_engine.schema import ResearchItem
from research_engine.session_hook import inject_session_context
from research_engine.store import ResearchStore


@pytest.fixture
def tmp_store(tmp_path):
    """Create a temporary ResearchStore for integration testing."""
    db = tmp_path / "research.db"
    return ResearchStore(db)


@pytest.fixture
def sample_item():
    """Create a sample ResearchItem for testing."""
    return ResearchItem(
        slug="abc123def456",
        source="hn",
        url="https://example.com/test",
        title="Integration Test Item",
        summary="A summary for integration testing.",
        score=42,
        tags=["python", "testing"],
        fetched_at=datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC),
        relevance=0.85,
    )


def test_store_upsert_and_retrieve(tmp_store, sample_item):
    """Full store cycle: upsert then get_recent returns the item."""
    tmp_store.upsert(sample_item)
    items = tmp_store.get_recent(hours=9999)
    assert len(items) == 1
    assert items[0].slug == sample_item.slug
    assert items[0].title == sample_item.title


def test_store_search(tmp_store, sample_item):
    """Full store cycle: upsert then search finds the item."""
    tmp_store.upsert(sample_item)
    results = tmp_store.search("Integration")
    assert any(i.slug == sample_item.slug for i in results)


def test_digest_with_real_store(tmp_store, sample_item):
    """DigestGenerator produces markdown from real store data."""
    tmp_store.upsert(sample_item)
    gen = DigestGenerator(tmp_store)
    digest = gen.generate(hours=9999, limit=10)
    assert "## Research Digest" in digest
    assert "Integration Test Item" in digest


def test_session_hook_with_real_store(tmp_store, sample_item):
    """inject_session_context produces markdown from real store data."""
    tmp_store.upsert(sample_item)
    context = inject_session_context(tmp_store, hours=9999)
    assert isinstance(context, str)
    assert "Integration Test Item" in context


def test_mirror_to_project(tmp_store, sample_item, tmp_path):
    """mirror_to_project copies high-relevance items to project DB."""
    tmp_store.upsert(sample_item)
    project_db = tmp_path / "project.db"
    n = tmp_store.mirror_to_project(project_db, min_relevance=0.5)
    assert n == 1
    project_store = ResearchStore(project_db)
    items = project_store.get_recent(hours=9999)
    assert len(items) == 1
    assert items[0].slug == sample_item.slug


def test_store_search_empty_store(tmp_store):
    """Search on empty store returns empty list."""
    results = tmp_store.search("nonexistent")
    assert results == []


def test_digest_empty_store(tmp_store):
    """DigestGenerator on empty store shows no items message."""
    gen = DigestGenerator(tmp_store)
    digest = gen.generate(hours=24, limit=10)
    assert "No new items" in digest


def test_session_hook_empty_store(tmp_store):
    """inject_session_context on empty store shows no items message."""
    context = inject_session_context(tmp_store)
    assert "No recent research items available" in context


def test_multiple_items_sorted_by_relevance(tmp_store):
    """Multiple items are sorted by relevance (highest first)."""
    low = ResearchItem(
        slug="low123",
        source="reddit",
        url="https://example.com/low",
        title="Low Relevance Item",
        summary="Low relevance item.",
        score=1,
        tags=[],
        fetched_at=datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC),
        relevance=0.2,
    )
    high = ResearchItem(
        slug="high456",
        source="github",
        url="https://example.com/high",
        title="High Relevance Item",
        summary="High relevance item.",
        score=100,
        tags=[],
        fetched_at=datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC),
        relevance=0.95,
    )
    tmp_store.upsert(low)
    tmp_store.upsert(high)
    items = tmp_store.get_recent(hours=9999)
    assert len(items) == 2
    assert items[0].slug == high.slug
    assert items[1].slug == low.slug


def test_upsert_idempotent(tmp_store, sample_item):
    """Upserting the same item twice replaces the first version."""
    tmp_store.upsert(sample_item)
    updated = ResearchItem(
        slug=sample_item.slug,
        source=sample_item.source,
        url=sample_item.url,
        title="Updated Title",
        summary=sample_item.summary,
        score=100,
        tags=sample_item.tags,
        fetched_at=datetime(2026, 1, 16, 12, 0, 0, tzinfo=UTC),
        relevance=0.95,
    )
    tmp_store.upsert(updated)
    items = tmp_store.get_recent(hours=9999)
    assert len(items) == 1
    assert items[0].score == 100
    assert items[0].relevance == 0.95
