# tests/research_engine/test_digest.py
# @trace FR-RE-011
"""DigestGenerator — markdown digest rendering tests."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from research_engine.schema import ResearchItem
from research_engine.store import ResearchStore


@pytest.fixture
def populated_store(tmp_path: Path) -> ResearchStore:
    """Create a store with 5 sample research items."""
    store = ResearchStore(tmp_path / "research.db")
    for i in range(5):
        store.upsert(
            ResearchItem.from_url(
                url=f"https://example.com/{i}",
                source="hn",  # type: ignore
                title=f"Item {i}: Python MCP",
                summary=f"Summary of item {i}",
                score=100 - i * 10,
                tags=["python", "mcp"],
                fetched_at=datetime.now(UTC),
                relevance=0.9 - i * 0.1,
            )
        )
    return store


def test_digest_generates_markdown(populated_store: ResearchStore) -> None:
    """Digest produces markdown with items, titles, and URLs."""
    from research_engine.digest import DigestGenerator

    gen = DigestGenerator(populated_store)
    md = gen.generate(hours=24, limit=10)
    assert "## Research Digest" in md
    assert "Item 0" in md
    assert "https://example.com/0" in md


def test_digest_respects_limit(populated_store: ResearchStore) -> None:
    """Digest respects the limit parameter."""
    from research_engine.digest import DigestGenerator

    gen = DigestGenerator(populated_store)
    md = gen.generate(hours=24, limit=2)
    assert md.count("https://example.com/") == 2


def test_digest_empty_store(tmp_path: Path) -> None:
    """Digest handles empty store gracefully."""
    from research_engine.digest import DigestGenerator

    store = ResearchStore(tmp_path / "empty.db")
    gen = DigestGenerator(store)
    md = gen.generate(hours=24, limit=10)
    assert "## Research Digest" in md
    assert "No new items" in md


@pytest.mark.requirement("WL-237")
def test_hourly_change_digest_groups_by_connector_action_outcome() -> None:
    from research_engine.digest import build_hourly_change_digest

    payload = build_hourly_change_digest(
        [
            {
                "timestamp": "2026-02-22T10:15:00Z",
                "connector": "github",
                "action": "write",
                "outcome": "success",
            },
            {
                "timestamp": "2026-02-22T10:25:00Z",
                "connector": "github",
                "action": "write",
                "outcome": "success",
            },
            {
                "timestamp": "2026-02-22T10:45:00Z",
                "connector": "linear",
                "action": "write",
                "outcome": "failure",
            },
        ]
    )
    hour_bucket = payload["hours"]["2026-02-22T10:00:00Z"]
    assert hour_bucket["github"]["write:success"] == 2
    assert hour_bucket["linear"]["write:failure"] == 1


@pytest.mark.requirement("WL-237")
def test_hourly_change_digest_accumulates_weighted_counts() -> None:
    from research_engine.digest import build_hourly_change_digest

    payload = build_hourly_change_digest(
        [
            {
                "timestamp": "2026-02-22T10:10:00Z",
                "connector": "github",
                "action": "write",
                "outcome": "failure",
                "count": 2,
            },
            {
                "timestamp": "2026-02-22T10:35:00Z",
                "connector": "github",
                "action": "write",
                "outcome": "failure",
                "count": 3,
            },
        ]
    )
    hour_bucket = payload["hours"]["2026-02-22T10:00:00Z"]
    assert hour_bucket["github"]["write:failure"] == 5


def test_hourly_change_digest_requires_timestamp() -> None:
    from research_engine.digest import build_hourly_change_digest

    with pytest.raises(ValueError, match="timestamp"):
        build_hourly_change_digest(
            [{"connector": "github", "action": "write", "outcome": "success"}]
        )
