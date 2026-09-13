"""Tests for the SOTA audit pass 12 cockpit pre-check hardening (AUDIT-N+26).

Pass 12 closes a single genuine, in-scope, in-branch gap surfaced by
the Pass 11 verification sweep:

* ``cockpit pre-check`` (both the single-context ``--json`` path and the
  batch ``--batch --json`` path) was never wired to the MCP audit-trail
  singleton, so operators correlating a deny / allow verdict with the
  upstream MCP tool / resource / gate dispatches had to issue two
  separate CLI invocations (``cockpit pre-check --json`` and
  ``cockpit audit mcp-tail --stats``). Pass 12 mirrors the
  ``cockpit render --include-mcp-audit`` and ``cockpit traffic
  --include-mcp-audit`` toggles on ``pre-check`` so the canonical
  operator UX surfaces agree on vocabulary.

The flag is **default off** on ``pre-check`` (Pass 12 chose the
``cockpit traffic`` default, not the ``cockpit render`` default) so
existing JSON harvesters
(``test_unit_cockpit_sota_json_parity._harvest_decisions`` /
``test_unit_ux_cli_cockpit._harvest_decisions``) stay byte-identical.
Pass 12 only changes the envelope when ``--include-mcp-audit`` is
explicitly supplied:

* Single-context path: the ``PolicyDecision.to_dict()`` envelope gains
  a sibling ``mcp_audit_stats`` key (existing top-level keys preserved
  so ``"verdict" in payload`` still passes).
* Batch path: a trailing ``_pre_check_envelope_v1`` line is emitted
  after the line-delimited decisions, with ``mcp_audit_stats`` and an
  optional ``mcp_audit_error`` key. The discriminator lets the
  canonical ``cockpit replay`` harvesters skip the envelope without
  affecting decision stream semantics.
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
    with audited_budget(AuditEntryKind.TOOL_INVOCATION, "tool_invoke_ms", agent="cursor"):
        pass
    record_resource_read("observe_summary_ms", agent="claude", outcome="ok")
    record_gate_check("gate_check_ms", agent="cursor", outcome="ok")


# ---------------------------------------------------------------------------
# Lane 1 — single-context --json envelope carries mcp_audit_stats
# ---------------------------------------------------------------------------


class TestCockpitPreCheckMcpAuditStatsSingle:
    """Pin the AUDIT-N+26 pass 12 contract for ``cockpit pre-check --json``."""

    def test_default_json_does_not_attach_mcp_audit_stats(self) -> None:
        """Default ``--json`` keeps the historical ``PolicyDecision.to_dict()`` shape.

        Pass 12 chose the ``cockpit traffic`` default (off) for
        ``pre-check`` so existing harvesters
        (``test_unit_cockpit_sota_json_parity._harvest_decisions``)
        stay byte-identical. The envelope is the bare decision dict.
        """
        _drive_three_entries()
        result = CliRunner().invoke(
            cockpit_app,
            [
                "pre-check",
                "--agent",
                "cursor",
                "--lane",
                "standard",
                "--env",
                "development",
                "--confidence",
                "0.95",
                "--json",
            ],
        )
        assert result.exit_code in (0, 3), result.output
        payload = json.loads(result.output)
        # Bare decision shape: all canonical keys present, no envelope
        # metadata.
        assert "verdict" in payload
        assert "reason_code" in payload
        assert "rule_id" in payload
        assert "evaluated_at" in payload
        assert "mcp_audit_stats" not in payload
        assert "mcp_audit_error" not in payload

    def test_include_mcp_audit_json_attaches_stats(self) -> None:
        """``--include-mcp-audit`` populates the ``mcp_audit_stats`` key.

        With three entries driven through the singleton, the key is a
        populated dict (``total_entries >= 1``) and every canonical
        decision key is preserved so the historical
        ``test_unit_ux_cli_cockpit::test_pre_check_json`` assertion
        (``"verdict" in payload``) keeps passing.
        """
        _drive_three_entries()
        result = CliRunner().invoke(
            cockpit_app,
            [
                "pre-check",
                "--agent",
                "cursor",
                "--lane",
                "standard",
                "--env",
                "development",
                "--confidence",
                "0.95",
                "--json",
                "--include-mcp-audit",
            ],
        )
        assert result.exit_code in (0, 3), result.output
        payload = json.loads(result.output)
        # Canonical decision keys preserved.
        assert "verdict" in payload
        assert "reason_code" in payload
        assert "rule_id" in payload
        assert "evaluated_at" in payload
        # New envelope key populated.
        assert "mcp_audit_stats" in payload
        stats = payload["mcp_audit_stats"]
        assert isinstance(stats, dict), f"expected dict, got {type(stats).__name__}: {stats!r}"
        assert stats.get("total_entries", 0) >= 1

    def test_include_mcp_audit_help_lists_flag(self) -> None:
        """``--include-mcp-audit`` / ``--no-mcp-audit`` surface in ``--help``."""
        result = CliRunner().invoke(cockpit_app, ["pre-check", "--help"])
        assert result.exit_code == 0
        clean = _strip_ansi(result.output)
        for needle in ("--include-mcp-audit", "--no-mcp-audit"):
            assert needle in clean, f"missing {needle!r} in:\n{clean}"

    def test_text_mode_is_unchanged(self) -> None:
        """Text mode is unaffected by the audit-trail wiring."""
        _drive_three_entries()
        result = CliRunner().invoke(
            cockpit_app,
            [
                "pre-check",
                "--agent",
                "cursor",
                "--lane",
                "standard",
                "--env",
                "development",
                "--confidence",
                "0.95",
            ],
        )
        assert result.exit_code in (0, 3)
        # Text mode emits the canonical ``verdict=... reason_code=...``
        # line — never the JSON envelope.
        assert "verdict=" in result.output
        assert "reason_code=" in result.output
        # No JSON envelope pollution in text mode.
        assert "mcp_audit_stats" not in result.output

    def test_include_mcp_audit_no_mcp_subsystem_surfaces_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A missing MCP subsystem emits ``mcp_audit_error`` instead of crashing.

        Mirrors the ``cockpit traffic --include-mcp-audit`` envelope
        error-key contract: structured diagnosis, never silent ``null``.
        """

        def _boom() -> None:
            raise ImportError("synthetic mcp subsystem unavailable")

        # Patch the lazy import to raise. We patch
        # ``thegent.mcp.server.mcp_audit_stats`` so the
        # ``from ..mcp.server import mcp_audit_stats`` inside
        # ``_fetch_pre_check_mcp_stats`` resolves to the boom.
        import thegent.mcp.server as mcp_server_mod

        monkeypatch.setattr(mcp_server_mod, "mcp_audit_stats", _boom, raising=False)
        result = CliRunner().invoke(
            cockpit_app,
            [
                "pre-check",
                "--agent",
                "cursor",
                "--lane",
                "standard",
                "--env",
                "development",
                "--confidence",
                "0.95",
                "--json",
                "--include-mcp-audit",
            ],
        )
        assert result.exit_code in (0, 3), result.output
        payload = json.loads(result.output)
        assert "verdict" in payload
        assert "mcp_audit_stats" in payload
        # The fetch helper swallows the exception and surfaces it as an
        # error string so the operator sees a structured diagnosis.
        assert "mcp_audit_error" in payload
        assert "ImportError" in payload["mcp_audit_error"]
        assert "synthetic mcp subsystem unavailable" in payload["mcp_audit_error"]


# ---------------------------------------------------------------------------
# Lane 2 — batch --json trailing envelope with mcp_audit_stats
# ---------------------------------------------------------------------------


class TestCockpitPreCheckMcpAuditStatsBatch:
    """Pin the AUDIT-N+26 pass 12 contract for ``cockpit pre-check --batch --json``."""

    @staticmethod
    def _write_corpus(tmp_path) -> object:
        """Write a 2-context corpus the batch runner accepts."""
        from pathlib import Path

        corpus = Path(tmp_path) / "corpus.json"
        corpus.write_text(
            json.dumps(
                [
                    {
                        "agent": "cursor",
                        "lane": "standard",
                        "confidence": 0.95,
                        "environment": "development",
                    },
                    {
                        "agent": "claude",
                        "lane": "standard",
                        "confidence": 0.80,
                        "environment": "development",
                    },
                ]
            ),
            encoding="utf-8",
        )
        return corpus

    def test_default_batch_json_does_not_attach_envelope(self, tmp_path) -> None:
        """Default ``--batch --json`` keeps the line-delimited decision shape.

        Pass 12 default off keeps
        ``test_unit_cockpit_sota_json_parity._harvest_decisions`` /
        ``test_unit_ux_cli_cockpit._harvest_decisions`` byte-identical:
        only decision-shaped JSON objects are emitted.
        """
        _drive_three_entries()
        corpus = self._write_corpus(tmp_path)
        result = CliRunner().invoke(
            cockpit_app,
            ["pre-check", "--batch", str(corpus), "--json"],
        )
        assert result.exit_code == 0, result.output
        # The summary tail line ("pre-check batch: items=...") is the
        # only non-JSON token in the output.
        decoder = json.JSONDecoder()
        decisions: list[dict] = []
        text = result.output
        idx = 0
        while idx < len(text):
            while idx < len(text) and text[idx].isspace():
                idx += 1
            if idx >= len(text) or text[idx] != "{":
                break
            obj, end = decoder.raw_decode(text[idx:])
            decisions.append(obj)
            idx += end
        # Two decisions, no envelope.
        assert len(decisions) == 2
        for d in decisions:
            assert "verdict" in d
            assert "_pre_check_envelope_v1" not in d

    def test_include_mcp_audit_batch_emits_trailing_envelope(self, tmp_path) -> None:
        """``--batch --json --include-mcp-audit`` emits a trailing envelope line.

        The envelope is tagged with ``_pre_check_envelope_v1`` so the
        canonical ``cockpit replay`` harvesters (which filter on
        ``"verdict"`` membership) can skip it without affecting
        decision stream semantics.
        """
        _drive_three_entries()
        corpus = self._write_corpus(tmp_path)
        result = CliRunner().invoke(
            cockpit_app,
            [
                "pre-check",
                "--batch",
                str(corpus),
                "--json",
                "--include-mcp-audit",
            ],
        )
        assert result.exit_code == 0, result.output
        # The decision stream is still first; the envelope is appended
        # after it. Walk the output and pick out the envelope by its
        # discriminator.
        decoder = json.JSONDecoder()
        decisions: list[dict] = []
        envelopes: list[dict] = []
        text = result.output
        idx = 0
        while idx < len(text):
            while idx < len(text) and text[idx].isspace():
                idx += 1
            if idx >= len(text) or text[idx] != "{":
                break
            obj, end = decoder.raw_decode(text[idx:])
            if obj.get("_pre_check_envelope_v1") is True:
                envelopes.append(obj)
            else:
                decisions.append(obj)
            idx += end
        # Two decisions first, then the envelope.
        assert len(decisions) == 2
        assert len(envelopes) == 1
        env = envelopes[0]
        assert env["mcp_audit_stats"] is not None
        assert isinstance(env["mcp_audit_stats"], dict)
        assert env["mcp_audit_stats"].get("total_entries", 0) >= 1

    def test_include_mcp_audit_batch_harvester_skips_envelope(self, tmp_path) -> None:
        """A canonical harvester that filters on ``verdict`` skips the envelope.

        This pins the contract the
        ``test_unit_cockpit_sota_json_parity._harvest_decisions``
        harvester relies on: ``--include-mcp-audit`` does not break
        snapshot harvesting even though the envelope line shares the
        ``{...}`` prefix.
        """
        _drive_three_entries()
        corpus = self._write_corpus(tmp_path)
        result = CliRunner().invoke(
            cockpit_app,
            [
                "pre-check",
                "--batch",
                str(corpus),
                "--json",
                "--include-mcp-audit",
            ],
        )
        assert result.exit_code == 0, result.output
        decoder = json.JSONDecoder()
        decisions: list[dict] = []
        text = result.output
        idx = 0
        while idx < len(text):
            while idx < len(text) and text[idx].isspace():
                idx += 1
            if idx >= len(text) or text[idx] != "{":
                break
            obj, end = decoder.raw_decode(text[idx:])
            if "verdict" in obj:
                decisions.append(obj)
            idx += end
        # Two decisions, envelope filtered out.
        assert len(decisions) == 2
        for d in decisions:
            assert "_pre_check_envelope_v1" not in d


# ---------------------------------------------------------------------------
# Cross-lane sanity (both lanes share the AUDIT-N+26 tag)
# ---------------------------------------------------------------------------


class TestPass12CrossLaneSanity:
    """Sanity tests confirming the single + batch lanes compose cleanly."""

    def test_default_off_keeps_existing_harvesters_byte_identical(self, tmp_path) -> None:
        """Default ``--batch --json`` output is byte-identical with or without pass 12.

        Pass 12 default-off is the load-bearing invariant for
        ``test_unit_cockpit_sota_json_parity.py`` and
        ``test_unit_ux_cli_cockpit.py::_harvest_decisions``. This
        test pins it by snapshotting the output twice (default vs
        ``--no-mcp-audit``) and confirming the decision stream is
        identical modulo the runtime-dependent ``evaluated_at``
        field (which the canonical replay comparer already excludes;
        see ``_REPLAY_COMPARE_FIELDS`` in
        ``src/thegent/ux/cli_cockpit.py``).
        """
        _drive_three_entries()
        corpus = TestCockpitPreCheckMcpAuditStatsBatch._write_corpus(tmp_path)
        default = CliRunner().invoke(
            cockpit_app,
            ["pre-check", "--batch", str(corpus), "--json"],
        )
        explicit_no = CliRunner().invoke(
            cockpit_app,
            [
                "pre-check",
                "--batch",
                str(corpus),
                "--json",
                "--no-mcp-audit",
            ],
        )
        assert default.exit_code == 0
        assert explicit_no.exit_code == 0

        # Strip the summary tail line ("pre-check batch: items=...")
        # which carries wall-clock-free counters that are stable but
        # order-dependent. Compare the JSON-decision stream only,
        # dropping the runtime-dependent ``evaluated_at`` field
        # (matches the canonical replay comparer's exclusion set).
        def _decisions_only(text: str) -> list[dict]:
            decoder = json.JSONDecoder()
            out: list[dict] = []
            i = 0
            while i < len(text):
                while i < len(text) and text[i].isspace():
                    i += 1
                if i >= len(text) or text[i] != "{":
                    break
                obj, end = decoder.raw_decode(text[i:])
                if "verdict" in obj:
                    obj.pop("evaluated_at", None)
                    out.append(obj)
                i += end
            return out

        assert _decisions_only(default.output) == _decisions_only(explicit_no.output)
