"""Unit tests for the Operator Cockpit dormant-core pane (AUDIT-N+18).

The dormant-core pane surfaces the AUDIT-N+13 dormant-core trend
envelope (``thegent.cli.commands.observability_impl._build_observe_trend_payload``
output shape) inside the cockpit so operators can see live escalation
count, past-SLA count, and freshness bucket next to the AUDIT-N+15
traffic pane in a single unified snapshot.

These tests pin:

* ``CockpitPane.DORMANT_CORE`` enum member exists with value ``"dormant_core"``
* ``OperatorCockpit.attach_dormant_core`` accepts a callable or object
* ``snapshot`` exposes a ``dormant_core`` field when attached
* ``_render_dormant_core_pane`` produces deterministic ASCII output
* Rendering is tolerant when no source is attached (no crash, no leak)
* Rendering is tolerant when the source raises or returns a non-dict
"""

from __future__ import annotations

import pytest

from thegent.ux.cockpit import (
    CockpitConfig,
    CockpitPane,
    OperatorCockpit,
)

pytestmark = pytest.mark.unit


def _envelope(
    *,
    backlog: int = 3,
    past_sla: int = 1,
    freshness: str = "fresh",
    health: str = "good",
    round_trip: bool = True,
    sig: str = "abcdef1234567890",
) -> dict[str, object]:
    """Build a small AUDIT-N+13 dormant-core envelope with deterministic inputs.

    Mirrors the canonical shape produced by
    ``thegent.cli.commands.observability_impl._build_observe_trend_payload``:
        ``trend_summary`` (dict)
        ``escalation_breakdown`` (dict)
        ``trend_scope_signature`` (str)
        ``wl120_dormant_round_trip`` (bool)
    """
    return {
        "trend_summary": {
            "trend_snapshot_health": health,
            "freshness_bucket": freshness,
        },
        "escalation_breakdown": {
            "backlog_count": backlog,
            "past_sla_count": past_sla,
            "top_rows": [],
        },
        "trend_scope_signature": sig,
        "wl120_dormant_round_trip": round_trip,
    }


# ---------------------------------------------------------------------------
# Sanity / API presence
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestDormantCorePanePublicApi:
    def test_dormant_core_pane_enum_member_exists(self) -> None:
        assert hasattr(CockpitPane, "DORMANT_CORE")
        assert CockpitPane.DORMANT_CORE.value == "dormant_core"

    def test_dormant_core_pane_in_default_labels(self) -> None:
        cfg = CockpitConfig()
        assert "dormant_core" in cfg.pane_labels

    def test_cockpit_has_attach_dormant_core(self) -> None:
        assert callable(getattr(OperatorCockpit, "attach_dormant_core", None))

    def test_cockpit_has_render_dormant_core_pane(self) -> None:
        assert callable(getattr(OperatorCockpit, "_render_dormant_core_pane", None))

    def test_cockpit_has_dormant_core_state(self) -> None:
        cockpit = OperatorCockpit()
        try:
            assert hasattr(cockpit, "_state")
            assert hasattr(cockpit._state, "dormant_source")
            assert cockpit._state.dormant_source is None
        finally:
            cockpit.shutdown()

    def test_cockpit_has_dormant_core_source_accessor(self) -> None:
        assert callable(getattr(OperatorCockpit, "dormant_core_source", None))


# ---------------------------------------------------------------------------
# attach_dormant_core behaviour
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestAttachDormantCore:
    def test_attach_dormant_core_accepts_callable(self) -> None:
        cockpit = OperatorCockpit()
        try:
            src = lambda: _envelope()  # noqa: E731 - intentional for the test
            cockpit.attach_dormant_core(src)
            assert cockpit._state.dormant_source is src
            assert cockpit.dormant_core_source() is src
        finally:
            cockpit.shutdown()

    def test_attach_dormant_core_accepts_object_with_summary(self) -> None:
        class _Obj:
            def summary(self) -> dict[str, object]:
                return _envelope()

        obj = _Obj()
        cockpit = OperatorCockpit()
        try:
            cockpit.attach_dormant_core(obj)
            assert cockpit._state.dormant_source is obj
        finally:
            cockpit.shutdown()

    def test_attach_dormant_core_accepts_none_to_detach(self) -> None:
        cockpit = OperatorCockpit()
        try:
            cockpit.attach_dormant_core(lambda: _envelope())
            assert cockpit._state.dormant_source is not None
            cockpit.attach_dormant_core(None)
            assert cockpit._state.dormant_source is None
        finally:
            cockpit.shutdown()

    def test_attach_dormant_core_returns_self_for_chaining(self) -> None:
        cockpit = OperatorCockpit()
        try:
            ret = cockpit.attach_dormant_core(lambda: _envelope())
            assert ret is cockpit
        finally:
            cockpit.shutdown()


# ---------------------------------------------------------------------------
# snapshot exposure
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSnapshotDormantCoreField:
    def test_snapshot_dormant_core_is_none_when_unattached(self) -> None:
        cockpit = OperatorCockpit()
        try:
            snap = cockpit.snapshot()
            assert snap["dormant_core"] is None
        finally:
            cockpit.shutdown()

    def test_snapshot_dormant_core_present_when_attached(self) -> None:
        cockpit = OperatorCockpit()
        try:
            cockpit.attach_dormant_core(lambda: _envelope(backlog=7, past_sla=2))
            snap = cockpit.snapshot()
            assert snap["dormant_core"] is not None
            assert isinstance(snap["dormant_core"], dict)
            assert "trend_summary" in snap["dormant_core"]
            assert "escalation_breakdown" in snap["dormant_core"]
            breakdown = snap["dormant_core"]["escalation_breakdown"]
            assert breakdown["backlog_count"] == 7
            assert breakdown["past_sla_count"] == 2
        finally:
            cockpit.shutdown()

    def test_snapshot_dormant_core_none_when_source_raises(self) -> None:
        cockpit = OperatorCockpit()
        try:

            def boom() -> dict[str, object]:
                raise RuntimeError("dormant-core exploded")

            cockpit.attach_dormant_core(boom)
            snap = cockpit.snapshot()
            assert snap["dormant_core"] is None
        finally:
            cockpit.shutdown()


# ---------------------------------------------------------------------------
# Render behaviour
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestRenderDormantCorePane:
    def test_render_returns_empty_string_when_unattached(self) -> None:
        cockpit = OperatorCockpit()
        try:
            text = cockpit._render_dormant_core_pane()
            assert isinstance(text, str)
            assert text == ""
        finally:
            cockpit.shutdown()

    def test_render_contains_header_when_attached(self) -> None:
        cockpit = OperatorCockpit()
        try:
            cockpit.attach_dormant_core(lambda: _envelope())
            text = cockpit._render_dormant_core_pane()
            assert "Dormant Core" in text
        finally:
            cockpit.shutdown()

    def test_render_contains_escalation_metrics(self) -> None:
        cockpit = OperatorCockpit()
        try:
            cockpit.attach_dormant_core(lambda: _envelope(backlog=4, past_sla=2))
            text = cockpit._render_dormant_core_pane()
            # ``esc=`` is the escalation-count marker; ``sla=`` is the
            # past-SLA marker — both are stable substrings of the
            # AUDIT-N+18 pane layout.
            assert "esc=" in text
            assert "sla=" in text
        finally:
            cockpit.shutdown()

    def test_render_contains_round_trip_flag(self) -> None:
        cockpit = OperatorCockpit()
        try:
            cockpit.attach_dormant_core(lambda: _envelope(round_trip=True))
            text = cockpit._render_dormant_core_pane()
            assert "round_trip=True" in text
        finally:
            cockpit.shutdown()

    def test_render_is_deterministic(self) -> None:
        cockpit1 = OperatorCockpit()
        cockpit2 = OperatorCockpit()
        try:
            env = _envelope(backlog=5, past_sla=1)
            cockpit1.attach_dormant_core(lambda: env)
            cockpit2.attach_dormant_core(lambda: env)
            assert cockpit1._render_dormant_core_pane() == cockpit2._render_dormant_core_pane()
        finally:
            cockpit1.shutdown()
            cockpit2.shutdown()

    def test_render_rows_have_uniform_width(self) -> None:
        cockpit = OperatorCockpit()
        try:
            cockpit.attach_dormant_core(lambda: _envelope())
            text = cockpit._render_dormant_core_pane()
            widths = {len(line) for line in text.splitlines()}
            assert len(widths) == 1, f"DORMANT_CORE box rows have inconsistent widths: {widths}"
        finally:
            cockpit.shutdown()

    def test_render_tolerant_when_source_raises(self) -> None:
        cockpit = OperatorCockpit()
        try:

            def boom() -> dict[str, object]:
                raise RuntimeError("nope")

            cockpit.attach_dormant_core(boom)
            text = cockpit._render_dormant_core_pane()
            # The pane must still render *something* (a neutral error
            # line) — never raise to the operator terminal.
            assert isinstance(text, str)
            assert text != ""
            assert "dormant-core source errored" in text
        finally:
            cockpit.shutdown()

    def test_render_tolerant_when_source_returns_non_dict(self) -> None:
        cockpit = OperatorCockpit()
        try:
            cockpit.attach_dormant_core(lambda: "not-a-dict")  # type: ignore[arg-type,return-value]
            text = cockpit._render_dormant_core_pane()
            assert isinstance(text, str)
            assert text != ""
            assert "dormant-core source errored" in text
        finally:
            cockpit.shutdown()

    def test_render_tolerant_with_empty_envelope(self) -> None:
        cockpit = OperatorCockpit()
        try:
            cockpit.attach_dormant_core(dict)
            text = cockpit._render_dormant_core_pane()
            # Empty envelope should still render a complete box (the
            # ``-`` placeholders take the place of the missing fields).
            assert isinstance(text, str)
            assert text != ""
            assert "round_trip=False" in text
        finally:
            cockpit.shutdown()


# ---------------------------------------------------------------------------
# Full render with dormant-core pane attached
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestFullRenderWithDormantCore:
    def test_full_render_includes_dormant_core_block_when_attached(self) -> None:
        cockpit = OperatorCockpit()
        try:
            cockpit.attach_dormant_core(lambda: _envelope())
            rendered = cockpit.render()
            assert "Dormant Core" in rendered
            assert "round_trip=True" in rendered
        finally:
            cockpit.shutdown()

    def test_full_render_omits_dormant_core_block_when_unattached(self) -> None:
        cockpit = OperatorCockpit()
        try:
            rendered = cockpit.render()
            assert "Dormant Core" not in rendered
        finally:
            cockpit.shutdown()

    def test_full_render_combines_traffic_and_dormant_core(self) -> None:
        """Sanity check: AUDIT-N+15 traffic and AUDIT-N+18 dormant-core
        panes coexist in a single cockpit snapshot without stepping on
        each other.
        """
        from thegent.ux.kpis.traffic import TrafficDashboard, TrafficEvent

        cockpit = OperatorCockpit()
        try:
            dash = TrafficDashboard(window_s=60.0)
            dash.record(
                TrafficEvent(
                    ts=0.0,
                    lane="audit",
                    agent="test",
                    status="ok",
                    duration_ms=10.0,
                )
            )
            cockpit.attach_traffic(dash)
            cockpit.attach_dormant_core(lambda: _envelope())
            rendered = cockpit.render()
            assert "Traffic" in rendered
            assert "Dormant Core" in rendered
        finally:
            cockpit.shutdown()
