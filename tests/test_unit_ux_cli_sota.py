"""Unit tests for the SOTA replay CLI (Phase 3/4 hardening lane, third item).

Covers:

* Snapshot-format dispatch (json / yaml / toml).
* Report-format dispatch (text / json / junitxml).
* Exit-code convention (0 match / 4 mismatch / 1 bad input).
* junitxml structure: ``<testsuite tests=... failures=...>`` with one
  ``<testcase>`` per corpus entry and a ``<failure>`` element per
  mismatch.
* Suite-name customisation for multi-suite CI ingestion.
* ``--report-path`` writes the report to disk and emits an ack on stdout.
"""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET  # noqa: S314  (test-only, fixture round-trip)
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from thegent.ux.cli_sota import app

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _harvest_pre_check_decisions(runner: CliRunner, corpus: Path) -> list[dict]:
    """Run ``cockpit pre-check --batch`` once and return the produced decisions.

    Mirrors the helper in ``test_unit_ux_cockpit_audit_pane_batch.py``
    so the snapshot we feed into ``sota replay`` is what the engine
    actually produced (the only stable ground truth for replay tests).

    ``cockpit pre-check --batch --json`` emits one pretty-printed JSON
    object per decision followed by a trailing human-readable summary
    line.  We walk forward one object at a time via
    :meth:`json.JSONDecoder.raw_decode` so the per-object indentation
    doesn't trip up a line-by-line scan.
    """
    from thegent.ux.cli_cockpit import app as cockpit_app

    result = runner.invoke(
        cockpit_app,
        [
            "pre-check",
            "--batch",
            str(corpus),
            "--json",
        ],
    )
    assert result.exit_code in (0, 3), result.output  # 3 == at least one deny
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
    assert decisions, f"no decisions harvested from pre-check output: {text!r}"
    return decisions


# ---------------------------------------------------------------------------
# Snapshot-format dispatch
# ---------------------------------------------------------------------------


class TestSotaReplaySnapshotFormats:
    """``--snapshot-format`` selects the loader for ``--compare``."""

    def test_json_snapshot_format_match_exits_zero(self, tmp_path: Path) -> None:
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
            )
        )
        expected = _harvest_pre_check_decisions(runner, corpus)
        snapshot = tmp_path / "snap.json"
        snapshot.write_text(json.dumps(expected))
        result = runner.invoke(
            app,
            [
                "replay",
                "--batch",
                str(corpus),
                "--compare",
                str(snapshot),
                "--snapshot-format",
                "json",
            ],
        )
        assert result.exit_code == 0, result.output
        assert "matched=True" in result.output

    def test_yaml_snapshot_format_match_exits_zero(self, tmp_path: Path) -> None:
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
            )
        )
        expected = _harvest_pre_check_decisions(runner, corpus)
        snapshot = tmp_path / "snap.yaml"
        snapshot.write_text(yaml.safe_dump(expected, sort_keys=True))
        result = runner.invoke(
            app,
            [
                "replay",
                "--batch",
                str(corpus),
                "--compare",
                str(snapshot),
                "--snapshot-format",
                "yaml",
            ],
        )
        assert result.exit_code == 0, result.output
        assert "matched=True" in result.output

    def test_yaml_accepts_yml_alias(self, tmp_path: Path) -> None:
        """``.yml`` extension and ``yaml`` format are interchangeable."""
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
            )
        )
        expected = _harvest_pre_check_decisions(runner, corpus)
        snapshot = tmp_path / "snap.yml"
        snapshot.write_text(yaml.safe_dump(expected, sort_keys=True))
        result = runner.invoke(
            app,
            [
                "replay",
                "--batch",
                str(corpus),
                "--compare",
                str(snapshot),
                "--snapshot-format",
                "yml",
            ],
        )
        assert result.exit_code == 0, result.output

    def test_toml_snapshot_format_match_exits_zero(self, tmp_path: Path) -> None:
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
            )
        )
        expected = _harvest_pre_check_decisions(runner, corpus)
        # TOML top level is always a table; use the ``decisions`` key form.
        snapshot = tmp_path / "snap.toml"
        snapshot.write_text("decisions = " + json.dumps(expected).replace('"', '\\"').replace("'", "\\'"))
        # The above escape is brittle — write TOML via tomllib instead:
        import tomllib  # noqa: F401  (presence check)

        # Use a simpler explicit form: build the file by hand.
        toml_body = "decisions = [\n"
        for d in expected:
            toml_body += "  { verdict = " + json.dumps(d["verdict"])
            toml_body += ", reason = " + json.dumps(d["reason"])
            toml_body += ", reason_code = " + json.dumps(d["reason_code"])
            toml_body += ", rule_id = " + json.dumps(d.get("rule_id") or "")
            toml_body += ", override_applied = " + ("true" if d["override_applied"] else "false")
            toml_body += " },\n"
        toml_body += "]\n"
        snapshot.write_text(toml_body)
        result = runner.invoke(
            app,
            [
                "replay",
                "--batch",
                str(corpus),
                "--compare",
                str(snapshot),
                "--snapshot-format",
                "toml",
            ],
        )
        # Note: TOML re-emit of the snapshot may differ in whitespace,
        # but the field-by-field compare in ``_compare_decision``
        # tolerates reason whitespace, so a match should still hold.
        assert result.exit_code == 0, result.output

    def test_unknown_snapshot_format_exits_one(self, tmp_path: Path) -> None:
        runner = CliRunner()
        corpus = tmp_path / "corpus.json"
        corpus.write_text(json.dumps([{"agent": "a", "lane": "standard"}]))
        snapshot = tmp_path / "snap.json"
        snapshot.write_text("[]")
        result = runner.invoke(
            app,
            [
                "replay",
                "--batch",
                str(corpus),
                "--compare",
                str(snapshot),
                "--snapshot-format",
                "xml",
            ],
        )
        assert result.exit_code == 1, result.output
        assert "snapshot-format" in result.output


# ---------------------------------------------------------------------------
# Report-format dispatch
# ---------------------------------------------------------------------------


class TestSotaReplayReportFormats:
    """``--report-format`` selects the report renderer."""

    def test_json_report_emits_envelope(self, tmp_path: Path) -> None:
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
            )
        )
        expected = _harvest_pre_check_decisions(runner, corpus)
        snapshot = tmp_path / "snap.json"
        snapshot.write_text(json.dumps(expected))
        result = runner.invoke(
            app,
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
        # The text envelope line is always printed on stdout.
        assert "matched=True" in result.output
        # JSON envelope is the first JSON object on stdout (pretty-printed).
        decoder = json.JSONDecoder()
        envelope = None
        idx = 0
        text = result.output
        while idx < len(text):
            while idx < len(text) and text[idx].isspace():
                idx += 1
            if idx >= len(text) or text[idx] != "{":
                break
            obj, _end = decoder.raw_decode(text[idx:])
            envelope = obj
            break
        assert envelope is not None, result.output
        assert envelope["matched"] is True
        assert envelope["items"] == 1
        assert envelope["mismatches"] == []

    def test_junitxml_report_well_formed_on_match(self, tmp_path: Path) -> None:
        """junitxml output is valid XML with the expected structure on match."""
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
                    {
                        "agent": "cursor",
                        "lane": "standard",
                        "confidence": 0.9,
                        "environment": "development",
                    },
                ]
            )
        )
        expected = _harvest_pre_check_decisions(runner, corpus)
        snapshot = tmp_path / "snap.json"
        snapshot.write_text(json.dumps(expected))
        result = runner.invoke(
            app,
            [
                "replay",
                "--batch",
                str(corpus),
                "--compare",
                str(snapshot),
                "--report-format",
                "junitxml",
            ],
        )
        assert result.exit_code == 0, result.output
        xml_text = self._extract_xml(result.output)
        root = ET.fromstring(xml_text)  # noqa: S314  (test-only)
        # Root is <testsuites>; one nested <testsuite>.
        suites = root.findall("testsuite")
        assert len(suites) == 1
        suite = suites[0]
        assert suite.attrib["tests"] == "2"
        assert suite.attrib["failures"] == "0"
        cases = suite.findall("testcase")
        assert len(cases) == 2
        # Match path: no <failure> children.
        for case in cases:
            assert case.find("failure") is None

    def test_junitxml_report_includes_failure_on_mismatch(self, tmp_path: Path) -> None:
        """On mismatch, junitxml surfaces a ``<failure>`` per offending index."""
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
            )
        )
        expected = _harvest_pre_check_decisions(runner, corpus)
        expected[0]["verdict"] = "deny"  # force mismatch
        snapshot = tmp_path / "snap.json"
        snapshot.write_text(json.dumps(expected))
        result = runner.invoke(
            app,
            [
                "replay",
                "--batch",
                str(corpus),
                "--compare",
                str(snapshot),
                "--report-format",
                "junitxml",
            ],
        )
        assert result.exit_code == 4, result.output
        xml_text = self._extract_xml(result.output)
        root = ET.fromstring(xml_text)  # noqa: S314  (test-only)
        suite = root.find("testsuite")
        assert suite.attrib["tests"] == "1"
        assert suite.attrib["failures"] == "1"
        case = suite.find("testcase")
        assert case is not None
        failure = case.find("failure")
        assert failure is not None
        assert failure.attrib["type"] == "policy_mismatch"
        assert "mismatch" in failure.text

    def test_junitxml_custom_suite_name(self, tmp_path: Path) -> None:
        """``--suite-name`` controls the testsuite name attribute."""
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
            )
        )
        expected = _harvest_pre_check_decisions(runner, corpus)
        snapshot = tmp_path / "snap.json"
        snapshot.write_text(json.dumps(expected))
        result = runner.invoke(
            app,
            [
                "replay",
                "--batch",
                str(corpus),
                "--compare",
                str(snapshot),
                "--report-format",
                "junitxml",
                "--suite-name",
                "ci.sota.audit",
            ],
        )
        assert result.exit_code == 0, result.output
        root = ET.fromstring(self._extract_xml(result.output))  # noqa: S314  (test-only)
        assert root.find("testsuite").attrib["name"] == "ci.sota.audit"

    def test_report_path_writes_to_disk(self, tmp_path: Path) -> None:
        """``--report-path`` writes the report and prints an ack on stdout."""
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
            )
        )
        expected = _harvest_pre_check_decisions(runner, corpus)
        snapshot = tmp_path / "snap.json"
        snapshot.write_text(json.dumps(expected))
        report_path = tmp_path / "report.json"
        result = runner.invoke(
            app,
            [
                "replay",
                "--batch",
                str(corpus),
                "--compare",
                str(snapshot),
                "--report-format",
                "json",
                "--report-path",
                str(report_path),
            ],
        )
        assert result.exit_code == 0, result.output
        assert "report written to" in result.output
        envelope = json.loads(report_path.read_text())
        assert envelope["matched"] is True
        assert envelope["items"] == 1

    def test_unknown_report_format_exits_one(self, tmp_path: Path) -> None:
        runner = CliRunner()
        corpus = tmp_path / "corpus.json"
        corpus.write_text(json.dumps([{"agent": "a", "lane": "standard"}]))
        snapshot = tmp_path / "snap.json"
        snapshot.write_text("[]")
        result = runner.invoke(
            app,
            [
                "replay",
                "--batch",
                str(corpus),
                "--compare",
                str(snapshot),
                "--report-format",
                "csv",
            ],
        )
        assert result.exit_code == 1, result.output
        assert "report-format" in result.output

    # ------------------------------------------------------------------ helpers

    @staticmethod
    def _extract_xml(output: str) -> str:
        """Slice the ``<testsuites>...</testsuites>`` block out of stdout.

        The SOTA command always prints the human-readable
        ``sota replay: matched=...`` line after the report, so we
        can't parse the full stdout as XML.
        """
        start = output.find("<testsuites")
        end = output.find("</testsuites>")
        assert start != -1 and end != -1, output
        return output[start : end + len("</testsuites>")]


# ---------------------------------------------------------------------------
# Exit-code convention
# ---------------------------------------------------------------------------


class TestSotaReplayExitCodes:
    """``sota replay`` exit codes mirror ``cockpit replay``."""

    def test_missing_batch_exits_one(self, tmp_path: Path) -> None:
        runner = CliRunner()
        snapshot = tmp_path / "snap.json"
        snapshot.write_text("[]")
        result = runner.invoke(
            app,
            [
                "replay",
                "--batch",
                str(tmp_path / "missing.json"),
                "--compare",
                str(snapshot),
            ],
        )
        assert result.exit_code == 1, result.output
        assert "not found" in result.output

    def test_missing_compare_exits_one(self, tmp_path: Path) -> None:
        runner = CliRunner()
        corpus = tmp_path / "corpus.json"
        corpus.write_text(json.dumps([{"agent": "a", "lane": "standard"}]))
        result = runner.invoke(
            app,
            [
                "replay",
                "--batch",
                str(corpus),
                "--compare",
                str(tmp_path / "missing.json"),
            ],
        )
        assert result.exit_code == 1, result.output

    def test_malformed_snapshot_exits_one(self, tmp_path: Path) -> None:
        runner = CliRunner()
        corpus = tmp_path / "corpus.json"
        corpus.write_text(json.dumps([{"agent": "a", "lane": "standard"}]))
        snapshot = tmp_path / "snap.json"
        snapshot.write_text(json.dumps({"foo": []}))  # no 'decisions' key
        result = runner.invoke(
            app,
            [
                "replay",
                "--batch",
                str(corpus),
                "--compare",
                str(snapshot),
            ],
        )
        assert result.exit_code == 1, result.output
        assert "decisions" in result.output

    def test_verdict_mismatch_exits_four(self, tmp_path: Path) -> None:
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
            )
        )
        expected = _harvest_pre_check_decisions(runner, corpus)
        expected[0]["verdict"] = "deny"  # force mismatch
        snapshot = tmp_path / "snap.json"
        snapshot.write_text(json.dumps(expected))
        result = runner.invoke(
            app,
            [
                "replay",
                "--batch",
                str(corpus),
                "--compare",
                str(snapshot),
            ],
        )
        assert result.exit_code == 4, result.output
        assert "matched=False" in result.output
        assert "mismatch[0]" in result.output


# ---------------------------------------------------------------------------
# CLI dispatch surface
# ---------------------------------------------------------------------------


class TestSotaCLIDispatch:
    """``thegent sota`` sub-app is well-formed and ``--help`` is informative."""

    def test_app_help_lists_replay_command(self) -> None:
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0, result.output
        assert "SOTA" in result.output or "sota" in result.output
        assert "replay" in result.output

    def test_replay_help_lists_snapshot_and_report_format(self) -> None:
        runner = CliRunner()
        # Wide terminal so long option names like ``--snapshot-format``
        # aren't truncated by Typer's panel formatter.
        result = runner.invoke(app, ["replay", "--help"], terminal_width=240)
        assert result.exit_code == 0, result.output
        # Strip ANSI escape codes and collapse whitespace so that
        # ``--snapshot-format`` isn't broken across panel gutters.
        clean = re.sub(r"\x1b\[[0-9;]*m", "", result.output)
        clean = re.sub(r"\s+", " ", clean)
        assert "--snapshot-format" in clean
        assert "--report-format" in clean
        assert "junitxml" in clean
