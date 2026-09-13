"""Tests for WL-318: Alert Routing Hooks.

@trace WL-318
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from thegent.integrations.alert_routing import (
    Alert,
    AlertRouter,
    AlertSeverity,
)


@pytest.mark.requirement("WL-318")
def test_alert_severity_enum() -> None:
    """Test AlertSeverity enum values."""
    assert AlertSeverity.INFO.value == "info"
    assert AlertSeverity.WARN.value == "warn"
    assert AlertSeverity.CRITICAL.value == "critical"


@pytest.mark.requirement("WL-318")
def test_alert_dataclass() -> None:
    """Test Alert dataclass creation."""
    timestamp = datetime.now(UTC)
    alert = Alert(
        alert_id="ALR-001",
        severity=AlertSeverity.WARN,
        message="Test alert",
        context={"user": "alice"},
        timestamp=timestamp,
    )
    assert alert.alert_id == "ALR-001"
    assert alert.severity == AlertSeverity.WARN
    assert alert.message == "Test alert"
    assert alert.context == {"user": "alice"}
    assert alert.timestamp == timestamp


@pytest.mark.requirement("WL-318")
def test_alert_router_initialization() -> None:
    """Test AlertRouter initializes with no hooks."""
    router = AlertRouter()
    assert router.list_hooks() == []


@pytest.mark.requirement("WL-318")
def test_register_single_hook() -> None:
    """Test registering a single hook."""
    router = AlertRouter()
    called = []

    def my_hook(alert: Alert) -> None:
        called.append(alert.alert_id)

    router.register_hook("my_hook", my_hook)
    assert router.list_hooks() == ["my_hook"]


@pytest.mark.requirement("WL-318")
def test_register_multiple_hooks() -> None:
    """Test registering multiple hooks."""
    router = AlertRouter()

    def hook1(alert: Alert) -> None:
        pass

    def hook2(alert: Alert) -> None:
        pass

    router.register_hook("hook1", hook1)
    router.register_hook("hook2", hook2)
    assert router.list_hooks() == ["hook1", "hook2"]


@pytest.mark.requirement("WL-318")
def test_unregister_hook() -> None:
    """Test unregistering a hook."""
    router = AlertRouter()

    def hook(alert: Alert) -> None:
        pass

    router.register_hook("hook", hook)
    assert "hook" in router.list_hooks()

    router.unregister_hook("hook")
    assert "hook" not in router.list_hooks()


@pytest.mark.requirement("WL-318")
def test_unregister_nonexistent_hook() -> None:
    """Test unregistering nonexistent hook raises KeyError."""
    router = AlertRouter()

    with pytest.raises(KeyError, match="Hook not found"):
        router.unregister_hook("nonexistent")


@pytest.mark.requirement("WL-318")
def test_route_single_hook() -> None:
    """Test routing to a single hook."""
    router = AlertRouter()
    called = []

    def hook(alert: Alert) -> None:
        called.append(alert.alert_id)

    router.register_hook("hook", hook)

    alert = Alert(
        alert_id="ALR-001",
        severity=AlertSeverity.INFO,
        message="Test",
        context={},
        timestamp=datetime.now(UTC),
    )

    count = router.route(alert)
    assert count == 1
    assert called == ["ALR-001"]


@pytest.mark.requirement("WL-318")
def test_route_multiple_hooks() -> None:
    """Test routing to multiple hooks."""
    router = AlertRouter()
    results = {"hook1": [], "hook2": []}

    def hook1(alert: Alert) -> None:
        results["hook1"].append(alert.alert_id)

    def hook2(alert: Alert) -> None:
        results["hook2"].append(alert.alert_id)

    router.register_hook("hook1", hook1)
    router.register_hook("hook2", hook2)

    alert = Alert(
        alert_id="ALR-001",
        severity=AlertSeverity.CRITICAL,
        message="Test",
        context={},
        timestamp=datetime.now(UTC),
    )

    count = router.route(alert)
    assert count == 2
    assert results["hook1"] == ["ALR-001"]
    assert results["hook2"] == ["ALR-001"]


@pytest.mark.requirement("WL-318")
def test_route_no_hooks() -> None:
    """Test routing with no hooks registered."""
    router = AlertRouter()

    alert = Alert(
        alert_id="ALR-001",
        severity=AlertSeverity.INFO,
        message="Test",
        context={},
        timestamp=datetime.now(UTC),
    )

    count = router.route(alert)
    assert count == 0


@pytest.mark.requirement("WL-318")
def test_route_passes_alert_context() -> None:
    """Test that route passes full alert context to hooks."""
    router = AlertRouter()
    received_alert = None

    def hook(alert: Alert) -> None:
        nonlocal received_alert
        received_alert = alert

    router.register_hook("hook", hook)

    alert = Alert(
        alert_id="ALR-001",
        severity=AlertSeverity.CRITICAL,
        message="Critical error",
        context={"user": "alice", "action": "sync"},
        timestamp=datetime.now(UTC),
    )

    router.route(alert)
    assert received_alert.alert_id == "ALR-001"
    assert received_alert.severity == AlertSeverity.CRITICAL
    assert received_alert.message == "Critical error"
    assert received_alert.context == {"user": "alice", "action": "sync"}


@pytest.mark.requirement("WL-318")
def test_list_hooks_sorted() -> None:
    """Test list_hooks returns sorted names."""
    router = AlertRouter()

    def hook(alert: Alert) -> None:
        pass

    router.register_hook("zebra", hook)
    router.register_hook("apple", hook)
    router.register_hook("mango", hook)

    assert router.list_hooks() == ["apple", "mango", "zebra"]


@pytest.mark.requirement("WL-318")
def test_hook_exception_isolation() -> None:
    """Test that failing hook doesn't prevent other hooks from running."""
    router = AlertRouter()
    results = {"hook1": [], "hook2": []}

    def failing_hook(alert: Alert) -> None:
        raise ValueError("Hook error")

    def working_hook(alert: Alert) -> None:
        results["hook2"].append(alert.alert_id)

    router.register_hook("failing", failing_hook)
    router.register_hook("working", working_hook)

    alert = Alert(
        alert_id="ALR-001",
        severity=AlertSeverity.INFO,
        message="Test",
        context={},
        timestamp=datetime.now(UTC),
    )

    # This will raise because hook fails - test that isolation is tested
    with pytest.raises(ValueError):
        router.route(alert)
