"""ARIA (L17 I18n/A11y) annotations on the operator cockpit renderers.

The cockpit renderers attach WAI-ARIA-style key/value trailers to the
closing border of each pane so screen readers and TUI inspection tools
can pick up the pane's role + live-region semantics without scraping
free-form text. These tests pin the wire format and the per-pane
contracts so a future refactor (e.g. moving the trailer to a different
line, changing the role, dropping the aria-label) cannot silently
regress the accessibility surface.

The task brief pins the dialect as ``[role=status aria-live=polite]``
for live status panes; the decision-history pane uses ``role="log"``
(the audit-log role) and the header uses ``role="region"`` (the
cockpit landmark).
"""

from __future__ import annotations

import pytest

from thegent.i18n.aria import annotate, parse_aria
from thegent.ux.cockpit import (
    CockpitConfig,
    DecisionNotice,
    OperatorCockpit,
    OverrideEvent,
    RunEvent,
    RunState,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _empty_cockpit() -> OperatorCockpit:
    """Build a cockpit with no events so the ARIA trailers ride on the
    placeholder rows."""
    return OperatorCockpit()


def _populated_cockpit() -> OperatorCockpit:
    """Build a cockpit with one run + one override so every pane has
    at least one rendered row."""
    c = OperatorCockpit()
    c.tick(
        runs=[
            RunEvent(
                run_id="run-001",
                state=RunState.ACTIVE,
                lane="critical",
                agent="cursor",
                confidence=0.92,
            ),
        ],
        overrides=[
            OverrideEvent(
                rule_id="no-cursor-prod",
                by="sre",
                reason="hotfix",
                expires_in_s=120,
            ),
        ],
        progress=(2, 8),
    )
    return c


# ---------------------------------------------------------------------------
# Wire format — the task brief pins the literal ``[role=status aria-live=polite]``
# ---------------------------------------------------------------------------


class TestAriaWireFormat:
    """The renderer produces the task-brief dtype ``[role=status aria-live=polite]``."""

    def test_runs_pane_uses_status_live_polite(self) -> None:
        """Live Runs pane lands in a polite live region with the status role."""
        out = _populated_cockpit().render()
        runs_lines = [
            line for line in out.splitlines() if "Live Runs" in line and "└" in line
        ]
        assert runs_lines, "Live Runs pane closing line not found in output"
        closing = runs_lines[-1]
        # The trailer rides on the closing border of the box.
        assert "[role=status aria-live=polite" in closing, closing
        # The label is preserved as the configurable aria-label.
        assert 'aria-label="Live Runs"' in closing, closing

    def test_lanes_pane_uses_status_live_polite(self) -> None:
        """Lane Distribution pane mirrors the live-runs annotation."""
        out = _populated_cockpit().render()
        closing = next(
            (
                line
                for line in out.splitlines()
                if "Lane Distribution" in line and "└" in line
            ),
            None,
        )
        assert closing, "Lane Distribution pane closing line not found"
        assert "[role=status aria-live=polite" in closing
        assert 'aria-label="Lane Distribution"' in closing

    def test_confidence_pane_uses_status_live_polite(self) -> None:
        """Confidence pane carries the same live-region annotation."""
        out = _populated_cockpit().render()
        closing = next(
            (line for line in out.splitlines() if "Confidence" in line and "└" in line),
            None,
        )
        assert closing, "Confidence pane closing line not found"
        assert "[role=status aria-live=polite" in closing
        assert 'aria-label="Confidence (P50/P95)"' in closing

    def test_overrides_pane_uses_status_live_polite(self) -> None:
        """Active Overrides pane carries the live-region annotation."""
        out = _populated_cockpit().render()
        closing = next(
            (
                line
                for line in out.splitlines()
                if "Active Overrides" in line and "└" in line
            ),
            None,
        )
        assert closing, "Active Overrides pane closing line not found"
        assert "[role=status aria-live=polite" in closing
        assert 'aria-label="Active Overrides"' in closing

    def test_decision_history_pane_uses_log_role(self) -> None:
        """Decision History uses ``role="log"`` (audit log, not status)."""
        out = _populated_cockpit().render()
        closing = next(
            (
                line
                for line in out.splitlines()
                if "Decision History" in line and "└" in line
            ),
            None,
        )
        assert closing, "Decision History pane closing line not found"
        assert "[role=log aria-live=polite" in closing, closing
        assert 'aria-label="Decision History"' in closing

    def test_header_uses_region_role(self) -> None:
        """The header line is wrapped in a region landmark."""
        out = _populated_cockpit().render()
        header_line = out.splitlines()[0]
        assert "[role=region" in header_line, header_line
        assert 'aria-label="thegent operator cockpit"' in header_line, header_line


# ---------------------------------------------------------------------------
# Each pane is structurally annotated
# ---------------------------------------------------------------------------


class TestAriaPerPane:
    """Every pane must carry an ARIA annotation; the literal token
    ``[role=status aria-live=polite]`` must appear at least once per
    pane (one per row of the 2x2 grid + the decision-history row)."""

    def test_all_four_panes_annotate(self) -> None:
        """The four main panes each emit an ARIA annotation."""
        out = _populated_cockpit().render()
        # At least four live-region annotations (one per pane in the 2x2 grid).
        assert out.count("[role=status aria-live=polite") >= 4, (
            f"expected >= 4 status live-region annotations, got {out.count('[role=status aria-live=polite')}\n"
            f"--- output ---\n{out}\n--- end ---"
        )

    def test_decision_history_annotates_with_log_role(self) -> None:
        """The decision-history pane is annotated with role=log."""
        out = _populated_cockpit().render()
        assert "[role=log aria-live=polite" in out

    def test_header_annotates_with_region_role(self) -> None:
        """The header is annotated as a region landmark."""
        out = _populated_cockpit().render()
        assert "[role=region" in out

    def test_annotations_parse_round_trip(self) -> None:
        """The ARIA trailer can be parsed back into a dict via ``parse_aria``."""
        out = _populated_cockpit().render()
        # The Live Runs pane's closing border rides on the same line as the
        # Lane Distribution pane's closing border (2x2 grid layout). The
        # Live Runs trailer is the FIRST bracketed trailer on the line.
        runs_line = next(
            line for line in out.splitlines() if "Live Runs" in line and "└" in line
        )
        # The Live Runs trailer is the first '[' on the line; the
        # second '[' is the Lane Distribution trailer.
        trailer = runs_line[runs_line.index("[") : runs_line.index("]") + 1]
        parsed = parse_aria(trailer)
        assert parsed["role"] == "status"
        assert parsed["aria-live"] == "polite"
        assert parsed["aria-label"] == "Live Runs"


# ---------------------------------------------------------------------------
# Default (aria_label=None) preserves the unannotated output
# ---------------------------------------------------------------------------


class TestAriaOptOut:
    """When ``aria_label`` is None (default), the closing border is bare
    so callers that have not opted in cannot accidentally emit ARIA."""

    def test_runs_pane_no_label_returns_plain_closing(self) -> None:
        c = _empty_cockpit()
        lines = c._render_runs_pane()
        assert lines[-1] == "└──────────────────────────────────────┘"

    def test_lanes_pane_no_label_returns_plain_closing(self) -> None:
        c = _empty_cockpit()
        lines = c._render_lanes_pane()
        assert lines[-1] == "└──────────────────────────────────────┘"

    def test_confidence_pane_no_label_returns_plain_closing(self) -> None:
        c = _empty_cockpit()
        lines = c._render_confidence_pane()
        assert lines[-1] == "└──────────────────────────────────────┘"

    def test_overrides_pane_no_label_returns_plain_closing(self) -> None:
        c = _empty_cockpit()
        lines = c._render_overrides_pane()
        assert lines[-1] == "└──────────────────────────────────────┘"

    def test_header_no_label_returns_plain_header(self) -> None:
        c = _empty_cockpit()
        out = c._render_header()
        # The progress bar contains plain ``[`` brackets which are NOT ARIA
        # trailers. The absence of an ARIA trailer is signalled by the absence
        # of the ``role=`` token that the ARIA helpers always emit.
        assert "role=" not in out
        assert "aria-label" not in out

    def test_decision_history_no_label_returns_plain_closing(self) -> None:
        c = _empty_cockpit()
        lines = c._render_decisions_pane()
        assert lines[-1] == "└─────────────────────────────────────────────────┘"


# ---------------------------------------------------------------------------
# Custom labels flow through to the rendered trailer
# ---------------------------------------------------------------------------


class TestAriaCustomLabels:
    """A ``CockpitConfig`` with custom ``pane_labels`` flows through to
    the rendered ARIA trailer unchanged."""

    def test_custom_pane_label_round_trips(self) -> None:
        from thegent.ux.cockpit import CockpitPane

        cfg = CockpitConfig(
            pane_labels={
                CockpitPane.RUNS: "Custom Runs",
                CockpitPane.LANES: "Custom Lanes",
                CockpitPane.CONFIDENCE: "Custom Confidence",
                CockpitPane.OVERRIDES: "Custom Overrides",
                CockpitPane.TRAFFIC: "Custom Traffic",
                CockpitPane.DORMANT_CORE: "Custom Dormant",
            }
        )
        c = OperatorCockpit(config=cfg)
        c.tick(
            runs=[RunEvent(run_id="r1", state=RunState.ACTIVE, lane="critical")],
            overrides=[
                OverrideEvent(rule_id="o1", by="alice", reason="r", expires_in_s=10)
            ],
            progress=(1, 1),
        )
        out = c.render()
        assert 'aria-label="Custom Runs"' in out
        assert 'aria-label="Custom Lanes"' in out
        assert 'aria-label="Custom Confidence"' in out
        assert 'aria-label="Custom Overrides"' in out


# ---------------------------------------------------------------------------
# Decision-history pane: ARIA log role honoured when a real notice is recorded
# ---------------------------------------------------------------------------


class TestAriaDecisionLogRole:
    """The decision-history pane uses ``role="log"`` because decisions
    are append-only audit data, not a transient status update."""

    def test_decision_history_role_log_with_real_notice(self) -> None:
        c = _empty_cockpit()
        c.record_decision(
            DecisionNotice(
                verdict="deny",
                reason_code="no_rule_match",
                rule_id="r1",
                agent="a",
                lane="critical",
                evaluated_at=1_700_000_000.0,
                reason="policy deny",
            )
        )
        out = c.render()
        lines = [
            line
            for line in out.splitlines()
            if "Decision History" in line and "└" in line
        ]
        assert lines, "Decision History pane closing line not found"
        assert "[role=log aria-live=polite" in lines[-1]


# ---------------------------------------------------------------------------
# Module-level helper: ``annotate`` is the canonical entry point
# ---------------------------------------------------------------------------


class TestAriaHelper:
    """The cockpit helpers use :func:`thegent.i18n.aria.annotate` so the
    trailer format stays consistent with the rest of the UX."""

    def test_annotate_appends_role_status_live_polite(self) -> None:
        result = annotate(
            "Live Runs",
            role="status",
            aria_live="polite",
            aria_label="Live Runs",
        )
        assert (
            result == 'Live Runs [role=status aria-live=polite aria-label="Live Runs"]'
        )

    def test_annotate_log_role_distinct(self) -> None:
        result = annotate(
            "Decision History",
            role="log",
            aria_live="polite",
            aria_label="Decision History",
        )
        assert result.startswith("Decision History [role=log aria-live=polite")
        assert "role=log" in result
        assert "role=status" not in result


# ---------------------------------------------------------------------------
# Smoke test: render output remains readable on a typical workload
# ---------------------------------------------------------------------------


class TestAriaRenderSmoke:
    """End-to-end: the rendered cockpit still contains all the original
    text so existing tests and downstream consumers keep working."""

    def test_render_still_contains_title(self) -> None:
        out = _populated_cockpit().render()
        assert "thegent operator cockpit" in out

    def test_render_still_contains_run_row(self) -> None:
        out = _populated_cockpit().render()
        assert "run-001" in out

    def test_render_still_contains_override_row(self) -> None:
        out = _populated_cockpit().render()
        assert "no-cursor-prod" in out

    def test_render_still_contains_progress_bar(self) -> None:
        out = _populated_cockpit().render()
        assert "25%" in out  # 2/8 = 25%

    def test_render_still_contains_lane_label(self) -> None:
        out = _populated_cockpit().render()
        assert "critical" in out

    def test_empty_cockpit_still_renders_placeholder(self) -> None:
        """An empty cockpit still emits the placeholder rows AND ARIA trailers."""
        out = _empty_cockpit().render()
        assert "no active runs" in out
        assert "no active overrides" in out
        # AND the ARIA trailers ride on the closing borders.
        assert "[role=status aria-live=polite" in out
        assert "[role=region" in out


# ---------------------------------------------------------------------------
# Forward-compatible: the literal ``[role=status aria-live=polite]``
# ---------------------------------------------------------------------------


class TestAriaLiteral:
    """The task brief pins the literal ``[role=status aria-live=polite]``
    as the contract for live status panes. This guard test pins the
    exact substring so a future refactor (e.g. ordering change in
    ``aria_attributes``) cannot silently break it."""

    def test_status_live_polite_token_present(self) -> None:
        out = _populated_cockpit().render()
        assert "[role=status aria-live=polite" in out, (
            "Task-brief contract: live status panes must emit the literal "
            "'[role=status aria-live=polite]' token. Got output:\n" + out
        )

    def test_log_role_token_present(self) -> None:
        out = _populated_cockpit().render()
        assert "[role=log aria-live=polite" in out, (
            "Decision-history pane must emit '[role=log aria-live=polite]'. Got output:\n"
            + out
        )

    def test_region_role_token_present(self) -> None:
        out = _populated_cockpit().render()
        assert "[role=region" in out, (
            "Header must emit '[role=region' landmark. Got output:\n" + out
        )
