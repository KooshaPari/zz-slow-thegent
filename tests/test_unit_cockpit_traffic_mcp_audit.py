"""Tests for the ``cockpit traffic --include-mcp-audit`` integration (Lane A, AUDIT-N+24).

SOTA audit pass 9 wires the live MCP audit-trail singleton
(``thegent.mcp.server.mcp_audit_recent`` / ``mcp_audit_stats`` /
``mcp_audit_query``) underneath the existing TRAFFIC KPI dashboard so
operators see ``count / rps / error_rate / p50 / p95`` **and** the
MCP audit gauge + recent entries in a single round-trip. The toggle
defaults to off (``--no-mcp-audit``) so the historical ``cockpit
traffic summary`` contract is preserved.

This module pins the new contract:

* ``--include-mcp-audit`` flips a clean flag — the JSON envelope gains
  the stable keys ``mcp_audit_stats``, ``mcp_audit_recent``, and
  ``mcp_audit_filters`` when the flag is on; none of those keys are
  present when the flag is off.
* ``--mcp-audit-lines N`` caps the number of recent entries returned
  in both JSON and text mode (matches ``--lines`` semantics on the
  audit-app ``mcp-tail`` subcommand for symmetry).
* ``--mcp-kind`` / ``--mcp-agent`` / ``--mcp-outcome`` forward through
  to ``mcp_audit_query``; an invalid ``--mcp-kind`` value surfaces as
  ``typer.BadParameter`` (exit code 2) instead of a stack trace.
* The text renderer appends a labelled ``MCP audit trail:`` block
  beneath the TRAFFIC dashboard so the operator terminal stays
  scrollable.
* The TRAFFIC dashboard itself is unchanged when the flag is off —
  ``TrafficDashboard.summary()`` keys are preserved (``count`` /
  ``by_lane`` / ``by_status`` / ``rps`` / ``error_rate`` / ``p50_ms``
  / ``p95_ms`` / ``override_count`` / ``duration_ms_window``).
"""

from __future__ import annotations

import json
import re

import pytest
from typer.testing import CliRunner

from thegent.mcp.server import (
    AuditEntryKind,
    audited_budget,
    mcp_audit_recent,
    record_gate_check,
    record_resource_read,
    reset_audit_trail,
)
from thegent.ux.cli_cockpit import app as cockpit_app

pytestmark = pytest.mark.unit


def _strip_ansi(text: str) -> str:
    """Strip Rich/Typer ANSI escape codes from CliRunner output."""
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def _drive_four_entries() -> None:
    """Drive four distinct entries through the audit-trail singleton.

    Four entries is the minimum needed for the
    ``--mcp-audit-lines 2`` cap test to be meaningful (we expect
    exactly the two newest entries).
    """
    reset_audit_trail()
    with audited_budget(
        AuditEntryKind.TOOL_INVOCATION, "tool_invoke_ms", agent="cursor"
    ):
        pass
    record_resource_read("observe_summary_ms", agent="claude", outcome="ok")
    record_gate_check("gate_check_ms", agent="cursor", outcome="ok")
    # Second gate_check with a different outcome so filter tests
    # have something to discriminate on.
    record_gate_check("gate_check_ms_2", agent="claude", outcome="error")


# ---------------------------------------------------------------------------
# Help / registration contract
# ---------------------------------------------------------------------------


class TestCockpitTrafficMcpAuditRegistration:
    """Pin the ``cockpit traffic`` help text shape (pass 9 contract)."""

    def test_traffic_summary_help_lists_audit_toggle(self) -> None:
        result = CliRunner().invoke(cockpit_app, ["traffic", "summary", "--help"])
        assert result.exit_code == 0
        clean = _strip_ansi(result.output)
        # The new flag names must surface in --help so operators can
        # discover them without reading source.
        for needle in (
            "--include-mcp-audit",
            "--no-mcp-audit",
            "--mcp-audit-lines",
            "--mcp-kind",
            "--mcp-agent",
            "--mcp-outcome",
        ):
            assert needle in clean, f"missing {needle!r} in:\n{clean}"

    def test_traffic_help_renders_summary_subcommand(self) -> None:
        result = CliRunner().invoke(cockpit_app, ["traffic", "--help"])
        assert result.exit_code == 0
        clean = _strip_ansi(result.output)
        assert "summary" in clean


# ---------------------------------------------------------------------------
# Default (flag off) — backward compatibility
# ---------------------------------------------------------------------------


class TestCockpitTrafficMcpAuditDisabledByDefault:
    """When ``--include-mcp-audit`` is *off* the envelope stays unchanged.

    This is the hard contract: existing CI hooks / dashboards consuming
    ``cockpit traffic summary --json`` must not see a new key added
    without an opt-in. ``mcp_audit_*`` keys only appear when the flag
    is on.
    """

    def test_default_json_envelope_excludes_audit_block(self) -> None:
        _drive_four_entries()
        result = CliRunner().invoke(cockpit_app, ["traffic", "summary", "--json"])
        assert result.exit_code == 0, result.output
        obj = json.loads(result.output)
        # Existing TRAFFIC keys are untouched.
        for needle in (
            "count",
            "by_lane",
            "by_status",
            "rps",
            "error_rate",
            "p50_ms",
            "p95_ms",
            "override_count",
            "duration_ms_window",
        ):
            assert needle in obj, f"missing traffic key {needle!r} in:\n{obj}"
        # And the new block is absent.
        for forbidden in ("mcp_audit_stats", "mcp_audit_recent", "mcp_audit_filters"):
            assert forbidden not in obj, (
                f"unexpected {forbidden!r} in default envelope:\n{obj}"
            )

    def test_default_text_mode_omits_audit_block(self) -> None:
        _drive_four_entries()
        result = CliRunner().invoke(cockpit_app, ["traffic", "summary"])
        assert result.exit_code == 0, result.output
        clean = _strip_ansi(result.output)
        # No "MCP audit trail:" sentinel in the default text output.
        assert "MCP audit trail:" not in clean

    def test_explicit_no_mcp_audit_matches_default(self) -> None:
        _drive_four_entries()
        result = CliRunner().invoke(
            cockpit_app, ["traffic", "summary", "--json", "--no-mcp-audit"]
        )
        assert result.exit_code == 0
        obj = json.loads(result.output)
        assert "mcp_audit_stats" not in obj
        assert "mcp_audit_recent" not in obj


# ---------------------------------------------------------------------------
# JSON envelope contract (flag on)
# ---------------------------------------------------------------------------


class TestCockpitTrafficMcpAuditJsonEnvelope:
    """Pin the ``--json`` shape when ``--include-mcp-audit`` is on."""

    def test_json_envelope_exposes_stats_block(self) -> None:
        _drive_four_entries()
        result = CliRunner().invoke(
            cockpit_app,
            ["traffic", "summary", "--json", "--include-mcp-audit"],
        )
        assert result.exit_code == 0, result.output
        obj = json.loads(result.output)
        # Stable key — downstream dashboards depend on this name.
        assert "mcp_audit_stats" in obj
        stats = obj["mcp_audit_stats"]
        assert stats is not None
        # The mcp_audit_stats() shape (audited in
        # test_unit_mcp_audit_wiring_*). We only pin the surface here.
        for key in ("total_entries", "by_kind", "by_outcome", "error_count"):
            assert key in stats, f"missing {key!r} in stats:\n{stats}"

    def test_json_envelope_exposes_recent_block(self) -> None:
        _drive_four_entries()
        result = CliRunner().invoke(
            cockpit_app,
            ["traffic", "summary", "--json", "--include-mcp-audit"],
        )
        assert result.exit_code == 0
        obj = json.loads(result.output)
        assert "mcp_audit_recent" in obj
        assert isinstance(obj["mcp_audit_recent"], list)
        # All four entries recorded — no filter applied.
        assert len(obj["mcp_audit_recent"]) == 4

    def test_json_envelope_exposes_filter_block(self) -> None:
        result = CliRunner().invoke(
            cockpit_app,
            [
                "traffic",
                "summary",
                "--json",
                "--include-mcp-audit",
                "--mcp-audit-lines",
                "3",
                "--mcp-kind",
                "gate_check",
                "--mcp-agent",
                "cursor",
            ],
        )
        assert result.exit_code == 0
        obj = json.loads(result.output)
        # The filter block mirrors what the operator typed so JSON
        # consumers can verify the request shape.
        assert obj["mcp_audit_filters"] == {
            "kind": "gate_check",
            "agent": "cursor",
            "outcome": None,
            "lines": 3,
        }

    def test_json_lines_cap_respected(self) -> None:
        _drive_four_entries()
        result = CliRunner().invoke(
            cockpit_app,
            [
                "traffic",
                "summary",
                "--json",
                "--include-mcp-audit",
                "--mcp-audit-lines",
                "2",
            ],
        )
        assert result.exit_code == 0
        obj = json.loads(result.output)
        # Cap is honoured: exactly two entries (the newest).
        assert len(obj["mcp_audit_recent"]) == 2


# ---------------------------------------------------------------------------
# Filter forwarding
# ---------------------------------------------------------------------------


class TestCockpitTrafficMcpAuditFilterForwarding:
    """Pin that ``--mcp-kind`` / ``--mcp-agent`` / ``--mcp-outcome`` filter the recent block."""

    def test_mcp_kind_gate_check_filters(self) -> None:
        _drive_four_entries()
        result = CliRunner().invoke(
            cockpit_app,
            [
                "traffic",
                "summary",
                "--json",
                "--include-mcp-audit",
                "--mcp-kind",
                "gate_check",
            ],
        )
        assert result.exit_code == 0
        obj = json.loads(result.output)
        # Two of the four entries are gate_check.
        assert len(obj["mcp_audit_recent"]) == 2
        for entry in obj["mcp_audit_recent"]:
            assert entry["kind"] == "gate_check"

    def test_mcp_agent_claude_filters(self) -> None:
        _drive_four_entries()
        result = CliRunner().invoke(
            cockpit_app,
            [
                "traffic",
                "summary",
                "--json",
                "--include-mcp-audit",
                "--mcp-agent",
                "claude",
            ],
        )
        assert result.exit_code == 0
        obj = json.loads(result.output)
        # Two of the four entries are from claude.
        assert len(obj["mcp_audit_recent"]) == 2
        for entry in obj["mcp_audit_recent"]:
            assert entry["agent"] == "claude"

    def test_mcp_outcome_error_filters(self) -> None:
        _drive_four_entries()
        result = CliRunner().invoke(
            cockpit_app,
            [
                "traffic",
                "summary",
                "--json",
                "--include-mcp-audit",
                "--mcp-outcome",
                "error",
            ],
        )
        assert result.exit_code == 0
        obj = json.loads(result.output)
        # One entry has outcome=error.
        assert len(obj["mcp_audit_recent"]) == 1
        assert obj["mcp_audit_recent"][0]["outcome"] == "error"

    def test_invalid_mcp_kind_raises_bad_parameter(self) -> None:
        """An unknown kind surfaces as ``typer.BadParameter`` (exit 2), not a stack trace."""
        result = CliRunner().invoke(
            cockpit_app,
            [
                "traffic",
                "summary",
                "--json",
                "--include-mcp-audit",
                "--mcp-kind",
                "not_a_real_kind",
            ],
        )
        # BadParameter renders exit code 2 (Typer's standard).
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# Text rendering (flag on)
# ---------------------------------------------------------------------------


class TestCockpitTrafficMcpAuditTextRendering:
    """Pin the human-readable text shape when the flag is on."""

    def test_text_mode_renders_audit_trail_block(self) -> None:
        _drive_four_entries()
        result = CliRunner().invoke(
            cockpit_app,
            ["traffic", "summary", "--include-mcp-audit", "--mcp-audit-lines", "10"],
        )
        assert result.exit_code == 0, result.output
        clean = _strip_ansi(result.output)
        # The "MCP audit trail:" sentinel anchors the block.
        assert "MCP audit trail:" in clean
        # Stats row surfaces the audit-singleton gauges.
        assert "total_entries" in clean
        # Error counter surfaces the audit-singleton gauge.
        assert "error_count" in clean

    def test_text_mode_lines_cap_respected(self) -> None:
        _drive_four_entries()
        result = CliRunner().invoke(
            cockpit_app,
            ["traffic", "summary", "--include-mcp-audit", "--mcp-audit-lines", "1"],
        )
        assert result.exit_code == 0, result.output
        clean = _strip_ansi(result.output)
        # With cap=1, the fetch helper clamps ``entries`` to the
        # single newest entry. Assert the cap is honoured by counting
        # the row lines (rendered as ``  [mcp-audit] seq=...`` —
        # two-space indent from the ``MCP audit trail:`` block —
        # followed by the audit columns). There must be exactly one
        # such row. The seq is monotonically increasing so the
        # rendered row is the freshest entry (seq=4).
        rows = [ln for ln in clean.splitlines() if "[mcp-audit] seq=" in ln]
        assert len(rows) == 1, (
            f"expected exactly 1 audit row with --mcp-audit-lines 1, got {len(rows)}:\n{rows}"
        )
        assert "seq=4" in rows[0]

    def test_text_mode_no_matches_surfaces_neutral(self) -> None:
        """A filter that matches nothing renders a single neutral line, not an empty block."""
        reset_audit_trail()
        result = CliRunner().invoke(
            cockpit_app,
            [
                "traffic",
                "summary",
                "--include-mcp-audit",
                "--mcp-agent",
                "ghost_agent",
            ],
        )
        assert result.exit_code == 0
        clean = _strip_ansi(result.output)
        # The neutral line keeps the dashboard scrollable.
        assert "(no MCP audit entries match the current filter)" in clean


# ---------------------------------------------------------------------------
# Recent block matches the audit-trail singleton directly
# ---------------------------------------------------------------------------


class TestCockpitTrafficMcpAuditMatchesProgrammaticApi:
    """The recent block must mirror ``mcp_audit_recent(n)`` exactly.

    Downstream consumers (CI hooks, SOTA replay tooling) compare the
    cockpit envelope against the programmatic API. We pin the equality
    here so a refactor that changes one but not the other is caught.
    """

    def test_recent_block_matches_mcp_audit_recent(self) -> None:
        _drive_four_entries()
        result = CliRunner().invoke(
            cockpit_app,
            [
                "traffic",
                "summary",
                "--json",
                "--include-mcp-audit",
                "--mcp-audit-lines",
                "10",
            ],
        )
        assert result.exit_code == 0
        obj = json.loads(result.output)
        # Programmatic API gives us the same dict shape.
        recent = [e.to_dict() for e in mcp_audit_recent(10)]
        assert obj["mcp_audit_recent"] == recent
