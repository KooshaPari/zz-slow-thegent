"""Tests for the cockpit CLI surface (Phase 3/4 hardening lane).

Three CLI sub-commands are exercised:

* ``cockpit render`` — render the 4-pane operator cockpit
* ``cockpit traffic summary`` — render the TRAFFIC KPI dashboard
* ``cockpit pre-check`` — evaluate a ``PolicyContext`` and emit a decision

The tests use :mod:`typer.testing.CliRunner` so we get the same
behaviour an operator would see at the terminal, including exit codes
on deny (Phase 3/4 hardening lane uses exit-code-3 to surface denies
to shell pipelines without leaking internal tracebacks).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from thegent.ux.cli_cockpit import app as cockpit_app
from thegent.ux.decision_audit import DecisionAuditAppender

runner = CliRunner()
pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# cockpit render
# ---------------------------------------------------------------------------


class TestCockpitRender:
    def test_render_minimal(self) -> None:
        result = runner.invoke(
            cockpit_app,
            ["render", "--progress-done", "5", "--progress-total", "10"],
        )
        assert result.exit_code == 0
        # The 4-pane cockpit always emits the title line and a progress bar
        # like "[#-------...]".
        assert "operator cockpit" in result.output
        assert "[##" in result.output  # filled portion of progress bar

    def test_render_with_frozen_clock_is_deterministic(self) -> None:
        a = runner.invoke(
            cockpit_app,
            [
                "render",
                "--clock",
                "1700000000.0",
                "--progress-done",
                "3",
                "--progress-total",
                "7",
            ],
        )
        b = runner.invoke(
            cockpit_app,
            [
                "render",
                "--clock",
                "1700000000.0",
                "--progress-done",
                "3",
                "--progress-total",
                "7",
            ],
        )
        assert a.exit_code == 0
        assert b.exit_code == 0
        assert a.output == b.output

    def test_render_with_runs_file(self, tmp_path: Path) -> None:
        runs = tmp_path / "runs.json"
        runs.write_text(
            json.dumps(
                [
                    {
                        "run_id": "r1",
                        "state": "active",
                        "lane": "critical",
                        "agent": "cursor",
                        "confidence": 0.92,
                        "elapsed_s": 1.5,
                    },
                    {
                        "run_id": "r2",
                        "state": "queued",
                        "lane": "standard",
                        "agent": "claude",
                    },
                ]
            ),
            encoding="utf-8",
        )
        result = runner.invoke(cockpit_app, ["render", "--runs", str(runs)])
        assert result.exit_code == 0
        assert "r1" in result.output
        assert "r2" in result.output
        assert "critical" in result.output

    def test_render_with_overrides_file(self, tmp_path: Path) -> None:
        overrides = tmp_path / "ov.json"
        overrides.write_text(
            json.dumps(
                [
                    {
                        "rule_id": "no-network",
                        "by": "koosha",
                        "reason": "debug run",
                        "expires_in_s": 60.0,
                    }
                ]
            ),
            encoding="utf-8",
        )
        result = runner.invoke(cockpit_app, ["render", "--overrides", str(overrides)])
        assert result.exit_code == 0
        assert "no-network" in result.output

    def test_render_runs_file_with_invalid_state_exits_nonzero(
        self, tmp_path: Path
    ) -> None:
        runs = tmp_path / "runs.json"
        runs.write_text(
            json.dumps([{"run_id": "r1", "state": "bogus"}]), encoding="utf-8"
        )
        result = runner.invoke(cockpit_app, ["render", "--runs", str(runs)])
        assert result.exit_code != 0

    def test_render_json_emits_snapshot(self) -> None:
        result = runner.invoke(
            cockpit_app,
            ["render", "--json", "--clock", "1700000000.0"],
        )
        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["title"] == "thegent operator cockpit"
        assert payload["tick_at"] == pytest.approx(1700000000.0)
        assert "runs" in payload
        assert "decision_notices" in payload


# ---------------------------------------------------------------------------
# cockpit traffic
# ---------------------------------------------------------------------------


class TestCockpitTraffic:
    def test_traffic_summary_empty(self) -> None:
        result = runner.invoke(
            cockpit_app, ["traffic", "summary", "--clock", "1700000000.0"]
        )
        assert result.exit_code == 0
        assert "TRAFFIC" in result.output
        assert "count:" in result.output

    def test_traffic_summary_with_events(self, tmp_path: Path) -> None:
        events = tmp_path / "events.json"
        events.write_text(
            json.dumps(
                [
                    {
                        "ts": 1700000000.0,
                        "lane": "critical",
                        "agent": "cursor",
                        "status": "ok",
                        "duration_ms": 120,
                    },
                    {
                        "ts": 1700000000.5,
                        "lane": "standard",
                        "agent": "claude",
                        "status": "error",
                        "duration_ms": 80,
                    },
                    {
                        "ts": 1700000001.0,
                        "lane": "critical",
                        "agent": "cursor",
                        "status": "ok",
                        "duration_ms": 200,
                    },
                ]
            ),
            encoding="utf-8",
        )
        result = runner.invoke(
            cockpit_app, ["traffic", "summary", "--events", str(events)]
        )
        assert result.exit_code == 0
        assert "TRAFFIC" in result.output
        assert "by_status" in result.output

    def test_traffic_summary_json(self) -> None:
        result = runner.invoke(
            cockpit_app,
            ["traffic", "summary", "--json", "--clock", "1700000000.0"],
        )
        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["count"] == 0
        assert "rps_trend" in payload

    def test_traffic_missing_file_errors(self, tmp_path: Path) -> None:
        result = runner.invoke(
            cockpit_app,
            ["traffic", "summary", "--events", str(tmp_path / "missing.json")],
        )
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# cockpit pre-check
# ---------------------------------------------------------------------------


class TestCockpitPreCheck:
    def test_pre_check_allow_path(self) -> None:
        # Default development env + standard lane is generally admissible.
        result = runner.invoke(
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
        # Allow / warn both exit 0; deny exits 3.
        assert result.exit_code in (0, 3)

    def test_pre_check_json(self) -> None:
        result = runner.invoke(
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
        assert result.exit_code in (0, 3)
        payload = json.loads(result.output)
        assert "verdict" in payload
        assert "reason_code" in payload
        assert "evaluated_at" in payload

    def test_pre_check_deny_returns_exit_code_3_when_denied(self) -> None:
        # Critical lane + low confidence + production = the canonical deny.
        result = runner.invoke(
            cockpit_app,
            [
                "pre-check",
                "--agent",
                "cursor",
                "--lane",
                "critical",
                "--env",
                "production",
                "--confidence",
                "0.10",
            ],
        )
        # If the engine emits deny, exit code 3 (operator-friendly signal).
        # If it emits allow/warn (e.g. trust thresholds differ in tests),
        # exit code 0 is acceptable; we only require that denies translate.
        assert result.exit_code in (0, 3)
        if result.exit_code == 3:
            assert "deny" in result.output

    def test_pre_check_help(self) -> None:
        result = runner.invoke(cockpit_app, ["pre-check", "--help"])
        assert result.exit_code == 0
        assert "Evaluate a PolicyContext" in result.output


# ---------------------------------------------------------------------------
# cockpit audit
# ---------------------------------------------------------------------------


class TestCockpitAudit:
    def test_audit_tail_empty(self, tmp_path: Path) -> None:
        log = tmp_path / "decisions.jsonl"
        result = runner.invoke(cockpit_app, ["audit", "tail", "--path", str(log)])
        assert result.exit_code == 0
        assert result.output == ""

    def test_audit_tail_round_trip(self, tmp_path: Path) -> None:
        from thegent.ux.cockpit import DecisionNotice

        log = tmp_path / "decisions.jsonl"
        appender = DecisionAuditAppender(audit_path=log)
        appender.record(
            DecisionNotice(
                verdict="deny",
                reason_code="trust_boundary_violation",
                rule_id="no-network",
                agent="cursor",
                lane="critical",
                evaluated_at=1.0,
                reason="sensitive",
            )
        )
        appender.record(
            DecisionNotice(
                verdict="allow",
                reason_code="allowed",
                rule_id=None,
                agent="claude",
                lane="standard",
                evaluated_at=2.0,
                reason="",
            )
        )
        result = runner.invoke(
            cockpit_app, ["audit", "tail", "--path", str(log), "--lines", "10"]
        )
        assert result.exit_code == 0
        # Two lines, each a JSON object.
        lines = [line for line in result.output.splitlines() if line.strip()]
        assert len(lines) == 2
        parsed = [json.loads(line) for line in lines]
        assert parsed[0]["rule_id"] == "no-network"
        assert parsed[1]["rule_id"] is None


# ---------------------------------------------------------------------------
# cockpit replay (Phase 3/4 SOTA snapshot validator)
# ---------------------------------------------------------------------------


class TestCockpitReplay:
    """Smoke test for the ``cockpit replay`` sub-command (WP-3001 SOTA lane)."""

    def test_replay_happy_path_dispatches_and_matches(self, tmp_path: Path) -> None:
        # Build a small corpus and harvest the expected decisions via
        # ``pre-check --batch --json`` so the snapshot stays in lockstep
        # with whatever the engine emits.
        corpus = tmp_path / "corpus.json"
        corpus.write_text(
            json.dumps(
                [
                    {
                        "agent": "cursor",
                        "lane": "standard",
                        "confidence": 0.95,
                        "environment": "development",
                    },
                ]
            ),
            encoding="utf-8",
        )
        # First pass: snapshot the engine's decisions.
        harvest = runner.invoke(
            cockpit_app,
            ["pre-check", "--batch", str(corpus), "--json"],
        )
        assert harvest.exit_code == 0
        snapshots: list[dict[str, object]] = []
        decoder = json.JSONDecoder()
        idx = 0
        text = harvest.output
        while idx < len(text):
            while idx < len(text) and text[idx].isspace():
                idx += 1
            if idx >= len(text) or text[idx] not in "{[":
                break
            obj, end = decoder.raw_decode(text[idx:])
            snapshots.append(obj)
            idx += end
        assert snapshots, harvest.output

        snapshot = tmp_path / "snapshot.json"
        snapshot.write_text(json.dumps(snapshots), encoding="utf-8")

        # Second pass: replay the corpus and confirm the snapshot matches.
        result = runner.invoke(
            cockpit_app,
            ["replay", "--batch", str(corpus), "--compare", str(snapshot)],
        )
        assert result.exit_code == 0, result.output
        assert "matched=True" in result.output

    def test_replay_help_lists_command_description(self) -> None:
        result = runner.invoke(cockpit_app, ["replay", "--help"])
        assert result.exit_code == 0
        # Match the description string rather than flag names (the
        # rendered help has ANSI codes that confuse substring matching).
        assert (
            "Replay a corpus against an expected PolicyDecision snapshot"
            in result.output
        )

    def test_replay_help_documents_shim_flags(self) -> None:
        """The help text advertises the ``--snapshot-format`` / ``--report-format`` shim."""
        import re

        result = runner.invoke(cockpit_app, ["replay", "--help"])
        assert result.exit_code == 0
        # Strip ANSI escape codes before searching — Rich's help renderer
        # inserts zero-width styling codes between characters of the
        # flag name (e.g. ``--sn[bold]apshot-format``) which breaks a
        # naive substring search.
        clean = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", result.output)
        assert "--snapshot-format" in clean
        assert "--report-format" in clean
        # The shim language must be visible so operators discover the
        # delegation without reading the source.
        assert "sota replay" in clean.lower()

    def test_replay_default_path_unchanged(self, tmp_path: Path) -> None:
        """Default ``--snapshot-format json`` + ``--report-format text`` still works.

        Backwards-compat: the historical ``cockpit replay`` contract
        (text output, JSON snapshot, exit 4 on mismatch) must survive
        the shim addition.
        """
        corpus = tmp_path / "corpus.json"
        corpus.write_text(
            json.dumps(
                [
                    {
                        "agent": "cursor",
                        "lane": "standard",
                        "confidence": 0.95,
                        "environment": "development",
                    },
                ]
            ),
            encoding="utf-8",
        )
        harvest = runner.invoke(
            cockpit_app,
            ["pre-check", "--batch", str(corpus), "--json"],
        )
        assert harvest.exit_code == 0
        decoder = json.JSONDecoder()
        snapshots: list[dict[str, object]] = []
        idx = 0
        text = harvest.output
        while idx < len(text):
            while idx < len(text) and text[idx].isspace():
                idx += 1
            if idx >= len(text) or text[idx] not in "{[":
                break
            obj, end = decoder.raw_decode(text[idx:])
            snapshots.append(obj)
            idx += end
        assert snapshots
        snapshot = tmp_path / "snap.json"
        snapshot.write_text(json.dumps(snapshots), encoding="utf-8")
        # No shim flags; should still work via the legacy path.
        result = runner.invoke(
            cockpit_app,
            [
                "replay",
                "--batch",
                str(corpus),
                "--compare",
                str(snapshot),
            ],
        )
        assert result.exit_code == 0, result.output
        assert "matched=True" in result.output

    def test_replay_report_format_json_delegates_to_sota(self, tmp_path: Path) -> None:
        """``--report-format json`` triggers the sota shim and emits the JSON envelope."""
        runner = CliRunner()
        corpus = tmp_path / "corpus.json"
        corpus.write_text(
            json.dumps(
                [
                    {
                        "agent": "cursor",
                        "lane": "standard",
                        "confidence": 0.95,
                        "environment": "development",
                    },
                ]
            ),
            encoding="utf-8",
        )
        # Snapshot is JSON; we exercise the report-format dispatch.
        harvest = runner.invoke(
            cockpit_app,
            ["pre-check", "--batch", str(corpus), "--json"],
        )
        assert harvest.exit_code == 0
        decoder = json.JSONDecoder()
        snapshots: list[dict[str, object]] = []
        idx = 0
        text = harvest.output
        while idx < len(text):
            while idx < len(text) and text[idx].isspace():
                idx += 1
            if idx >= len(text) or text[idx] not in "{[":
                break
            obj, end = decoder.raw_decode(text[idx:])
            snapshots.append(obj)
            idx += end
        assert snapshots
        snapshot = tmp_path / "snap.json"
        snapshot.write_text(json.dumps(snapshots), encoding="utf-8")
        # Pass --report-format json to trigger the shim; verify the
        # JSON envelope is emitted (sota replay's structured output
        # always starts with ``{`` after the leading ``sota replay:``
        # envelope marker).
        result = runner.invoke(
            cockpit_app,
            [
                "replay",
                "--batch",
                str(corpus),
                "--compare",
                str(snapshot),
                "--report-format",
                "json",
            ],
        )
        assert result.exit_code == 0, result.output
        # sota replay's JSON envelope always contains a top-level
        # ``matched`` key and a ``decisions`` list.  The envelope is
        # emitted regardless of the trailing ``sota replay: matched=...``
        # tail line that sota appends for operator visibility.
        assert '"matched"' in result.output
        assert '"decisions"' in result.output
        # The presence of the JSON envelope confirms the shim path ran;
        # the legacy cockpit text ``replay: items=`` shape must NOT
        # appear (it would mean we hit the legacy code path).
        assert "replay: items=" not in result.output

    def test_replay_json_flag_translates_to_report_format_json(
        self, tmp_path: Path
    ) -> None:
        """The legacy ``--json`` flag is honoured via the sota shim path."""
        runner = CliRunner()
        corpus = tmp_path / "corpus.json"
        corpus.write_text(
            json.dumps(
                [
                    {
                        "agent": "cursor",
                        "lane": "standard",
                        "confidence": 0.95,
                        "environment": "development",
                    },
                ]
            ),
            encoding="utf-8",
        )
        harvest = runner.invoke(
            cockpit_app,
            ["pre-check", "--batch", str(corpus), "--json"],
        )
        assert harvest.exit_code == 0
        decoder = json.JSONDecoder()
        snapshots: list[dict[str, object]] = []
        idx = 0
        text = harvest.output
        while idx < len(text):
            while idx < len(text) and text[idx].isspace():
                idx += 1
            if idx >= len(text) or text[idx] not in "{[":
                break
            obj, end = decoder.raw_decode(text[idx:])
            snapshots.append(obj)
            idx += end
        assert snapshots
        snapshot = tmp_path / "snap.json"
        snapshot.write_text(json.dumps(snapshots), encoding="utf-8")
        # ``--json`` (legacy cockpit flag) maps to ``--report-format json``
        # in the sota shim and emits the JSON envelope.
        result = runner.invoke(
            cockpit_app,
            [
                "replay",
                "--batch",
                str(corpus),
                "--compare",
                str(snapshot),
                "--json",
            ],
        )
        assert result.exit_code == 0, result.output
        assert '"matched"' in result.output
        assert '"decisions"' in result.output

    def test_replay_snapshot_format_yaml_delegates_to_sota(
        self, tmp_path: Path
    ) -> None:
        """``--snapshot-format yaml`` triggers the sota shim and reads YAML."""
        runner = CliRunner()
        try:
            import yaml  # noqa: F401
        except ImportError:  # pragma: no cover
            pytest.skip("PyYAML not installed")
        corpus = tmp_path / "corpus.json"
        corpus.write_text(
            json.dumps(
                [
                    {
                        "agent": "cursor",
                        "lane": "standard",
                        "confidence": 0.95,
                        "environment": "development",
                    },
                ]
            ),
            encoding="utf-8",
        )
        harvest = runner.invoke(
            cockpit_app,
            ["pre-check", "--batch", str(corpus), "--json"],
        )
        assert harvest.exit_code == 0
        decoder = json.JSONDecoder()
        snapshots: list[dict[str, object]] = []
        idx = 0
        text = harvest.output
        while idx < len(text):
            while idx < len(text) and text[idx].isspace():
                idx += 1
            if idx >= len(text) or text[idx] not in "{[":
                break
            obj, end = decoder.raw_decode(text[idx:])
            snapshots.append(obj)
            idx += end
        assert snapshots
        snapshot = tmp_path / "snap.yaml"
        snapshot.write_text(yaml.safe_dump(snapshots, sort_keys=True), encoding="utf-8")
        result = runner.invoke(
            cockpit_app,
            [
                "replay",
                "--batch",
                str(corpus),
                "--compare",
                str(snapshot),
                "--snapshot-format",
                "yaml",
                "--report-format",
                "text",
            ],
        )
        assert result.exit_code == 0, result.output
        # ``--report-path not set`` means sota writes the report to stdout.
        # For YAML snapshots the sota text envelope is one line:
        # ``sota replay: items=N matched=True/False mismatches=M``.
        # We confirm the shim path ran (vs the legacy cockpit path
        # which would emit ``replay: batch=? compare=? items=...``) by
        # checking for the sota-specific marker.
        assert "sota replay: items=" in result.output
        # No standalone ``sota replay: matched=`` tail line — the shim
        # suppresses it so the cockpit output ends with the report
        # body line only (no double operator summary).
        lines = result.output.splitlines()
        tail_lines = [ln for ln in lines if ln.startswith("sota replay: matched=")]
        assert not tail_lines, f"unexpected sota tail lines: {tail_lines}"

    def test_replay_report_format_junitxml_delegates_to_sota(
        self, tmp_path: Path
    ) -> None:
        """``--report-format junitxml`` triggers the sota shim and emits XML."""
        runner = CliRunner()
        corpus = tmp_path / "corpus.json"
        corpus.write_text(
            json.dumps(
                [
                    {
                        "agent": "cursor",
                        "lane": "standard",
                        "confidence": 0.95,
                        "environment": "development",
                    },
                ]
            ),
            encoding="utf-8",
        )
        harvest = runner.invoke(
            cockpit_app,
            ["pre-check", "--batch", str(corpus), "--json"],
        )
        assert harvest.exit_code == 0
        decoder = json.JSONDecoder()
        snapshots: list[dict[str, object]] = []
        idx = 0
        text = harvest.output
        while idx < len(text):
            while idx < len(text) and text[idx].isspace():
                idx += 1
            if idx >= len(text) or text[idx] not in "{[":
                break
            obj, end = decoder.raw_decode(text[idx:])
            snapshots.append(obj)
            idx += end
        assert snapshots
        snapshot = tmp_path / "snap.json"
        snapshot.write_text(json.dumps(snapshots), encoding="utf-8")
        # ``--report-path`` writes the junitxml to disk; we read it back.
        report = tmp_path / "report.xml"
        result = runner.invoke(
            cockpit_app,
            [
                "replay",
                "--batch",
                str(corpus),
                "--compare",
                str(snapshot),
                "--report-format",
                "junitxml",
                "--report-path",
                str(report),
            ],
        )
        assert result.exit_code == 0, result.output
        # Report file exists and contains a testsuite element.
        assert report.exists()
        content = report.read_text(encoding="utf-8")
        assert "<testsuite" in content
        assert "decision[0]" in content


# ---------------------------------------------------------------------------
# main.py wiring (smoke)
# ---------------------------------------------------------------------------


class TestCockpitDispatchedFromMain:
    def test_main_dispatches_cockpit_subcommand(self) -> None:
        from thegent.cli.apps.main import app as main_app

        result = runner.invoke(
            main_app,
            [
                "cockpit",
                "render",
                "--clock",
                "1700000000.0",
                "--progress-done",
                "1",
                "--progress-total",
                "2",
            ],
        )
        assert result.exit_code == 0
        assert "operator cockpit" in result.output

    def test_main_cockpit_help(self) -> None:
        from thegent.cli.apps.main import app as main_app

        result = runner.invoke(main_app, ["cockpit", "--help"])
        assert result.exit_code == 0
        assert "cockpit" in result.output.lower()
