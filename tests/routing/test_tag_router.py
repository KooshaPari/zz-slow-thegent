"""Tests for GW-58: Tag-based routing.

# @trace FR-AROUTE-058
"""

from __future__ import annotations

import pytest

from thegent.utils.routing_impl.tag_router import (
    TagRoute,
    TagRouter,
    extract_request_tags,
)


@pytest.mark.requirement("FR-AROUTE-058")
class TestTagRouter:
    def test_tag_router_matches_all_tags(self) -> None:
        router = TagRouter()
        router.register(TagRoute(tags=["free_tier"], target="gpt-4o-mini", priority=1))
        result = router.resolve(["free_tier", "streaming"])
        assert result == "gpt-4o-mini"

    def test_tag_router_no_match_missing_tag(self) -> None:
        router = TagRouter()
        router.register(TagRoute(tags=["paid_tier"], target="gpt-4o", priority=1))
        result = router.resolve(["free_tier"])
        assert result is None

    def test_tag_router_priority_wins(self) -> None:
        router = TagRouter()
        router.register(
            TagRoute(tags=["premium"], target="low-priority-model", priority=1)
        )
        router.register(
            TagRoute(tags=["premium"], target="high-priority-model", priority=10)
        )
        result = router.resolve(["premium"])
        assert result == "high-priority-model"

    def test_tag_router_all_tags_required(self) -> None:
        router = TagRouter()
        router.register(TagRoute(tags=["paid_tier", "streaming"], target="gpt-4o"))
        # Only one of the two required tags present
        result = router.resolve(["paid_tier"])
        assert result is None

    def test_tag_router_all_tags_present_matches(self) -> None:
        router = TagRouter()
        router.register(TagRoute(tags=["paid_tier", "streaming"], target="gpt-4o"))
        result = router.resolve(["paid_tier", "streaming", "extra"])
        assert result == "gpt-4o"

    def test_tag_router_empty_request_tags(self) -> None:
        router = TagRouter()
        router.register(TagRoute(tags=["paid_tier"], target="gpt-4o"))
        result = router.resolve([])
        assert result is None

    def test_tag_router_empty_route_tags_matches_everything(self) -> None:
        router = TagRouter()
        router.register(TagRoute(tags=[], target="default-model"))
        result = router.resolve(["anything"])
        assert result == "default-model"

    def test_tag_router_no_routes(self) -> None:
        router = TagRouter()
        result = router.resolve(["free_tier"])
        assert result is None

    def test_tag_router_multiple_routes_first_registered_wins_on_tie(self) -> None:
        router = TagRouter()
        router.register(TagRoute(tags=["user"], target="model-a", priority=5))
        router.register(TagRoute(tags=["user"], target="model-b", priority=5))
        result = router.resolve(["user"])
        # max() is stable on equal priority — first registered (model-a) wins
        assert result == "model-a"


@pytest.mark.requirement("FR-AROUTE-058")
class TestExtractRequestTags:
    def test_extract_request_tags_present(self) -> None:
        body = {"tg_tags": ["free_tier", "streaming"], "model": "gpt-4o"}
        tags = extract_request_tags(body)
        assert tags == ["free_tier", "streaming"]

    def test_extract_request_tags_missing(self) -> None:
        body = {"model": "gpt-4o"}
        tags = extract_request_tags(body)
        assert tags == []

    def test_extract_request_tags_empty_list(self) -> None:
        body = {"tg_tags": []}
        tags = extract_request_tags(body)
        assert tags == []
