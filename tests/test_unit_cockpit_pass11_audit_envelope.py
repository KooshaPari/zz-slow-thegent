"""Tests for the SOTA audit pass 11 cockpit-lane hardening (AUDIT-N+25).

Pass 11 closes two genuine, in-scope, in-branch gaps surfaced by the
Pass 9 carry-forward verification sweep:

1. ``cockpit render --json`` was never wired to attach the
   ``mcp_audit_stats`` source, so the snapshot envelope's
   ``mcp_audit_stats`` key was always ``null`` — a silent regression
   of the AUDIT-N+22 contract (Pass 8) that only the traffic pane
   honoured. Pass 11 adds a default-on ``--include-mcp-audit`` flag
   that calls ``cockpit.attach_audit_trail(mcp_audit_stats)`` so the
   key is populated for the canonical operator UX surface (the 4-pane
   cockpit).

2. ``cockpit audit mcp-tail --json`` returned line-delimited entries
   without echoing the resolved filter set, forcing CI consumers to
   re-parse argv to know which filters were applied. Pass 11 adds an
   opt-in ``--json-envelope`` flag that emits a single JSON object
   with ``filters`` / ``entries`` / ``count`` keys, mirroring the
   ``cockpit traffic --include-mcp-audit`` envelope contract. The
   default ``--json`` path keeps the line-delimited shape so existing
   ``head -n 1 | jq`` pipelines keep working unchanged.

Both lanes share the AUDIT-N+25 tag so the worklog + DAG tick tally
stays consistent.
"""

from __future__ import annotations

import json
import re

import pytest
from typer.testing import CliRunner

from thegent.mcp.server import (
    AuditEntryKind,
    audited_budget,
    record_gate_check,
    record_resource_read,
    reset_audit_trail,
)
from thegent.ux.cli_cockpit import app as cockpit_app

pytestmark = pytest.mark.unit


def _strip_ansi(text: str) -> str:
    """Strip Rich/Typer ANSI escape codes from CliRunner output."""
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def _drive_three_entries() -> None:
    """Drive three distinct entries through the audit-trail singleton."""
    reset_audit_trail()
    with audited_budget(
        AuditEntryKind.TOOL_INVOCATION, "tool_invoke_ms", agent="cursor"
    ):
        pass
    record_resource_read("observe_summary_ms", agent="claude", outcome="ok")
    record_gate_check("gate_check_ms", agent="cursor", outcome="ok")


# ---------------------------------------------------------------------------
# Lane 1 — cockpit render --json wires mcp_audit_stats
# ---------------------------------------------------------------------------


class TestCockpitRenderMcpAuditStats:
    """Pin the AUDIT-N+25 pass 11 contract for ``cockpit render --json``.

    The Pass 8 envelope contract already emitted a ``mcp_audit_stats``
    key in the snapshot, but the render command never attached the
    source so the key was perpetually ``null``. Pass 11 wires the
    source so the live audit-trail singleton stats are surfaced in
    the canonical 4-pane cockpit JSON envelope.
    """

    def test_render_json_envelope_contains_mcp_audit_stats_key(self) -> None:
        """The ``--json`` envelope always emits the ``mcp_audit_stats`` key."""
        result = CliRunner().invoke(cockpit_app, ["render", "--json"])
        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        # The key is part of the AUDIT-N+22 envelope contract (Pass 8)
        # and must be present even when the source is unattached.
        assert "mcp_audit_stats" in payload

    def test_render_json_default_includes_mcp_audit_stats_when_populated(self) -> None:
        """Default render (``--include-mcp-audit`` on) populates the key."""
        _drive_three_entries()
        result = CliRunner().invoke(cockpit_app, ["render", "--json"])
        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        stats = payload["mcp_audit_stats"]
        # With three entries driven through the singleton, the key
        # should be a dict, not ``null``. ``total_entries`` is the
        # canonical gauge validated by the existing MCP audit-trail
        # contract tests.
        assert isinstance(stats, dict), (
            f"expected dict, got {type(stats).__name__}: {stats!r}"
        )
        assert stats.get("total_entries", 0) >= 1

    def test_render_json_no_mcp_audit_keeps_key_as_none(self) -> None:
        """``--no-mcp-audit`` skips the attach so the key stays ``null``."""
        _drive_three_entries()
        result = CliRunner().invoke(
            cockpit_app,
            ["render", "--json", "--no-mcp-audit"],
        )
        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        # The key is part of the envelope contract (Pass 8) so it
        # must still be present, but ``--no-mcp-audit`` skips the
        # attach so the value is ``null``.
        assert "mcp_audit_stats" in payload
        assert payload["mcp_audit_stats"] is None

    def test_render_json_help_lists_audit_toggle(self) -> None:
        """The new ``--include-mcp-audit`` flag must surface in ``--help``."""
        result = CliRunner().invoke(cockpit_app, ["render", "--help"])
        assert result.exit_code == 0
        clean = _strip_ansi(result.output)
        for needle in ("--include-mcp-audit", "--no-mcp-audit"):
            assert needle in clean, f"missing {needle!r} in:\n{clean}"

    def test_render_text_mode_is_unchanged(self) -> None:
        """Text mode is unaffected by the audit-trail wiring."""
        _drive_three_entries()
        result = CliRunner().invoke(
            cockpit_app,
            ["render", "--progress-done", "5", "--progress-total", "10"],
        )
        assert result.exit_code == 0
        # The 4-pane cockpit always emits the title line and a
        # progress bar like ``[##-------...]``.
        assert "operator cockpit" in result.output
        assert "[##" in result.output


# ---------------------------------------------------------------------------
# Lane 2 — cockpit audit mcp-tail --json-envelope echo
# ---------------------------------------------------------------------------


class TestCockpitAuditMcpTailJsonEnvelope:
    """Pin the AUDIT-N+25 pass 11 contract for ``cockpit audit mcp-tail``.

    The default ``--json`` mode stays line-delimited (Pass 9 contract)
    so existing grep-style pipelines keep working. The new
    ``--json-envelope`` flag adds a single JSON object with
    ``filters`` / ``entries`` / ``count`` keys, mirroring the
    ``cockpit traffic --include-mcp-audit`` envelope shape so CI
    consumers can introspect the resolved filter set in one
    round-trip.
    """

    def test_json_envelope_emits_single_object_with_filters(self) -> None:
        _drive_three_entries()
        result = CliRunner().invoke(
            cockpit_app,
            [
                "audit",
                "mcp-tail",
                "--json",
                "--json-envelope",
                "--kind",
                "gate_check",
                "--agent",
                "cursor",
            ],
        )
        assert result.exit_code == 0, result.output
        # Single envelope, not line-delimited.
        obj = json.loads(result.output)
        # The filter echo is the whole point of this lane.
        assert obj["filters"] == {
            "kind": "gate_check",
            "agent": "cursor",
            "outcome": None,
            "lines": 20,
        }
        # The entries list contains the filtered entries.
        assert "entries" in obj
        assert obj["count"] == len(obj["entries"])
        for entry in obj["entries"]:
            assert entry["kind"] == "gate_check"
            assert entry["agent"] == "cursor"

    def test_json_envelope_count_matches_entries_length(self) -> None:
        _drive_three_entries()
        result = CliRunner().invoke(
            cockpit_app,
            ["audit", "mcp-tail", "--json", "--json-envelope", "--lines", "2"],
        )
        assert result.exit_code == 0, result.output
        obj = json.loads(result.output)
        assert obj["count"] == 2
        assert len(obj["entries"]) == 2
        assert obj["filters"]["lines"] == 2

    def test_json_envelope_stats_only_emits_stats_block(self) -> None:
        """``--json-envelope --stats`` emits the stats block, no entries list."""
        _drive_three_entries()
        result = CliRunner().invoke(
            cockpit_app,
            ["audit", "mcp-tail", "--json", "--json-envelope", "--stats"],
        )
        assert result.exit_code == 0, result.output
        obj = json.loads(result.output)
        # Roll-up keys are present, entries list is absent.
        assert "stats" in obj
        assert obj["stats"]["total_entries"] >= 1
        assert "entries" not in obj
        # And the filters echo is still there.
        assert obj["filters"] == {
            "kind": None,
            "agent": None,
            "outcome": None,
            "lines": 20,
        }

    def test_json_envelope_empty_trail_returns_empty_entries(self) -> None:
        """An empty trail yields ``entries=[]`` and ``count=0``."""
        reset_audit_trail()
        result = CliRunner().invoke(
            cockpit_app,
            ["audit", "mcp-tail", "--json", "--json-envelope"],
        )
        assert result.exit_code == 0, result.output
        obj = json.loads(result.output)
        assert obj["entries"] == []
        assert obj["count"] == 0

    def test_json_envelope_help_lists_flag(self) -> None:
        """The new ``--json-envelope`` flag must surface in ``--help``."""
        result = CliRunner().invoke(cockpit_app, ["audit", "mcp-tail", "--help"])
        assert result.exit_code == 0
        clean = _strip_ansi(result.output)
        assert "--json-envelope" in clean, f"missing --json-envelope in:\n{clean}"

    def test_default_json_still_line_delimited(self) -> None:
        """Without ``--json-envelope``, ``--json`` keeps the line-delimited shape.

        The Pass 9 line-delimited contract is preserved so existing
        ``head -n 1 | jq`` pipelines keep working unchanged.
        """
        _drive_three_entries()
        result = CliRunner().invoke(cockpit_app, ["audit", "mcp-tail", "--json"])
        assert result.exit_code == 0, result.output
        lines = [ln for ln in result.output.splitlines() if ln.strip()]
        assert len(lines) == 3
        for line in lines:
            obj = json.loads(line)
            # Each line is a bare entry, not an envelope.
            assert "filters" not in obj
            assert "kind" in obj
            assert "agent" in obj


# ---------------------------------------------------------------------------
# Cross-lane sanity (both lanes' flags share the AUDIT-N+25 tag)
# ---------------------------------------------------------------------------


class TestPass11CrossLaneSanity:
    """Sanity tests that confirm both lanes compose cleanly."""

    def test_render_with_runs_and_mcp_audit_composes(self) -> None:
        """``cockpit render --json --runs runs.json`` populates both blocks."""
        import tempfile
        from pathlib import Path

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                [
                    {
                        "run_id": "r1",
                        "state": "active",
                        "lane": "critical",
                        "agent": "cursor",
                        "confidence": 0.92,
                        "elapsed_s": 1.5,
                    },
                ],
                f,
            )
            runs_path = f.name
        try:
            _drive_three_entries()
            result = CliRunner().invoke(
                cockpit_app,
                ["render", "--json", "--runs", runs_path],
            )
            assert result.exit_code == 0, result.output
            payload = json.loads(result.output)
            # Both surfaces compose:
            assert len(payload["runs"]) == 1
            assert payload["runs"][0]["run_id"] == "r1"
            assert isinstance(payload["mcp_audit_stats"], dict)
            assert payload["mcp_audit_stats"]["total_entries"] >= 1
        finally:
            Path(runs_path).unlink(missing_ok=True)
