"""ResearchStore SQLite persistence tests.

@trace FR-RE-003
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from research_engine.schema import ResearchItem


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "research.db"


@pytest.fixture
def item() -> ResearchItem:
    return ResearchItem.from_url(
        url="https://news.ycombinator.com/item?id=99",
        source="hn",
        title="Test HN Item",
        summary="A cool project",
        score=500,
        tags=["python", "ai"],
        fetched_at=datetime.now(UTC),
        relevance=0.9,
    )


def test_upsert_and_get_recent(db_path: Path, item: ResearchItem) -> None:
    """Test upsert and retrieval of recent items."""
    from research_engine.store import ResearchStore

    store = ResearchStore(db_path)
    store.upsert(item)
    results = store.get_recent(hours=1, limit=10)
    assert len(results) == 1
    assert results[0].slug == item.slug


def test_search_by_title(db_path: Path, item: ResearchItem) -> None:
    """Test full-text search by title."""
    from research_engine.store import ResearchStore

    store = ResearchStore(db_path)
    store.upsert(item)
    results = store.search("cool project")
    assert len(results) == 1
    assert results[0].slug == item.slug


def test_upsert_dedup(db_path: Path, item: ResearchItem) -> None:
    """Test that duplicate slugs are deduplicated."""
    from research_engine.store import ResearchStore

    store = ResearchStore(db_path)
    store.upsert(item)
    store.upsert(item)
    assert len(store.get_recent(hours=1, limit=100)) == 1


def test_mirror_to_project(db_path: Path, tmp_path: Path, item: ResearchItem) -> None:
    """Test mirroring items to a project database."""
    from research_engine.store import ResearchStore

    global_store = ResearchStore(db_path)
    global_store.upsert(item)
    project_db = tmp_path / "project.db"
    global_store.mirror_to_project(project_db, min_relevance=0.5)
    project_store = ResearchStore(project_db)
    results = project_store.get_recent(hours=1, limit=10)
    assert len(results) == 1


def test_mirror_filters_low_relevance(db_path: Path, tmp_path: Path) -> None:
    """Test that mirror filters out low-relevance items."""
    from research_engine.store import ResearchStore

    store = ResearchStore(db_path)
    low = ResearchItem.from_url(
        url="https://example.com/low",
        source="hn",
        title="Low Relevance",
        summary="irrelevant",
        score=1,
        tags=[],
        fetched_at=datetime.now(UTC),
        relevance=0.1,
    )
    store.upsert(low)
    project_db = tmp_path / "project.db"
    store.mirror_to_project(project_db, min_relevance=0.3)
    project_store = ResearchStore(project_db)
    assert len(project_store.get_recent(hours=1, limit=100)) == 0
