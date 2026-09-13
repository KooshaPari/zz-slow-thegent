"""JSON-shape parity between ``cockpit replay --json`` and ``sota replay --report-format json``.

Both commands share the same evaluation + compare pipeline but their
``--json`` envelopes were assembled independently (cockpit:
``_emit_replay_summary`` in ``src/thegent/ux/cli_cockpit.py``; sota:
``_render_report_json`` in ``src/thegent/ux/cli_sota.py``). SOTA audit
tooling that ``jq``-s the envelope will silently break if a refactor
drops a key from one side without touching the other, so this suite
pins the cross-cutting contract:

* ``matched`` (bool) and ``mismatches`` (list) MUST appear on both.
* Each ``mismatches[*]`` MUST carry ``index``, ``fields``, ``expected``,
  ``actual`` on both.

Scope is intentionally narrow: envelope SHAPE only. Mirrors the
``_write_batch``/``_write_compare`` fixture pattern from
``test_unit_ux_cli_cockpit_replay_audit_confirmation.py``.
"""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from thegent.ux.cli_cockpit import app as cockpit_app
from thegent.ux.cli_sota import app as sota_app

# Per-mismatch sub-keys the two envelopes MUST both expose.
_MISMATCH_SUBKEYS: tuple[str, ...] = ("index", "fields", "expected", "actual")


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
    """Run ``cockpit pre-check --batch --json`` and collect produced decisions.

    The engine's actual output is the only stable ground truth we can
    use for a matching snapshot.
    """
    result = runner.invoke(
        cockpit_app,
        ["pre-check", "--batch", str(corpus), "--json"],
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


def _write_snapshot(runner: CliRunner, batch: Path, compare: Path, *, flip: bool) -> None:
    """Persist a snapshot of decisions; ``flip=True`` inverts verdicts to force mismatch."""
    decisions = _harvest_decisions(runner, batch)
    if flip:
        flipped = []
        for d in decisions:
            d = dict(d)
            d["verdict"] = "allow" if d.get("verdict") != "allow" else "deny"
            flipped.append(d)
        decisions = flipped
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
# Positive path: matching snapshot
# ---------------------------------------------------------------------------


class TestCockpitSotaJsonParityPositive:
    """Both envelopes expose ``matched=True`` + empty ``mismatches``."""

    def test_cockpit_json_envelope_shape(self, tmp_path: Path) -> None:
        """``cockpit replay --json``: 6 top-level keys + per-mismatch sub-keys.

        Day 5/5 hardening lane pins the new ``items`` and ``flipped``
        keys in addition to the historical ``matched``/``mismatches``/
        ``decisions``/``audit`` contract. The Phase 3/4 SOTA audit
        second pass surfaced the drift where ``cockpit replay --json``
        was missing ``items`` (and the parity test used a ``>=``
        superset check that masked the gap); both surfaces now agree.
        """
        runner = CliRunner()
        batch = tmp_path / "batch.json"
        compare = tmp_path / "compare.json"
        audit = tmp_path / "audit.jsonl"
        _write_batch(batch)
        _write_snapshot(runner, batch, compare, flip=False)

        result = runner.invoke(
            cockpit_app,
            [
                "replay",
                "--batch",
                str(batch),
                "--compare",
                str(compare),
                "--audit-path",
                str(audit),
                "--json",
            ],
        )
        assert result.exit_code == 0, result.output
        envelope = json.loads(result.output)
        # Tight equality (Day 5/5 hardening lane + AUDIT-2): the
        # envelope must carry exactly these 6 keys so a downstream
        # consumer can rely on the contract without checking for
        # missing-or-extra fields.
        assert set(envelope.keys()) == {
            "matched",
            "items",
            "mismatches",
            "decisions",
            "audit",
            "flipped",
        }, envelope.keys()
        assert envelope["matched"] is True
        assert envelope["items"] == 2
        assert envelope["mismatches"] == []
        assert isinstance(envelope["decisions"], list)
        assert len(envelope["decisions"]) == 2
        assert envelope["audit"] == str(audit)
        # No flip flags were passed; the envelope must report an empty
        # flip set so the schema is stable.
        assert envelope["flipped"] == []

    def test_sota_json_envelope_shape(self, tmp_path: Path) -> None:
        """``sota replay --report-format json``: matched (bool) + mismatches (list).

        Day 5/5 hardening lane: also pins the new ``items`` and
        ``flipped`` keys for parity with the cockpit-side envelope.
        The Phase 3/4 SOTA audit second pass surfaced a key-set drift
        between the two surfaces (cockpit was missing ``items``);
        both now expose exactly the same 6 keys.
        """
        runner = CliRunner()
        batch = tmp_path / "batch.json"
        compare = tmp_path / "compare.json"
        _write_batch(batch)
        _write_snapshot(runner, batch, compare, flip=False)

        result = runner.invoke(
            sota_app,
            [
                "replay",
                "--batch",
                str(batch),
                "--compare",
                str(compare),
                "--snapshot-format",
                "json",
                "--report-format",
                "json",
            ],
        )
        envelope = _extract_last_json_object(result.output)
        assert set(envelope.keys()) == {
            "matched",
            "items",
            "mismatches",
            "decisions",
            "audit",
            "flipped",
        }, envelope.keys()
        assert isinstance(envelope.get("matched"), bool)
        assert envelope["matched"] is True
        assert isinstance(envelope.get("mismatches"), list)
        assert envelope["mismatches"] == []
        assert envelope["items"] == 2
        assert envelope["flipped"] == []


# ---------------------------------------------------------------------------
# Negative path: snapshot disagrees
# ---------------------------------------------------------------------------


class TestCockpitSotaJsonParityNegative:
    """Both envelopes expose ``matched=False`` + populated ``mismatches``."""

    def test_cockpit_json_negative_envelope(self, tmp_path: Path) -> None:
        """Cockpit on mismatch: matched=False + per-row {index,fields,expected,actual}."""
        runner = CliRunner()
        batch = tmp_path / "batch.json"
        compare = tmp_path / "compare.json"
        _write_batch(batch)
        _write_snapshot(runner, batch, compare, flip=True)

        result = runner.invoke(
            cockpit_app,
            ["replay", "--batch", str(batch), "--compare", str(compare), "--json"],
        )
        # Mismatch path exits 4; envelope is still printed before exit.
        assert result.exit_code == 4, result.output
        envelope = json.loads(result.output)
        assert envelope["matched"] is False
        assert envelope["mismatches"], "expected at least one mismatch row"
        for row in envelope["mismatches"]:
            assert set(row.keys()) >= set(_MISMATCH_SUBKEYS)
            assert isinstance(row["index"], int)
            assert isinstance(row["fields"], list)
            assert isinstance(row["expected"], dict)
            assert isinstance(row["actual"], dict)

    def test_sota_json_negative_envelope(self, tmp_path: Path) -> None:
        runner = CliRunner()
        batch = tmp_path / "batch.json"
        compare = tmp_path / "compare.json"
        _write_batch(batch)
        _write_snapshot(runner, batch, compare, flip=True)

        result = runner.invoke(
            sota_app,
            [
                "replay",
                "--batch",
                str(batch),
                "--compare",
                str(compare),
                "--snapshot-format",
                "json",
                "--report-format",
                "json",
            ],
        )
        assert result.exit_code == 4, result.output
        envelope = _extract_last_json_object(result.output)
        assert isinstance(envelope.get("matched"), bool)
        assert envelope["matched"] is False
        assert envelope["mismatches"], "expected at least one mismatch row"
        for row in envelope["mismatches"]:
            assert set(row.keys()) >= set(_MISMATCH_SUBKEYS)
            assert isinstance(row["index"], int)
            assert isinstance(row["fields"], list)
            assert isinstance(row["expected"], dict)
            assert isinstance(row["actual"], dict)
