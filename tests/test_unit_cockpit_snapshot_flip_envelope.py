"""Day 5/5 hardening lane — JSON-envelope ``flipped`` field coverage.

The Day 4/5 sprint added ``--snapshot-flip`` (single + repeated) and
``--snapshot-flip-all`` to ``cockpit replay`` and ``sota replay``, but
did not surface the resolved flip set to downstream consumers. This
file pins the new top-level ``flipped`` key on both the cockpit and
sota JSON envelopes, the cockpit-shim forwarding contract, and the
JUnit-XML ``<property name="flipped" .../>`` extension so a CI runner
can introspect the flip set without re-running the compare.

The tests below run end-to-end via ``CliRunner`` and consume real
``cockpit pre-check`` output for ground-truth decisions, mirroring
the fixture pattern in ``test_unit_cockpit_sota_json_parity.py``.
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from typer.testing import CliRunner

from thegent.ux.cli_cockpit import app as cockpit_app
from thegent.ux.cli_sota import app as sota_app

# ---------------------------------------------------------------------------
# Fixtures (mirrors ``test_unit_cockpit_sota_json_parity.py``)
# ---------------------------------------------------------------------------


def _write_batch(path: Path) -> None:
    """Write a 2-context batch the cockpit/sota replay CLIs accept."""
    context = {
        "agent": "cursor",
        "model": "",
        "lane": "standard",
        "confidence": 0.95,
        "environment": "development",
        "namespace": "global",
        "prompt": "",
        "cost_usd": 0.0,
        "metadata": {},
    }
    path.write_text(json.dumps([context, dict(context)]), encoding="utf-8")


def _harvest_decisions(runner: CliRunner, corpus: Path) -> list[dict]:
    """Run ``cockpit pre-check --batch --json`` and collect produced decisions."""
    result = runner.invoke(
        cockpit_app,
        ["pre-check", "--batch", str(corpus), "--json"],
    )
    assert result.exit_code in (0, 3), result.output
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


def _write_snapshot(compare: Path, decisions: list[dict]) -> None:
    """Persist a snapshot of decisions to disk."""
    compare.write_text(json.dumps(decisions), encoding="utf-8")


def _extract_last_json_object(text: str) -> dict:
    """Return the last balanced JSON object embedded in ``text``.

    ``sota replay`` always appends a ``sota replay: matched=...`` tail
    line so we cannot ``json.loads(text)`` directly; we walk forward
    and return the last well-formed object encountered.
    """
    decoder = json.JSONDecoder()
    last_obj: dict | None = None
    idx = 0
    while idx < len(text):
        while idx < len(text) and text[idx].isspace():
            idx += 1
        if idx >= len(text) or text[idx] != "{":
            break
        obj, end = decoder.raw_decode(text[idx:])
        last_obj = obj
        idx += end
    assert last_obj is not None, f"no JSON object found in sota output: {text!r}"
    return last_obj


# ---------------------------------------------------------------------------
# Cockpit replay --json envelope: ``flipped`` key
# ---------------------------------------------------------------------------


class TestCockpitReplayFlippedField:
    """``cockpit replay --json`` exposes the resolved flip set under ``flipped``."""

    def test_no_flip_flag_yields_empty_flipped(self, tmp_path: Path) -> None:
        """Without ``--snapshot-flip*``, ``flipped`` is the empty list."""
        runner = CliRunner()
        batch = tmp_path / "batch.json"
        compare = tmp_path / "compare.json"
        _write_batch(batch)
        _write_snapshot(compare, _harvest_decisions(runner, batch))

        result = runner.invoke(
            cockpit_app,
            [
                "replay",
                "--batch",
                str(batch),
                "--compare",
                str(compare),
                "--json",
            ],
        )
        assert result.exit_code == 0, result.output
        envelope = json.loads(result.output)
        assert envelope["flipped"] == []
        assert envelope["matched"] is True

    def test_single_flip_flag_surfaces_in_envelope(self, tmp_path: Path) -> None:
        """``--snapshot-flip verdict`` -> ``flipped == ["verdict"]``."""
        runner = CliRunner()
        batch = tmp_path / "batch.json"
        compare = tmp_path / "compare.json"
        _write_batch(batch)
        _write_snapshot(compare, _harvest_decisions(runner, batch))

        result = runner.invoke(
            cockpit_app,
            [
                "replay",
                "--batch",
                str(batch),
                "--compare",
                str(compare),
                "--snapshot-flip",
                "verdict",
                "--json",
            ],
        )
        assert result.exit_code == 4, result.output  # mismatch path
        envelope = json.loads(result.output)
        assert envelope["flipped"] == ["verdict"]
        assert envelope["matched"] is False
        assert envelope["mismatches"], "expected at least one mismatch row"

    def test_repeated_flip_flag_dedupes_in_envelope(self, tmp_path: Path) -> None:
        """Repeated ``--snapshot-flip verdict`` collapses to ``["verdict"]``."""
        runner = CliRunner()
        batch = tmp_path / "batch.json"
        compare = tmp_path / "compare.json"
        _write_batch(batch)
        _write_snapshot(compare, _harvest_decisions(runner, batch))

        result = runner.invoke(
            cockpit_app,
            [
                "replay",
                "--batch",
                str(batch),
                "--compare",
                str(compare),
                "--snapshot-flip",
                "verdict",
                "--snapshot-flip",
                "verdict",
                "--json",
            ],
        )
        envelope = json.loads(result.output)
        assert envelope["flipped"] == ["verdict"]

    def test_multi_field_flip_preserves_first_seen_order(self, tmp_path: Path) -> None:
        """``--snapshot-flip verdict --snapshot-flip override_applied`` keeps order."""
        runner = CliRunner()
        batch = tmp_path / "batch.json"
        compare = tmp_path / "compare.json"
        _write_batch(batch)
        _write_snapshot(compare, _harvest_decisions(runner, batch))

        result = runner.invoke(
            cockpit_app,
            [
                "replay",
                "--batch",
                str(batch),
                "--compare",
                str(compare),
                "--snapshot-flip",
                "verdict",
                "--snapshot-flip",
                "override_applied",
                "--json",
            ],
        )
        envelope = json.loads(result.output)
        assert envelope["flipped"] == ["verdict", "override_applied"]

    def test_flip_all_preset_in_envelope(self, tmp_path: Path) -> None:
        """``--snapshot-flip-all`` expands to the canonical triple."""
        runner = CliRunner()
        batch = tmp_path / "batch.json"
        compare = tmp_path / "compare.json"
        _write_batch(batch)
        _write_snapshot(compare, _harvest_decisions(runner, batch))

        result = runner.invoke(
            cockpit_app,
            [
                "replay",
                "--batch",
                str(batch),
                "--compare",
                str(compare),
                "--snapshot-flip-all",
                "--json",
            ],
        )
        envelope = json.loads(result.output)
        assert envelope["flipped"] == ["verdict", "override_applied", "cached"]

    def test_flip_all_with_explicit_field_dedupes(self, tmp_path: Path) -> None:
        """``--snapshot-flip-all --snapshot-flip verdict`` does not duplicate."""
        runner = CliRunner()
        batch = tmp_path / "batch.json"
        compare = tmp_path / "compare.json"
        _write_batch(batch)
        _write_snapshot(compare, _harvest_decisions(runner, batch))

        result = runner.invoke(
            cockpit_app,
            [
                "replay",
                "--batch",
                str(batch),
                "--compare",
                str(compare),
                "--snapshot-flip-all",
                "--snapshot-flip",
                "verdict",
                "--json",
            ],
        )
        envelope = json.loads(result.output)
        assert envelope["flipped"] == ["verdict", "override_applied", "cached"]


# ---------------------------------------------------------------------------
# Sota replay --report-format json envelope: ``flipped`` key
# ---------------------------------------------------------------------------


class TestSotaReplayFlippedField:
    """``sota replay --report-format json`` exposes ``flipped`` for parity."""

    def test_no_flip_flag_yields_empty_flipped(self, tmp_path: Path) -> None:
        """Without ``--snapshot-flip*``, ``flipped`` is the empty list."""
        runner = CliRunner()
        batch = tmp_path / "batch.json"
        compare = tmp_path / "compare.json"
        _write_batch(batch)
        _write_snapshot(compare, _harvest_decisions(runner, batch))

        result = runner.invoke(
            sota_app,
            [
                "replay",
                "--batch",
                str(batch),
                "--compare",
                str(compare),
                "--report-format",
                "json",
            ],
        )
        envelope = _extract_last_json_object(result.output)
        assert envelope["flipped"] == []
        assert envelope["matched"] is True

    def test_flip_all_surfaces_in_envelope(self, tmp_path: Path) -> None:
        """``--snapshot-flip-all`` -> ``flipped == ["verdict", ...]``."""
        runner = CliRunner()
        batch = tmp_path / "batch.json"
        compare = tmp_path / "compare.json"
        _write_batch(batch)
        _write_snapshot(compare, _harvest_decisions(runner, batch))

        result = runner.invoke(
            sota_app,
            [
                "replay",
                "--batch",
                str(batch),
                "--compare",
                str(compare),
                "--snapshot-flip-all",
                "--report-format",
                "json",
            ],
        )
        envelope = _extract_last_json_object(result.output)
        assert envelope["flipped"] == ["verdict", "override_applied", "cached"]
        assert envelope["matched"] is False

    def test_yaml_snapshot_with_flip_surfaces_in_envelope(self, tmp_path: Path) -> None:
        """``--snapshot-format yaml --snapshot-flip-all`` -> ``flipped`` set."""
        pytest = __import__("pytest")  # noqa: PLC0415 — defer for PyYAML skip
        pytest.importorskip("yaml")
        runner = CliRunner()
        batch = tmp_path / "batch.json"
        compare = tmp_path / "compare.yaml"
        _write_batch(batch)
        decisions = _harvest_decisions(runner, batch)
        import yaml  # type: ignore[import-untyped]  # noqa: PLC0415

        compare.write_text(yaml.safe_dump(decisions), encoding="utf-8")

        result = runner.invoke(
            sota_app,
            [
                "replay",
                "--batch",
                str(batch),
                "--compare",
                str(compare),
                "--snapshot-format",
                "yaml",
                "--report-format",
                "json",
                "--snapshot-flip-all",
            ],
        )
        envelope = _extract_last_json_object(result.output)
        assert envelope["flipped"] == ["verdict", "override_applied", "cached"]


# ---------------------------------------------------------------------------
# Cockpit -> Sota shim: ``flipped`` propagates through delegation
# ---------------------------------------------------------------------------


class TestCockpitShimFlippedField:
    """The cockpit shim forwards ``--snapshot-flip*`` to sota and the JSON envelope surfaces it."""

    def test_cockpit_shim_with_flip_all_emits_sota_envelope(
        self, tmp_path: Path
    ) -> None:
        """``cockpit replay --snapshot-flip-all --report-format json`` delegates + carries flipped."""
        runner = CliRunner()
        batch = tmp_path / "batch.json"
        compare = tmp_path / "compare.json"
        _write_batch(batch)
        _write_snapshot(compare, _harvest_decisions(runner, batch))

        result = runner.invoke(
            cockpit_app,
            [
                "replay",
                "--batch",
                str(batch),
                "--compare",
                str(compare),
                "--snapshot-flip-all",
                "--report-format",
                "json",
            ],
        )
        # The shim always returns the sota envelope even on
        # mismatch; the ``cockpit replay --json`` text-tail line is
        # suppressed via the ``_render_tail=False`` flag in the shim.
        envelope = _extract_last_json_object(result.output)
        assert envelope["flipped"] == ["verdict", "override_applied", "cached"]

    def test_cockpit_shim_with_no_flip_emits_empty_flipped(
        self, tmp_path: Path
    ) -> None:
        """``cockpit replay --report-format json`` with no flip yields ``flipped == []``."""
        runner = CliRunner()
        batch = tmp_path / "batch.json"
        compare = tmp_path / "compare.json"
        _write_batch(batch)
        _write_snapshot(compare, _harvest_decisions(runner, batch))

        result = runner.invoke(
            cockpit_app,
            [
                "replay",
                "--batch",
                str(batch),
                "--compare",
                str(compare),
                "--report-format",
                "json",
            ],
        )
        envelope = _extract_last_json_object(result.output)
        assert envelope["flipped"] == []


# ---------------------------------------------------------------------------
# JUnit-XML: ``flipped`` is exposed as ``<property>`` on the testsuite root
# ---------------------------------------------------------------------------


class TestSotaJunitXmlFlippedProperty:
    """``sota replay --report-format junitxml`` exposes ``flipped`` via ``<properties>``."""

    def test_no_flip_omits_properties_element(self, tmp_path: Path) -> None:
        """Without a flip flag the ``<properties>`` element is absent."""
        runner = CliRunner()
        batch = tmp_path / "batch.json"
        compare = tmp_path / "compare.json"
        report = tmp_path / "report.xml"
        _write_batch(batch)
        _write_snapshot(compare, _harvest_decisions(runner, batch))

        result = runner.invoke(
            sota_app,
            [
                "replay",
                "--batch",
                str(batch),
                "--compare",
                str(compare),
                "--report-format",
                "junitxml",
                "--report-path",
                str(report),
                "--suite-name",
                "ci.thegent.day5",
            ],
        )
        assert result.exit_code == 0, result.output
        tree = ET.parse(report)  # noqa: S314  (test-only)
        testsuite = tree.getroot().find("testsuite")
        assert testsuite is not None
        # No <properties> child when the operator did not pass any flip flag.
        assert testsuite.find("properties") is None

    def test_flip_all_adds_flipped_property(self, tmp_path: Path) -> None:
        """``--snapshot-flip-all`` -> ``<properties><property name='flipped' value='...'/>``."""
        runner = CliRunner()
        batch = tmp_path / "batch.json"
        compare = tmp_path / "compare.json"
        report = tmp_path / "report.xml"
        _write_batch(batch)
        _write_snapshot(compare, _harvest_decisions(runner, batch))

        result = runner.invoke(
            sota_app,
            [
                "replay",
                "--batch",
                str(batch),
                "--compare",
                str(compare),
                "--report-format",
                "junitxml",
                "--report-path",
                str(report),
                "--suite-name",
                "ci.thegent.day5",
                "--snapshot-flip-all",
            ],
        )
        assert result.exit_code == 4, result.output  # mismatch path
        tree = ET.parse(report)  # noqa: S314  (test-only)
        testsuite = tree.getroot().find("testsuite")
        assert testsuite is not None
        properties = testsuite.find("properties")
        assert properties is not None, "<properties> element missing on testsuite root"
        prop = properties.find("property")
        assert prop is not None
        assert prop.get("name") == "flipped"
        assert prop.get("value") == "verdict,override_applied,cached"

    def test_single_flip_property_value_is_field_name(self, tmp_path: Path) -> None:
        """``--snapshot-flip verdict`` -> ``<property value='verdict'/>``."""
        runner = CliRunner()
        batch = tmp_path / "batch.json"
        compare = tmp_path / "compare.json"
        report = tmp_path / "report.xml"
        _write_batch(batch)
        _write_snapshot(compare, _harvest_decisions(runner, batch))

        runner.invoke(
            sota_app,
            [
                "replay",
                "--batch",
                str(batch),
                "--compare",
                str(compare),
                "--report-format",
                "junitxml",
                "--report-path",
                str(report),
                "--suite-name",
                "ci.thegent.day5",
                "--snapshot-flip",
                "verdict",
            ],
        )
        tree = ET.parse(report)  # noqa: S314  (test-only)
        testsuite = tree.getroot().find("testsuite")
        assert testsuite is not None
        properties = testsuite.find("properties")
        assert properties is not None
        prop = properties.find("property")
        assert prop is not None
        assert prop.get("name") == "flipped"
        assert prop.get("value") == "verdict"


# ---------------------------------------------------------------------------
# Direct helper coverage — pinned composition semantics
# ---------------------------------------------------------------------------


class TestFlipEnvelopeCompositionSemantics:
    """Pin the cross-surface contract at the helper level (no I/O)."""

    def test_cockpit_emit_replay_summary_flipped_is_serialised(self) -> None:
        """``_emit_replay_summary(json_output=True, flipped=[...])`` includes the key."""
        import contextlib
        import io

        from thegent.ux.cli_cockpit import _emit_replay_summary

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            _emit_replay_summary(
                items=2,
                matched=False,
                mismatches=[
                    {
                        "index": 0,
                        "fields": ["verdict"],
                        "expected": {"verdict": "deny"},
                        "actual": {"verdict": "allow"},
                        "text": "mismatch[0]: verdict expected=deny actual=allow",
                    }
                ],
                decisions=[{"verdict": "allow"}, {"verdict": "allow"}],
                audit_path=None,
                json_output=True,
                flipped=["verdict"],
            )
        envelope = json.loads(buf.getvalue())
        assert envelope["flipped"] == ["verdict"]
        assert envelope["items"] == 2
        assert envelope["matched"] is False

    def test_cockpit_emit_replay_summary_no_flip_defaults_to_empty_list(self) -> None:
        """``_emit_replay_summary(..., flipped=None)`` -> ``flipped == []`` (no key drift)."""
        import contextlib
        import io

        from thegent.ux.cli_cockpit import _emit_replay_summary

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            _emit_replay_summary(
                items=0,
                matched=True,
                mismatches=[],
                decisions=[],
                audit_path=None,
                json_output=True,
            )
        envelope = json.loads(buf.getvalue())
        assert envelope["flipped"] == []

    def test_sota_render_report_json_flipped_is_serialised(self) -> None:
        """``_render_report_json(flipped=[...])`` includes the key on the sota side."""
        from thegent.ux.cli_sota import _render_report_json

        rendered = _render_report_json(
            items=1,
            matched=False,
            mismatches=[],
            decisions=[],
            audit_path=None,
            flipped=["verdict", "override_applied"],
        )
        envelope = json.loads(rendered)
        assert envelope["flipped"] == ["verdict", "override_applied"]
