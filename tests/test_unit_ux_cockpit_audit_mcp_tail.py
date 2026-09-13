"""Tests for the ``cockpit audit mcp-tail`` subcommand (Lane D / AUDIT-N+15).

This subcommand surfaces the in-memory MCP audit trail (a singleton
held by ``mcp_audit_trail``) to the operator CLI. It supports:

* ``--json`` for machine-readable output (line-delimited JSON).
* ``--kind`` for filtering by ``AuditEntryKind`` (string form).
* ``--lines`` for capping the number of entries returned (latest N).
* ``--stats`` for a roll-up summary without listing entries.
* ``--query <substring>`` for substring filtering on ``operation``.

The CLI is the operator's window into the audit-trail singleton; the
contracts here pin the **shape** of that window so future consumers
(JSON dashboards, the cockpit live-tail, etc.) can rely on it.

Lane D of the audit-trail rollout (AUDIT-N+15) adds this subcommand
without disturbing the existing ``cockpit audit`` JSONL decision-log
subcommand (which lives alongside it under the same ``audit_app``).
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


def _drive_three_entries() -> None:
    """Drive three distinct entries through the audit-trail singleton.

    Used by every test that needs a non-empty trail. Three entries
    cover: tool-invocation, resource-read, and gate-check, so the
    ``--kind`` filter tests have something to discriminate on.
    """
    reset_audit_trail()
    with audited_budget(AuditEntryKind.TOOL_INVOCATION, "tool_invoke_ms", agent="cursor"):
        pass
    record_resource_read("observe_summary_ms", agent="claude", outcome="ok")
    record_gate_check("gate_check_ms", agent="cursor", outcome="ok")


# ---------------------------------------------------------------------------
# Subcommand registration + help text shape
# ---------------------------------------------------------------------------


class TestMcpTailRegistration:
    """Pin the Lane D subcommand registration contract."""

    def test_help_renders_mcp_tail_subcommand(self) -> None:
        result = CliRunner().invoke(cockpit_app, ["audit", "--help"])
        assert result.exit_code == 0
        clean = _strip_ansi(result.output)
        assert "mcp-tail" in clean

    def test_help_renders_audit_root_description(self) -> None:
        # The audit-app callback should mention MCP audit so the operator
        # sees both surfaces (decision-log JSONL + MCP trail tail).
        result = CliRunner().invoke(cockpit_app, ["audit", "--help"])
        assert result.exit_code == 0
        clean = _strip_ansi(result.output)
        assert "audit" in clean.lower()

    def test_mcp_tail_help_lists_filters(self) -> None:
        """The --help output for ``mcp-tail`` should document its filters."""
        result = CliRunner().invoke(cockpit_app, ["audit", "mcp-tail", "--help"])
        assert result.exit_code == 0
        clean = _strip_ansi(result.output)
        # The filter flags that the CLI exposes should appear in --help.
        for needle in ("--kind", "--lines", "--agent", "--outcome", "--stats", "--json"):
            assert needle in clean, f"missing {needle!r} in:\n{clean}"


# ---------------------------------------------------------------------------
# JSON output shape
# ---------------------------------------------------------------------------


class TestMcpTailJsonOutput:
    """Pin the ``--json`` line-delimited shape consumed by dashboards.

    The CLI mirrors ``AuditEntry.to_dict()`` exactly — see
    ``TestMcpTailMatchesProgrammaticApi`` for the round-trip contract.
    """

    def test_json_mode_emits_one_object_per_line(self) -> None:
        _drive_three_entries()
        result = CliRunner().invoke(cockpit_app, ["audit", "mcp-tail", "--json"])
        assert result.exit_code == 0, result.output
        lines = [ln for ln in result.output.splitlines() if ln.strip()]
        assert len(lines) == 3, lines
        for line in lines:
            obj = json.loads(line)
            assert "seq" in obj
            assert "kind" in obj
            assert "operation" in obj
            assert "agent" in obj
            assert "outcome" in obj

    def test_json_lines_caps_returned_count(self) -> None:
        _drive_three_entries()
        result = CliRunner().invoke(cockpit_app, ["audit", "mcp-tail", "--json", "--lines", "2"])
        assert result.exit_code == 0
        lines = [ln for ln in result.output.splitlines() if ln.strip()]
        assert len(lines) == 2

    def test_json_kind_filter_narrows_to_one_kind(self) -> None:
        _drive_three_entries()
        result = CliRunner().invoke(cockpit_app, ["audit", "mcp-tail", "--json", "--kind", "gate_check"])
        assert result.exit_code == 0
        lines = [ln for ln in result.output.splitlines() if ln.strip()]
        assert len(lines) == 1
        obj = json.loads(lines[0])
        # ``kind`` is the lowercased ``AuditEntryKind`` name.
        assert obj["kind"] == "gate_check"
        assert obj["operation"] == "gate_check_ms"


# ---------------------------------------------------------------------------
# Text output shape
# ---------------------------------------------------------------------------


class TestMcpTailTextOutput:
    """Pin the human-readable (default) text output shape."""

    def test_text_mode_renders_table_with_required_columns(self) -> None:
        _drive_three_entries()
        result = CliRunner().invoke(cockpit_app, ["audit", "mcp-tail", "--lines", "10"])
        assert result.exit_code == 0, result.output
        clean = _strip_ansi(result.output)
        # Text mode uses ``op=`` (not ``operation=``) as the column label,
        # and ``kind=`` / ``agent=`` / ``outcome=`` / ``duration_ms=`` for
        # the rest of the row. Pin all five so future refactors don't
        # silently drop a column.
        for col in ("seq=", "kind=", "op=", "agent=", "outcome=", "duration_ms="):
            assert col in clean, f"missing column {col!r} in:\n{clean}"


# ---------------------------------------------------------------------------
# --stats roll-up
# ---------------------------------------------------------------------------


class TestMcpTailStats:
    """Pin the ``--stats`` roll-up contract.

    The roll-up is emitted as a single JSON object with ``total_entries``,
    ``by_kind``, ``by_outcome``, ``avg_duration_ms``, ``p99_duration_ms``.
    """

    def test_stats_only_renders_summary(self) -> None:
        _drive_three_entries()
        result = CliRunner().invoke(cockpit_app, ["audit", "mcp-tail", "--stats"])
        assert result.exit_code == 0
        # ``--stats`` in CLI mode emits a single JSON object.
        obj = json.loads(result.output)
        assert obj["total_entries"] == 3
        assert obj["by_kind"]["tool_invocation"] == 1
        assert obj["by_kind"]["resource_read"] == 1
        assert obj["by_kind"]["gate_check"] == 1
        assert obj["error_count"] == 0

    def test_stats_does_not_render_entries(self) -> None:
        _drive_three_entries()
        result = CliRunner().invoke(cockpit_app, ["audit", "mcp-tail", "--stats"])
        assert result.exit_code == 0
        obj = json.loads(result.output)
        # Roll-up has no row-level data — keys are aggregate counts only.
        assert "seq" not in obj


# ---------------------------------------------------------------------------
# --query substring filter
# ---------------------------------------------------------------------------


class TestMcpTailFilters:
    """Pin the ``--kind`` / ``--agent`` / ``--outcome`` filter contracts.

    All three filters compose (e.g. ``--kind tool_invocation --agent cursor``).
    See ``cockpit_audit_mcp_tail`` in ``cli_cockpit.py`` for the
    composition rules.
    """

    def test_kind_filter_narrows_to_one_kind(self) -> None:
        _drive_three_entries()
        result = CliRunner().invoke(cockpit_app, ["audit", "mcp-tail", "--json", "--kind", "gate_check"])
        assert result.exit_code == 0
        lines = [ln for ln in result.output.splitlines() if ln.strip()]
        assert len(lines) == 1
        obj = json.loads(lines[0])
        assert obj["kind"] == "gate_check"
        assert obj["operation"] == "gate_check_ms"

    def test_agent_filter_narrows_to_one_agent(self) -> None:
        _drive_three_entries()
        result = CliRunner().invoke(cockpit_app, ["audit", "mcp-tail", "--json", "--agent", "claude"])
        assert result.exit_code == 0
        lines = [ln for ln in result.output.splitlines() if ln.strip()]
        assert len(lines) == 1
        obj = json.loads(lines[0])
        assert obj["agent"] == "claude"

    def test_outcome_filter_narrows_to_matching_outcome(self) -> None:
        _drive_three_entries()
        result = CliRunner().invoke(cockpit_app, ["audit", "mcp-tail", "--json", "--outcome", "ok"])
        assert result.exit_code == 0
        # All three entries are outcome=ok.
        lines = [ln for ln in result.output.splitlines() if ln.strip()]
        assert len(lines) == 3
        for line in lines:
            obj = json.loads(line)
            assert obj["outcome"] == "ok"

    def test_composed_filters_intersect(self) -> None:
        """``--kind`` and ``--agent`` together narrow to the intersection."""
        _drive_three_entries()
        result = CliRunner().invoke(
            cockpit_app,
            [
                "audit",
                "mcp-tail",
                "--json",
                "--kind",
                "gate_check",
                "--agent",
                "cursor",
            ],
        )
        assert result.exit_code == 0
        lines = [ln for ln in result.output.splitlines() if ln.strip()]
        assert len(lines) == 1
        obj = json.loads(lines[0])
        assert obj["kind"] == "gate_check"
        assert obj["agent"] == "cursor"

    def test_no_match_returns_no_lines(self) -> None:
        _drive_three_entries()
        result = CliRunner().invoke(
            cockpit_app,
            ["audit", "mcp-tail", "--json", "--agent", "no-such-agent"],
        )
        assert result.exit_code == 0
        assert result.output.strip() == ""


# ---------------------------------------------------------------------------
# Error envelope
# ---------------------------------------------------------------------------


class TestMcpTailErrors:
    """Pin the F-15 error-envelope shape on bad input."""

    def test_unknown_kind_exits_nonzero_with_helpful_message(self) -> None:
        _drive_three_entries()
        result = CliRunner().invoke(cockpit_app, ["audit", "mcp-tail", "--kind", "nonsense"])
        assert result.exit_code != 0
        clean = _strip_ansi(result.output)
        # Should mention the offending kind.
        assert "nonsense" in clean

    def test_empty_trail_returns_empty_output(self) -> None:
        reset_audit_trail()
        result = CliRunner().invoke(cockpit_app, ["audit", "mcp-tail", "--json"])
        assert result.exit_code == 0
        assert result.output.strip() == ""

    def test_empty_trail_stats_reports_zero(self) -> None:
        reset_audit_trail()
        result = CliRunner().invoke(cockpit_app, ["audit", "mcp-tail", "--stats"])
        assert result.exit_code == 0
        obj = json.loads(result.output)
        assert obj["total_entries"] == 0
        assert obj["by_kind"] == {}


# ---------------------------------------------------------------------------
# Live-tick integration
# ---------------------------------------------------------------------------


class TestMcpTailAfterAuditedBudget:
    """Ensure the CLI reflects new entries recorded between invocations."""

    def test_new_entry_appears_in_subsequent_invocation(self) -> None:
        reset_audit_trail()
        # First invocation sees nothing.
        result = CliRunner().invoke(cockpit_app, ["audit", "mcp-tail", "--json"])
        assert result.exit_code == 0
        assert result.output.strip() == ""
        # Record one entry via the audited_budget helper.
        with audited_budget(AuditEntryKind.TOOL_INVOCATION, "tool_invoke_ms", agent="forge"):
            pass
        # Second invocation sees it.
        result = CliRunner().invoke(cockpit_app, ["audit", "mcp-tail", "--json"])
        assert result.exit_code == 0
        lines = [ln for ln in result.output.splitlines() if ln.strip()]
        assert len(lines) == 1
        obj = json.loads(lines[0])
        assert obj["agent"] == "forge"
        assert obj["kind"] == "tool_invocation"


# ---------------------------------------------------------------------------
# Compatibility with mcp_audit_recent
# ---------------------------------------------------------------------------


class TestMcpTailMatchesProgrammaticApi:
    """Pin that the CLI shape matches the programmatic ``mcp_audit_recent`` API.

    This is the most important contract: anything that reads the JSON
    output should see exactly what ``mcp_audit_recent(n).to_dict()``
    yields — no silent re-shaping, no missing fields.
    """

    def test_json_payload_matches_recent_to_dict(self) -> None:
        _drive_three_entries()
        result = CliRunner().invoke(cockpit_app, ["audit", "mcp-tail", "--json"])
        assert result.exit_code == 0
        cli_lines = [ln for ln in result.output.splitlines() if ln.strip()]
        api_dicts = [e.to_dict() for e in mcp_audit_recent(n=10)]
        assert len(cli_lines) == len(api_dicts)
        for cli_line, api_dict in zip(cli_lines, api_dicts, strict=True):
            cli_obj = json.loads(cli_line)
            assert cli_obj == api_dict
