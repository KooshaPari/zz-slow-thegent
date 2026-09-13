"""Tests for the operator cockpit's audit wiring + decision-history pane + CLI batch.

These tests cover the third iteration of the Phase 3/4 hardening lane:

1. ``OperatorCockpit(audit_appender=..., auto_tail=True)`` — production
   deployments get free JSONL persistence for every
   :meth:`record_decision` call without manual wiring, and the cockpit
   owns / stops the background :class:`DecisionAuditTailer` via
   :meth:`shutdown`.
2. The new decision-history pane appears at the bottom of the cockpit
   render with verdict glyph, rule_id, agent, lane, age, and reason
   code. It mirrors the existing override-history UX (different stream).
3. ``thegent cockpit pre-check --batch <path>`` replays a JSON corpus
   (file or directory of ``*.json``) and persists a combined audit
   log; deny verdicts surface via exit code ``3`` so shell pipelines
   can react.
"""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path

import pytest
from typer.testing import CliRunner

from thegent.ux.cli_cockpit import (
    _follow_audit_log,
    _load_pre_check_corpus,
    app,
)
from thegent.ux.cockpit import (
    MAX_DECISION_PANE_ROWS,
    DecisionNotice,
    OperatorCockpit,
    _decision_glyph,
    _format_decision_row,
)
from thegent.ux.decision_audit import DecisionAuditAppender

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _FrozenClock:
    """Mutable wall-clock callable for deterministic replays."""

    def __init__(self, start: float = 1_700_000_000.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def _make_notice(
    *,
    verdict: str = "deny",
    rule_id: str = "no-network",
    agent: str = "cursor",
    lane: str = "critical",
    evaluated_at: float = 0.0,
) -> DecisionNotice:
    return DecisionNotice(
        verdict=verdict,
        reason_code="trust_boundary_violation",
        rule_id=rule_id,
        agent=agent,
        lane=lane,
        evaluated_at=evaluated_at,
        reason="",
    )


# ---------------------------------------------------------------------------
# 1. OperatorCockpit(audit_appender=..., auto_tail=...) wiring
# ---------------------------------------------------------------------------


class TestOperatorCockpitAuditAppenderWiring:
    """``audit_appender`` + ``auto_tail`` constructor wiring + lifecycle."""

    def test_default_policy_commit_enables_federation(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``--default-policy`` with ``--commit`` builds ``PolicyEngine(use_federation=True, ...)``."""
        from thegent.governance import policy_engine as pe_mod

        captured: dict[str, object] = {}

        class _SpyEngine:
            def __init__(self, *args: object, **kwargs: object) -> None:
                captured["kwargs"] = kwargs
                self.federated = None
                self._cache: dict[str, object] = {}
                self._lock = type("L", (), {})()  # no-op lock

            def evaluate(self, ctx: object) -> object:
                return type(
                    "D",
                    (),
                    {
                        "verdict": type("V", (), {"value": "allow"})(),
                        "reason_code": type("R", (), {"value": "allowed"})(),
                        "rule_id": None,
                        "reason": "ok",
                        "override_applied": False,
                        "evaluated_at": 0.0,
                        "cached": False,
                        "to_dict": lambda self: {"verdict": "allow"},
                    },
                )()

        monkeypatch.setattr(pe_mod, "PolicyEngine", _SpyEngine)
        corpus = tmp_path / "corpus.json"
        corpus.write_text(
            json.dumps(
                [
                    {
                        "agent": "a",
                        "lane": "standard",
                        "confidence": 0.9,
                        "environment": "development",
                    }
                ]
            )
        )
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "pre-check",
                "--batch",
                str(corpus),
                "--commit",
                "--default-policy",
                "team-acme",
            ],
        )
        assert result.exit_code == 0, result.output
        kwargs = captured["kwargs"]
        assert kwargs["use_federation"] is True
        assert kwargs["default_namespace"] == "team-acme"

    def test_default_policy_single_context_commit_enables_federation(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Single-context ``--default-policy --commit`` also enables federation."""
        from thegent.governance import policy_engine as pe_mod

        captured: dict[str, object] = {}

        class _SpyEngine:
            def __init__(self, *args: object, **kwargs: object) -> None:
                captured["kwargs"] = kwargs
                self._cache: dict[str, object] = {}
                self._lock = type("L", (), {})()

            def evaluate(self, ctx: object) -> object:
                return type(
                    "D",
                    (),
                    {
                        "verdict": type("V", (), {"value": "allow"})(),
                        "reason_code": type("R", (), {"value": "allowed"})(),
                        "rule_id": None,
                        "reason": "ok",
                        "override_applied": False,
                        "evaluated_at": 0.0,
                        "cached": False,
                        "to_dict": lambda self: {"verdict": "allow"},
                    },
                )()

        monkeypatch.setattr(pe_mod, "PolicyEngine", _SpyEngine)
        runner = CliRunner()
        result = runner.invoke(
            app,
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
                "--commit",
                "--default-policy",
                "team-acme",
            ],
        )
        assert result.exit_code == 0, result.output
        kwargs = captured["kwargs"]
        assert kwargs["use_federation"] is True
        assert kwargs["default_namespace"] == "team-acme"

    def test_default_policy_omitted_keeps_federation_off(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Omitting ``--default-policy`` keeps ``use_federation=False`` on the engine."""
        from thegent.governance import policy_engine as pe_mod

        captured: dict[str, object] = {}

        class _SpyEngine:
            def __init__(self, *args: object, **kwargs: object) -> None:
                captured["kwargs"] = kwargs
                self._cache: dict[str, object] = {}
                self._lock = type("L", (), {})()

            def evaluate(self, ctx: object) -> object:
                return type(
                    "D",
                    (),
                    {
                        "verdict": type("V", (), {"value": "allow"})(),
                        "reason_code": type("R", (), {"value": "allowed"})(),
                        "rule_id": None,
                        "reason": "ok",
                        "override_applied": False,
                        "evaluated_at": 0.0,
                        "cached": False,
                        "to_dict": lambda self: {"verdict": "allow"},
                    },
                )()

        monkeypatch.setattr(pe_mod, "PolicyEngine", _SpyEngine)
        corpus = tmp_path / "corpus.json"
        corpus.write_text(
            json.dumps(
                [
                    {
                        "agent": "a",
                        "lane": "standard",
                        "confidence": 0.9,
                        "environment": "development",
                    }
                ]
            )
        )
        runner = CliRunner()
        result = runner.invoke(
            app,
            ["pre-check", "--batch", str(corpus), "--commit"],
        )
        assert result.exit_code == 0, result.output
        kwargs = captured["kwargs"]
        assert kwargs["use_federation"] is False
        assert kwargs["default_namespace"] == "global"

    def test_frozen_clock_propagates_through_auto_tail(self, tmp_path: Path) -> None:
        # Determinism: the cockpit's injected clock determines
        # ``emitted_at`` JSONL stamps when the appender's clock is the
        # same callable, so SOTA replay tooling can reproduce a run.
        log = tmp_path / "decisions.jsonl"
        clk = _FrozenClock(start=1_700_000_000.0)
        appender = DecisionAuditAppender(audit_path=log, clock=clk)
        cockpit = OperatorCockpit(
            audit_appender=appender,
            auto_tail=True,
            tail_interval_s=0.05,
            clock=clk,
        )
        try:
            cockpit.record_decision(
                _make_notice(evaluated_at=clk.now),
            )
            deadline = time.time() + 5.0
            while time.time() < deadline:
                try:
                    if log.stat().st_size > 0:
                        break
                except FileNotFoundError:
                    pass
                time.sleep(0.05)
            tail = appender.tail_events(n=5)
            assert len(tail) == 1
            assert tail[0]["emitted_at"] == pytest.approx(1_700_000_000.0)
        finally:
            cockpit.shutdown(timeout_s=2.0)


# ---------------------------------------------------------------------------
# 2. Decision-history pane
# ---------------------------------------------------------------------------


class TestDecisionHistoryPane:
    """The new full-width decision-history pane (WP-3001 -> WP-4001)."""

    def test_empty_decision_history_renders_neutral_pane(self) -> None:
        cockpit = OperatorCockpit()
        rendered = cockpit.render()
        # Always present in the rendered output, even when there are no
        # recorded notices.
        assert "Decision History" in rendered
        assert "(no policy decisions recorded yet)" in rendered
        cockpit.shutdown()

    def test_single_deny_renders_with_ballot_x_glyph(self) -> None:
        clk = _FrozenClock(start=1_700_000_000.0)
        cockpit = OperatorCockpit(clock=clk)
        try:
            cockpit.record_decision(
                _make_notice(verdict="deny", rule_id="crit.lane", evaluated_at=clk.now)
            )
            rendered = cockpit.render()
            assert "Decision History" in rendered
            # Glyph + rule_id present.
            assert "\u2717 crit.lane" in rendered
        finally:
            cockpit.shutdown()

    def test_allow_uses_check_mark(self) -> None:
        cockpit = OperatorCockpit(clock=_FrozenClock())
        try:
            cockpit.record_decision(
                _make_notice(
                    verdict="allow",
                    rule_id="std.allow",
                    lane="standard",
                    evaluated_at=time.time(),
                )
            )
            rendered = cockpit.render()
            assert "\u2713 std.allow" in rendered
        finally:
            cockpit.shutdown()

    def test_warn_uses_bang(self) -> None:
        cockpit = OperatorCockpit(clock=_FrozenClock())
        try:
            cockpit.record_decision(
                _make_notice(
                    verdict="warn",
                    rule_id="cost.warn",
                    lane="standard",
                    evaluated_at=time.time(),
                )
            )
            rendered = cockpit.render()
            assert "! cost.warn" in rendered
        finally:
            cockpit.shutdown()

    def test_zero_evaluated_at_renders_dash_glyph(self) -> None:
        cockpit = OperatorCockpit()
        try:
            # No clock provided; ``evaluated_at`` stays 0.
            cockpit.record_decision(_make_notice(verdict="allow"))
            rendered = cockpit.render()
            assert "-" in rendered
            # The pane shows the placeholder age when the notice hasn't
            # been clocked yet.
            assert "   -" in rendered
        finally:
            cockpit.shutdown()

    def test_pane_respects_max_rows_with_ellipsis(self) -> None:
        clk = _FrozenClock(start=1_700_000_000.0)
        cockpit = OperatorCockpit(clock=clk)
        try:
            for i in range(MAX_DECISION_PANE_ROWS + 3):
                cockpit.record_decision(
                    _make_notice(
                        verdict="allow",
                        rule_id=f"rule.{i:03d}",
                        evaluated_at=clk.now,
                    )
                )
            rendered = cockpit.render()
            assert "older decisions hidden" in rendered
        finally:
            cockpit.shutdown()

    def test_decision_glyph_helper_classifies_verdicts(self) -> None:
        assert _decision_glyph(_make_notice(verdict="deny")) == "\u2717"
        assert _decision_glyph(_make_notice(verdict="warn")) == "!"
        assert (
            _decision_glyph(_make_notice(verdict="allow", evaluated_at=1.0)) == "\u2713"
        )
        # No clock yet -> dash (no fake age).
        assert _decision_glyph(_make_notice(verdict="allow", evaluated_at=0.0)) == "-"

    def test_format_decision_row_layout_is_stable(self) -> None:
        notice = _make_notice(
            verdict="allow",
            rule_id="std.allow",
            agent="cursor",
            lane="standard",
            evaluated_at=1_700_000_000.0,
        )
        row = _format_decision_row(notice, age=12.0)
        # Columns in order: rule_id, agent, lane, age, reason_code.
        assert row.startswith("std.allow")
        assert "cursor" in row
        assert "standard" in row
        assert "12s" in row
        # ``reason_code`` is truncated to 16 chars by the formatter;
        # assert the prefix so the test does not depend on the
        # truncation policy.
        assert "trust_boundary" in row


# ---------------------------------------------------------------------------
# 3. ``cockpit pre-check --batch`` (SOTA replay corpus)
# ---------------------------------------------------------------------------


class TestPreCheckBatchCLI:
    """``thegent cockpit pre-check --batch`` replay tooling."""

    def test_batch_file_overwrite_audit_default(self, tmp_path: Path) -> None:
        corpus = tmp_path / "corpus.json"
        corpus.write_text(
            json.dumps(
                [
                    {
                        "agent": "cursor",
                        "lane": "critical",
                        "confidence": 0.5,
                        "environment": "production",
                    },
                    {
                        "agent": "cursor",
                        "lane": "standard",
                        "confidence": 0.95,
                        "environment": "development",
                    },
                ]
            )
        )
        audit = tmp_path / "audit.jsonl"
        # Pre-seed with stale content to prove overwrite semantics.
        audit.write_text('{"stale":true}\n')
        runner = CliRunner()
        result = runner.invoke(
            app,
            ["pre-check", "--batch", str(corpus), "--audit-path", str(audit)],
        )
        # The corpus contains a deny (critical lane + low confidence),
        # so the command must surface exit code 3.
        assert result.exit_code == 3, result.output
        assert "pre-check batch: items=2 deny=True" in result.output
        lines = audit.read_text().strip().splitlines()
        # Overwrite: only the two fresh decisions remain.
        assert len(lines) == 2
        joined = "\n".join(lines)
        assert "stale" not in joined
        assert '"verdict":"deny"' in joined
        assert '"verdict":"allow"' in joined

    def test_batch_file_append_audit_keeps_prior_lines(self, tmp_path: Path) -> None:
        corpus = tmp_path / "corpus.json"
        corpus.write_text(
            json.dumps(
                [
                    {
                        "agent": "cursor",
                        "lane": "standard",
                        "confidence": 0.9,
                        "environment": "development",
                    }
                ]
            )
        )
        audit = tmp_path / "audit.jsonl"
        audit.write_text('{"prior":"line"}\n')
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "pre-check",
                "--batch",
                str(corpus),
                "--audit-path",
                str(audit),
                "--audit-append",
            ],
        )
        assert result.exit_code == 0
        lines = audit.read_text().strip().splitlines()
        assert any('"prior":"line"' in line for line in lines)
        assert any('"verdict":"allow"' in line for line in lines)
        assert len(lines) == 2

    def test_batch_directory_globs_json_files(self, tmp_path: Path) -> None:
        d = tmp_path / "corpus"
        d.mkdir()
        (d / "a.json").write_text(
            json.dumps(
                [
                    {
                        "agent": "a",
                        "lane": "standard",
                        "confidence": 0.9,
                        "environment": "development",
                    }
                ]
            )
        )
        (d / "b.json").write_text(
            json.dumps(
                [
                    {
                        "agent": "b",
                        "lane": "critical",
                        "confidence": 0.1,
                        "environment": "production",
                    }
                ]
            )
        )
        # Non-JSON files are ignored.
        (d / "README.txt").write_text("skip me")
        audit = tmp_path / "audit.jsonl"
        runner = CliRunner()
        result = runner.invoke(
            app,
            ["pre-check", "--batch", str(d), "--audit-path", str(audit)],
        )
        # Critical lane + low confidence + production -> deny.
        assert result.exit_code == 3
        lines = audit.read_text().strip().splitlines()
        assert len(lines) == 2
        agents = {json.loads(line)["agent"] for line in lines}
        assert agents == {"a", "b"}

    def test_batch_single_context_object_in_file(self, tmp_path: Path) -> None:
        # Single JSON object (not a list) is also accepted.
        corpus = tmp_path / "single.json"
        corpus.write_text(
            json.dumps(
                {
                    "agent": "cursor",
                    "lane": "standard",
                    "confidence": 0.95,
                    "environment": "development",
                }
            )
        )
        audit = tmp_path / "audit.jsonl"
        runner = CliRunner()
        result = runner.invoke(
            app,
            ["pre-check", "--batch", str(corpus), "--audit-path", str(audit)],
        )
        assert result.exit_code == 0
        lines = audit.read_text().strip().splitlines()
        assert len(lines) == 1
        assert '"verdict":"allow"' in lines[0]

    def test_batch_empty_corpus_reports_quietly(self, tmp_path: Path) -> None:
        empty = tmp_path / "empty.json"
        empty.write_text("[]")
        runner = CliRunner()
        result = runner.invoke(app, ["pre-check", "--batch", str(empty)])
        # Empty corpus is a no-op success; no deny => exit 0.
        assert result.exit_code == 0
        assert "pre-check batch is empty" in result.output

    def test_batch_missing_path_surfaces_error(self, tmp_path: Path) -> None:
        missing = tmp_path / "nope.json"
        runner = CliRunner()
        result = runner.invoke(app, ["pre-check", "--batch", str(missing)])
        assert result.exit_code == 1
        assert "not found" in result.output or "nope" in result.output

    def test_load_corpus_rejects_non_object_entries(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.json"
        bad.write_text(json.dumps([123, 456]))
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "pre-check",
                "--batch",
                str(bad),
                "--audit-path",
                str(tmp_path / "audit.jsonl"),
            ],
        )
        # Bad entries surface a useful error and exit code 1.
        assert result.exit_code == 1
        assert "must be objects" in result.output


class TestLoadPreCheckCorpus:
    """Direct unit tests for the corpus loader (no CLI round-trip)."""

    def test_load_file_list(self, tmp_path: Path) -> None:
        p = tmp_path / "x.json"
        p.write_text(json.dumps([{"agent": "a"}, {"agent": "b"}]))
        out = _load_pre_check_corpus(p)
        assert [c.agent for c in out] == ["a", "b"]

    def test_load_file_single_object(self, tmp_path: Path) -> None:
        p = tmp_path / "x.json"
        p.write_text(json.dumps({"agent": "x", "lane": "standard"}))
        out = _load_pre_check_corpus(p)
        assert len(out) == 1
        assert out[0].agent == "x"

    def test_load_directory_concatenates(self, tmp_path: Path) -> None:
        d = tmp_path / "c"
        d.mkdir()
        (d / "1.json").write_text(json.dumps([{"agent": "1"}]))
        (d / "2.json").write_text(json.dumps({"agent": "2"}))
        out = _load_pre_check_corpus(d)
        assert sorted(c.agent for c in out) == ["1", "2"]

    def test_missing_path_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            _load_pre_check_corpus(tmp_path / "missing")


# ---------------------------------------------------------------------------
# 5. ``cockpit replay --batch --compare`` (SOTA snapshot validator)
# ---------------------------------------------------------------------------


def _harvest_pre_check_decisions(
    runner: CliRunner,
    corpus: Path,
) -> list[dict[str, object]]:
    """Run ``pre-check --batch --json`` once and harvest the decision dicts.

    The replay sub-command must accept snapshots in the same shape the
    engine emits, so we synthesise them straight from the engine to keep
    these tests deterministic without hard-coding engine internals.
    """
    result = runner.invoke(
        app,
        ["pre-check", "--batch", str(corpus), "--json"],
    )
    assert result.exit_code in (0, 3), result.output
    # The pre-check --json stream emits one JSON object per item, then a
    # trailing human-readable status line. We walk forward one object at
    # a time and stop at the first non-JSON-prefix byte.
    snapshots: list[dict[str, object]] = []
    decoder = json.JSONDecoder()
    idx = 0
    text = result.output
    while idx < len(text):
        while idx < len(text) and text[idx].isspace():
            idx += 1
        if idx >= len(text) or text[idx] not in "{[":
            break
        obj, end = decoder.raw_decode(text[idx:])
        snapshots.append(obj)
        idx += end
    assert snapshots, f"no decisions harvested from pre-check output: {text!r}"
    return snapshots


class TestReplayCLI:
    """``thegent cockpit replay --batch --compare`` line-by-line snapshot diff."""

    def test_happy_path_match_exits_zero(self, tmp_path: Path) -> None:
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
                        "lane": "critical",
                        "confidence": 0.1,
                        "environment": "production",
                    },
                ]
            )
        )
        expected = _harvest_pre_check_decisions(runner, corpus)
        snapshot = tmp_path / "snapshot.json"
        snapshot.write_text(json.dumps(expected))
        result = runner.invoke(
            app,
            ["replay", "--batch", str(corpus), "--compare", str(snapshot)],
        )
        assert result.exit_code == 0, result.output
        assert "matched=True" in result.output
        assert "mismatches=0" in result.output

    def test_verdict_mismatch_exits_four_and_reports_index(
        self,
        tmp_path: Path,
    ) -> None:
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
        # Force a verdict mismatch at index 0.
        expected[0]["verdict"] = "deny"
        snapshot = tmp_path / "snapshot.json"
        snapshot.write_text(json.dumps(expected))
        result = runner.invoke(
            app,
            ["replay", "--batch", str(corpus), "--compare", str(snapshot)],
        )
        assert result.exit_code == 4, result.output
        assert "matched=False" in result.output
        assert "mismatch[0]" in result.output
        assert "verdict" in result.output
        assert "expected=deny" in result.output

    def test_structural_length_mismatch_exits_four(self, tmp_path: Path) -> None:
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
                        "lane": "critical",
                        "confidence": 0.1,
                        "environment": "production",
                    },
                ]
            )
        )
        expected = _harvest_pre_check_decisions(runner, corpus)[:1]
        snapshot = tmp_path / "snapshot.json"
        snapshot.write_text(json.dumps(expected))
        result = runner.invoke(
            app,
            ["replay", "--batch", str(corpus), "--compare", str(snapshot)],
        )
        assert result.exit_code == 4, result.output
        assert "length" in result.output
        assert "expected=1" in result.output
        assert "actual=2" in result.output

    def test_snapshot_with_decisions_key_is_accepted(self, tmp_path: Path) -> None:
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
        snapshot = tmp_path / "snapshot.json"
        snapshot.write_text(json.dumps({"decisions": expected}))
        result = runner.invoke(
            app,
            ["replay", "--batch", str(corpus), "--compare", str(snapshot)],
        )
        assert result.exit_code == 0, result.output
        assert "matched=True" in result.output

    def test_audit_path_writes_jsonl_matching_appender(self, tmp_path: Path) -> None:
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
                        "lane": "critical",
                        "confidence": 0.1,
                        "environment": "production",
                    },
                ]
            )
        )
        expected = _harvest_pre_check_decisions(runner, corpus)
        snapshot = tmp_path / "snapshot.json"
        snapshot.write_text(json.dumps(expected))
        audit = tmp_path / "audit.jsonl"
        result = runner.invoke(
            app,
            [
                "replay",
                "--batch",
                str(corpus),
                "--compare",
                str(snapshot),
                "--audit-path",
                str(audit),
            ],
        )
        assert result.exit_code == 0, result.output
        lines = audit.read_text().strip().splitlines()
        assert len(lines) == 2
        parsed = [json.loads(line) for line in lines]
        for line in parsed:
            assert "verdict" in line
            assert "rule_id" in line
            assert "evaluated_at" in line
        verdicts = {line["verdict"] for line in parsed}
        assert "deny" in verdicts
        assert "allow" in verdicts

    def test_json_mode_emits_parseable_object_with_matched_bool(
        self,
        tmp_path: Path,
    ) -> None:
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
        snapshot = tmp_path / "snapshot.json"
        snapshot.write_text(json.dumps(expected))
        result = runner.invoke(
            app,
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
        payload = json.loads(result.output)
        assert payload["matched"] is True
        assert payload["mismatches"] == []
        assert len(payload["decisions"]) == len(expected)
        for got, want in zip(payload["decisions"], expected, strict=False):
            assert got["verdict"] == want["verdict"]
            assert got["reason_code"] == want["reason_code"]
            assert got["rule_id"] == want["rule_id"]
            assert got["override_applied"] == want["override_applied"]
            assert got["reason"].strip() == want["reason"].strip()
        assert "audit" in payload

    def test_json_mode_mismatch_payload_includes_diff_details(
        self,
        tmp_path: Path,
    ) -> None:
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
        expected[0]["reason_code"] = "fabricated_reason_code"
        snapshot = tmp_path / "snapshot.json"
        snapshot.write_text(json.dumps(expected))
        result = runner.invoke(
            app,
            [
                "replay",
                "--batch",
                str(corpus),
                "--compare",
                str(snapshot),
                "--json",
            ],
        )
        assert result.exit_code == 4, result.output
        payload = json.loads(result.output)
        assert payload["matched"] is False
        assert payload["mismatches"], payload
        first = payload["mismatches"][0]
        assert first["index"] == 0
        assert "reason_code" in first["fields"]

    def test_replay_rejects_malformed_snapshot(self, tmp_path: Path) -> None:
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
        snapshot = tmp_path / "snapshot.json"
        snapshot.write_text(json.dumps({"foo": []}))  # no 'decisions' key
        result = runner.invoke(
            app,
            ["replay", "--batch", str(corpus), "--compare", str(snapshot)],
        )
        assert result.exit_code == 1, result.output
        assert "decisions" in result.output

    def test_replay_missing_compare_path_exits_one(self, tmp_path: Path) -> None:
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
        assert "not found" in result.output


# ---------------------------------------------------------------------------
# 4. ``cockpit audit decision-tail --follow`` (live tail)
# ---------------------------------------------------------------------------


class TestDecisionTailFollow:
    """``thegent cockpit audit decision-tail`` follow-mode tests.

    Covers the first "Unblocked Next" item from ``WORKLOG.md``: a
    follow-mode for the JSONL decision audit log so operators can
    watch live decisions without manually specifying ``--path``.
    """

    def test_decision_tail_default_path_round_trip(self, tmp_path: Path) -> None:
        # Single-shot, no --follow. Pre-seed the log with two decisions,
        # then invoke the command without --follow and assert both
        # lines are echoed back.
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
                reason="",
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
        runner = CliRunner()
        result = runner.invoke(
            app,
            ["audit", "decision-tail", "--path", str(log)],
        )
        assert result.exit_code == 0, result.output
        lines = [line for line in result.output.splitlines() if line.strip()]
        assert len(lines) == 2
        parsed = [json.loads(line) for line in lines]
        assert parsed[0]["rule_id"] == "no-network"
        assert parsed[1]["rule_id"] is None

    def test_decision_tail_follow_emits_new_lines(self, tmp_path: Path) -> None:
        # Pre-seed the log with N lines, start follow in a background
        # thread with ``--max-events 1`` (the cap counts events the
        # follower emits, not lines already on disk), write an extra
        # line into the log mid-flight, and verify the new line is
        # emitted and the thread exits cleanly within the timeout.
        log = tmp_path / "decisions.jsonl"
        appender = DecisionAuditAppender(audit_path=log)
        n_seeded = 3
        for i in range(n_seeded):
            appender.record(
                DecisionNotice(
                    verdict="allow",
                    reason_code="allowed",
                    rule_id=f"seed-{i}",
                    agent="cursor",
                    lane="standard",
                    evaluated_at=float(i),
                    reason="",
                )
            )

        interval_s = 0.05
        emit_error: list[BaseException] = []
        stop_flag = threading.Event()

        def _runner() -> None:
            try:
                _follow_audit_log(
                    appender,
                    interval_s=interval_s,
                    max_events=1,
                )
            except BaseException as exc:  # noqa: BLE001
                emit_error.append(exc)
            finally:
                stop_flag.set()

        thread = threading.Thread(
            target=_runner, name="test-decision-tail", daemon=True
        )
        thread.start()
        try:
            # Give the thread time to seed its offset from the file's
            # current size before we append the new line.
            time.sleep(interval_s * 2)
            appender.record(
                DecisionNotice(
                    verdict="deny",
                    reason_code="trust_boundary_violation",
                    rule_id="live-tail",
                    agent="cursor",
                    lane="critical",
                    evaluated_at=99.0,
                    reason="",
                )
            )
            thread.join(timeout=5.0)
            assert not thread.is_alive(), "decision-tail thread did not exit in time"
        finally:
            if thread.is_alive():
                stop_flag.set()
                thread.join(timeout=2.0)

        assert not emit_error, f"unexpected error in follow thread: {emit_error!r}"
        assert stop_flag.is_set()

        events = appender.tail_events(n=10)
        assert len(events) == n_seeded + 1
        assert events[-1]["rule_id"] == "live-tail"

    def test_decision_tail_follow_handles_truncation(self, tmp_path: Path) -> None:
        # Pre-seed the log, start the follower, truncate the file
        # (write ""), append a fresh line via the appender, and verify
        # the follower re-anchors and emits the new line.
        log = tmp_path / "decisions.jsonl"
        appender = DecisionAuditAppender(audit_path=log)
        for i in range(2):
            appender.record(
                DecisionNotice(
                    verdict="allow",
                    reason_code="allowed",
                    rule_id=f"pre-{i}",
                    agent="cursor",
                    lane="standard",
                    evaluated_at=float(i),
                    reason="",
                )
            )

        interval_s = 0.05
        emit_error: list[BaseException] = []

        def _runner() -> None:
            try:
                _follow_audit_log(
                    appender,
                    interval_s=interval_s,
                    max_events=1,
                )
            except BaseException as exc:  # noqa: BLE001
                emit_error.append(exc)

        thread = threading.Thread(
            target=_runner, name="test-truncation-tail", daemon=True
        )
        thread.start()
        try:
            time.sleep(interval_s * 2)
            log.write_text("", encoding="utf-8")
            DecisionAuditAppender(audit_path=log).record(
                DecisionNotice(
                    verdict="deny",
                    reason_code="trust_boundary_violation",
                    rule_id="after-truncate",
                    agent="cursor",
                    lane="critical",
                    evaluated_at=42.0,
                    reason="",
                )
            )
            thread.join(timeout=5.0)
            assert not thread.is_alive(), "follower did not exit in time"
        finally:
            if thread.is_alive():
                thread.join(timeout=2.0)

        assert not emit_error, f"unexpected error in follow thread: {emit_error!r}"

        events = DecisionAuditAppender(audit_path=log).tail_events(n=10)
        assert len(events) == 1
        assert events[0]["rule_id"] == "after-truncate"

    def test_decision_tail_help(self) -> None:
        # ``cockpit audit --help`` lists the new command so operators
        # can discover it via the standard CLI help workflow.
        runner = CliRunner()
        result = runner.invoke(app, ["audit", "--help"])
        assert result.exit_code == 0, result.output
        assert "decision-tail" in result.output
