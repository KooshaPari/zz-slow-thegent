"""Tests for research_engine.session_hook — @trace FR-RES-030"""

from datetime import UTC, datetime
from unittest.mock import MagicMock

from research_engine.schema import ResearchItem
from research_engine.session_hook import inject_session_context


def test_inject_session_context_returns_string():
    store = MagicMock()
    store.get_recent.return_value = []
    result = inject_session_context(store)
    assert isinstance(result, str)


def test_inject_includes_items():
    store = MagicMock()
    item = ResearchItem(
        slug="abc123def456",
        source="hn",
        url="https://example.com",
        title="Test Item",
        summary="A test summary",
        score=100,
        tags=["python"],
        fetched_at=datetime(2026, 1, 1, tzinfo=UTC),
        relevance=0.9,
    )
    store.get_recent.return_value = [item]
    result = inject_session_context(store)
    assert "Test Item" in result


def test_inject_empty_store():
    store = MagicMock()
    store.get_recent.return_value = []
    result = inject_session_context(store)
    assert isinstance(result, str)
    assert len(result) > 0


def test_inject_with_hours_and_limit():
    store = MagicMock()
    store.get_recent.return_value = []
    inject_session_context(store, hours=12, limit=5)
    store.get_recent.assert_called_once_with(hours=12, limit=5)


def test_inject_formats_tags():
    store = MagicMock()
    item = ResearchItem(
        slug="test123",
        source="reddit",
        url="https://reddit.com/r/python",
        title="Python Tips",
        summary="Learn Python",
        score=50,
        tags=["python", "tips"],
        fetched_at=datetime(2026, 1, 1, tzinfo=UTC),
        relevance=0.8,
    )
    store.get_recent.return_value = [item]
    result = inject_session_context(store)
    assert "python" in result
    assert "tips" in result
