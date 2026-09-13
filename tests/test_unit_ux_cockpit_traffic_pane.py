"""Unit tests for the Operator Cockpit traffic pane (AUDIT-N+15).

The traffic pane surfaces live :class:`TrafficDashboard` data inside the
cockpit so operators can see request count, error rate, and latency
percentiles next to the run/lane/confidence/overrides panes.

These tests pin:

* ``CockpitPane.TRAFFIC`` enum member exists with value ``"traffic"``
* ``OperatorCockpit.attach_traffic`` accepts a ``TrafficDashboard``
* ``snapshot`` exposes a ``traffic`` field when attached
* ``_render_traffic_pane`` produces deterministic ASCII output
* Rendering is tolerant when no dashboard is attached (no crash, no leak)
"""

from __future__ import annotations

import time

import pytest

from thegent.ux.cockpit import (
    CockpitConfig,
    CockpitPane,
    OperatorCockpit,
)
from thegent.ux.kpis.traffic import TrafficDashboard, TrafficEvent

pytestmark = pytest.mark.unit


def _dashboard(count: int = 10, error_rate: float = 0.0) -> TrafficDashboard:
    """Build a small traffic dashboard with deterministic inputs."""
    dash = TrafficDashboard(window_s=60.0)
    for i in range(count):
        dash.record(
            TrafficEvent(
                ts=time.time(),
                lane="audit",
                agent="test",
                status="error" if i % 5 == 0 else "ok",
                duration_ms=10.0 + (i * 2.0),
            )
        )
    return dash


# ---------------------------------------------------------------------------
# Sanity / API presence
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestTrafficPanePublicApi:
    def test_traffic_pane_enum_member_exists(self) -> None:
        assert hasattr(CockpitPane, "TRAFFIC")
        assert CockpitPane.TRAFFIC.value == "traffic"

    def test_traffic_pane_in_default_labels(self) -> None:
        cfg = CockpitConfig()
        assert "traffic" in cfg.pane_labels

    def test_cockpit_has_attach_traffic(self) -> None:
        assert callable(getattr(OperatorCockpit, "attach_traffic", None))

    def test_cockpit_has_render_traffic_pane(self) -> None:
        assert callable(getattr(OperatorCockpit, "_render_traffic_pane", None))

    def test_cockpit_has_traffic_dashboard_state(self) -> None:
        cockpit = OperatorCockpit()
        try:
            assert hasattr(cockpit, "_state")
            assert hasattr(cockpit._state, "traffic_dashboard")
        finally:
            cockpit.shutdown()


# ---------------------------------------------------------------------------
# attach_traffic behaviour
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestAttachTraffic:
    def test_attach_traffic_stores_dashboard_reference(self) -> None:
        cockpit = OperatorCockpit()
        try:
            dash = _dashboard(count=5)
            cockpit.attach_traffic(dash)
            assert cockpit._state.traffic_dashboard is dash
        finally:
            cockpit.shutdown()

    def test_attach_traffic_accepts_none_to_detach(self) -> None:
        cockpit = OperatorCockpit()
        try:
            dash = _dashboard(count=3)
            cockpit.attach_traffic(dash)
            assert cockpit._state.traffic_dashboard is dash
            cockpit.attach_traffic(None)
            assert cockpit._state.traffic_dashboard is None
        finally:
            cockpit.shutdown()

    def test_attach_traffic_rejects_non_dashboard(self) -> None:
        cockpit = OperatorCockpit()
        try:
            with pytest.raises(TypeError):
                cockpit.attach_traffic("not-a-dashboard")  # type: ignore[arg-type]
        finally:
            cockpit.shutdown()


# ---------------------------------------------------------------------------
# snapshot exposure
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSnapshotTrafficField:
    def test_snapshot_traffic_is_none_when_unattached(self) -> None:
        cockpit = OperatorCockpit()
        try:
            snap = cockpit.snapshot()
            assert snap["traffic"] is None
        finally:
            cockpit.shutdown()

    def test_snapshot_traffic_present_when_attached(self) -> None:
        cockpit = OperatorCockpit()
        try:
            dash = _dashboard(count=7, error_rate=0.0)
            cockpit.attach_traffic(dash)
            snap = cockpit.snapshot()
            assert snap["traffic"] is not None
            assert isinstance(snap["traffic"], dict)
            assert "count" in snap["traffic"]
            assert snap["traffic"]["count"] == 7
        finally:
            cockpit.shutdown()


# ---------------------------------------------------------------------------
# Render behaviour
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestRenderTrafficPane:
    def test_render_returns_empty_string_when_unattached(self) -> None:
        cockpit = OperatorCockpit()
        try:
            text = cockpit._render_traffic_pane()
            assert isinstance(text, str)
            assert text == ""
        finally:
            cockpit.shutdown()

    def test_render_contains_header_when_attached(self) -> None:
        cockpit = OperatorCockpit()
        try:
            dash = _dashboard(count=4)
            cockpit.attach_traffic(dash)
            text = cockpit._render_traffic_pane()
            assert "Traffic" in text
        finally:
            cockpit.shutdown()

    def test_render_contains_latency_metrics(self) -> None:
        cockpit = OperatorCockpit()
        try:
            dash = _dashboard(count=6)
            cockpit.attach_traffic(dash)
            text = cockpit._render_traffic_pane()
            assert "p50" in text or "p95" in text
        finally:
            cockpit.shutdown()


# ---------------------------------------------------------------------------
# Full render with traffic pane attached
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestFullRenderWithTraffic:
    def test_full_render_includes_traffic_block(self) -> None:
        cockpit = OperatorCockpit()
        try:
            dash = _dashboard(count=3)
            cockpit.attach_traffic(dash)
            rendered = cockpit.render()
            assert "Traffic" in rendered
        finally:
            cockpit.shutdown()

    def test_full_render_omits_traffic_block_when_unattached(self) -> None:
        cockpit = OperatorCockpit()
        try:
            rendered = cockpit.render()
            assert "Traffic" not in rendered
        finally:
            cockpit.shutdown()
