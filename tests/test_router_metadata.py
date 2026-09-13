from datetime import UTC, datetime, timedelta

from thegent.utils.routing_impl.litellm_router import EnhancedRouter
from thegent.utils.routing_impl.model_metadata import (
    mark_metadata_stale,
    stamp_metadata_freshness,
    validate_metadata_freshness,
)


def test_router_metadata_model_preference():
    router = EnhancedRouter()

    # Normal routing
    route = router.route("Normal task", model="gpt-4")
    assert route.model == "gpt-4"

    # Routing from metadata
    metadata = {"model": "claude-3-opus"}
    route = router.route("Task from queue", queue_metadata=metadata)
    assert route.model == "claude-3-opus"

    # Routing from preferred_model
    metadata = {"preferred_model": "gemini-pro"}
    route = router.route("Task from queue", queue_metadata=metadata)
    assert route.model == "gemini-pro"

    # Explicit model overrides metadata
    metadata = {"model": "claude-3-opus"}
    route = router.route("Task from queue", model="gpt-4", queue_metadata=metadata)
    assert route.model == "gpt-4"


def test_metadata_freshness_stamp_and_validate():
    now = datetime.now(UTC)
    stamped = stamp_metadata_freshness({"model": "gpt-5-mini"}, fetched_at=now, ttl_seconds=60)
    validated = validate_metadata_freshness(stamped, now=now + timedelta(seconds=30))
    assert validated["freshness_status"] == "fresh"


def test_metadata_freshness_marks_stale_when_expired():
    now = datetime.now(UTC)
    stamped = stamp_metadata_freshness({"model": "gpt-5-mini"}, fetched_at=now, ttl_seconds=1)
    validated = validate_metadata_freshness(stamped, now=now + timedelta(seconds=2))
    assert validated["freshness_status"] == "stale"
    explicit = mark_metadata_stale(stamped)
    assert explicit["freshness_status"] == "stale"
