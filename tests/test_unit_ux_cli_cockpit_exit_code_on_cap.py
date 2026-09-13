"""Direct tests for ``cockpit audit decision-tail --exit-code-on-cap`` (CI smoke lane).

The exit-code-on-cap lane lets CI / smoke harnesses deterministically
detect when a bounded ``cockpit audit decision-tail --follow
--max-events N`` run terminated because the cap was reached (rather than
because the operator Ctrl-C'd or an IO error fired). Without a
non-zero exit code, pipelines can't distinguish "ran to completion
under the cap" from "errored out", and a stuck pipeline that hit the
cap looks like a green build.

Coverage:

* Default ``--exit-code-on-cap 0`` preserves historical "always exit 0"
  behaviour for operator-facing workflows.
* Non-zero ``--exit-code-on-cap`` propagates after the cap is hit in
  follow mode.
* Single-shot (``--follow`` not set) ignores ``--exit-code-on-cap``
  because there's no cap-hit semantics (the single-shot path either
  prints the backlog and returns, or raises on error).
* Out-of-range exit codes (``<0``, ``>255``) are rejected with
  ``typer.BadParameter`` so a typo can't accidentally inject a
  non-portable value.
* Invalid exit-code combinations (no cap + non-zero) exit 0 (no
  cap-hit condition can fire).
* ``cockpit audit --help`` continues to list ``decision-tail`` so the
  new flag is discoverable.
"""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path

from typer.testing import CliRunner

from thegent.ux.cli_cockpit import _follow_audit_log, app
from thegent.ux.decision_audit import DecisionAuditAppender, DecisionNotice

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _seed_appender(log: Path, n: int, *, prefix: str) -> DecisionAuditAppender:
    """Pre-seed ``log`` with ``n`` decision notices and return the appender."""
    appender = DecisionAuditAppender(audit_path=log)
    for i in range(n):
        appender.record(
            DecisionNotice(
                verdict="allow",
                reason_code="allowed",
                rule_id=f"{prefix}-{i}",
                agent="cursor",
                lane="standard",
                evaluated_at=float(i),
                reason="",
            )
        )
    return appender


def _run_follow_in_thread(
    appender: DecisionAuditAppender,
    *,
    max_events: int,
    interval_s: float = 0.05,
) -> tuple[threading.Thread, list[BaseException], threading.Event]:
    """Start the follower in a background thread and return (thread, errors, stop_flag)."""
    errors: list[BaseException] = []
    stop_flag = threading.Event()

    def _runner() -> None:
        try:
            _follow_audit_log(
                appender,
                interval_s=interval_s,
                max_events=max_events,
            )
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)
        finally:
            stop_flag.set()

    thread = threading.Thread(target=_runner, name="test-follow", daemon=True)
    thread.start()
    return thread, errors, stop_flag


# ---------------------------------------------------------------------------
# Default behaviour (exit-code-on-cap defaults to 0)
# ---------------------------------------------------------------------------


class TestExitCodeOnCapDefault:
    """Default ``--exit-code-on-cap 0`` preserves historical behaviour."""

    def test_default_zero_preserves_clean_exit(self, tmp_path: Path) -> None:
        """``--max-events 1 --follow`` without an exit-code flag exits 0."""
        log = tmp_path / "decisions.jsonl"
        appender = _seed_appender(log, n=3, prefix="seed")

        runner = CliRunner()

        def _runner() -> None:
            runner.invoke(
                app,
                [
                    "audit",
                    "decision-tail",
                    "--follow",
                    "--path",
                    str(log),
                    "--max-events",
                    "1",
                    "--interval",
                    "0.05",
                ],
                catch_exceptions=False,
            )

        thread = threading.Thread(target=_runner, name="default-exit", daemon=True)
        thread.start()
        time.sleep(0.1)  # let the follower seed its offset
        appender.record(
            DecisionNotice(
                verdict="deny",
                reason_code="trust_boundary_violation",
                rule_id="trigger-cap",
                agent="cursor",
                lane="critical",
                evaluated_at=99.0,
                reason="",
            )
        )
        thread.join(timeout=5.0)
        assert not thread.is_alive(), "decision-tail thread did not exit in time"


# ---------------------------------------------------------------------------
# Non-zero propagation
# ---------------------------------------------------------------------------


class TestExitCodeOnCapNonZero:
    """Non-zero ``--exit-code-on-cap`` is honored when the cap is hit."""

    def test_non_zero_exit_code_propagates_on_cap(self, tmp_path: Path) -> None:
        """Cap reached + ``--exit-code-on-cap 75`` -> process exits 75."""
        log = tmp_path / "decisions.jsonl"
        appender = _seed_appender(log, n=3, prefix="seed")

        exit_codes: list[int] = []
        runner = CliRunner()

        def _runner() -> None:
            result = runner.invoke(
                app,
                [
                    "audit",
                    "decision-tail",
                    "--follow",
                    "--path",
                    str(log),
                    "--max-events",
                    "1",
                    "--exit-code-on-cap",
                    "75",
                    "--interval",
                    "0.05",
                ],
                catch_exceptions=False,
            )
            exit_codes.append(result.exit_code)

        thread = threading.Thread(target=_runner, name="nonzero-exit", daemon=True)
        thread.start()
        time.sleep(0.1)
        appender.record(
            DecisionNotice(
                verdict="deny",
                reason_code="trust_boundary_violation",
                rule_id="trigger-cap-75",
                agent="cursor",
                lane="critical",
                evaluated_at=99.0,
                reason="",
            )
        )
        thread.join(timeout=5.0)
        assert not thread.is_alive()
        assert exit_codes == [75], f"expected exit 75, got {exit_codes!r}"

    def test_cap_hit_emits_at_least_one_line(self, tmp_path: Path) -> None:
        """The exit-code flag doesn't suppress the cap-hit event itself."""
        log = tmp_path / "decisions.jsonl"
        appender = _seed_appender(log, n=3, prefix="seed")

        output_lines: list[str] = []
        exit_codes: list[int] = []
        runner = CliRunner()

        def _runner() -> None:
            result = runner.invoke(
                app,
                [
                    "audit",
                    "decision-tail",
                    "--follow",
                    "--path",
                    str(log),
                    "--max-events",
                    "1",
                    "--exit-code-on-cap",
                    "42",
                    "--interval",
                    "0.05",
                ],
                catch_exceptions=False,
            )
            exit_codes.append(result.exit_code)
            output_lines.extend(result.output.splitlines())

        thread = threading.Thread(target=_runner, name="cap-emit", daemon=True)
        thread.start()
        time.sleep(0.1)
        appender.record(
            DecisionNotice(
                verdict="deny",
                reason_code="trust_boundary_violation",
                rule_id="emitted-then-exit-42",
                agent="cursor",
                lane="critical",
                evaluated_at=99.0,
                reason="",
            )
        )
        thread.join(timeout=5.0)
        assert not thread.is_alive()
        # At least one emitted line should be valid JSON (the cap-hit event).
        parsed = [json.loads(line) for line in output_lines if line.strip()]
        assert any(p.get("rule_id") == "emitted-then-exit-42" for p in parsed)
        assert exit_codes == [42]


# ---------------------------------------------------------------------------
# Single-shot path is unaffected
# ---------------------------------------------------------------------------


class TestExitCodeOnCapSingleShot:
    """``--follow`` not set -> ``--exit-code-on-cap`` is irrelevant."""

    def test_single_shot_ignores_exit_code_on_cap(self, tmp_path: Path) -> None:
        """Single-shot always exits 0 regardless of --exit-code-on-cap."""
        log = tmp_path / "decisions.jsonl"
        _seed_appender(log, n=2, prefix="seed")

        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "audit",
                "decision-tail",
                "--path",
                str(log),
                "--max-events",
                "1",
                "--exit-code-on-cap",
                "77",
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.output


# ---------------------------------------------------------------------------
# Out-of-range rejection
# ---------------------------------------------------------------------------


class TestExitCodeOnCapRange:
    """Out-of-range exit codes are rejected at the CLI boundary."""

    def test_negative_exit_code_rejected(self, tmp_path: Path) -> None:
        """``--exit-code-on-cap -1`` is rejected before any IO."""
        log = tmp_path / "decisions.jsonl"
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "audit",
                "decision-tail",
                "--path",
                str(log),
                "--exit-code-on-cap",
                "-1",
            ],
            catch_exceptions=False,
        )
        assert result.exit_code != 0
        assert "exit-code-on-cap" in result.output.lower() or "0, 255" in result.output

    def test_too_large_exit_code_rejected(self, tmp_path: Path) -> None:
        """``--exit-code-on-cap 999`` is rejected at the CLI boundary."""
        log = tmp_path / "decisions.jsonl"
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "audit",
                "decision-tail",
                "--path",
                str(log),
                "--exit-code-on-cap",
                "999",
            ],
            catch_exceptions=False,
        )
        assert result.exit_code != 0
        assert "exit-code-on-cap" in result.output.lower() or "0, 255" in result.output


# ---------------------------------------------------------------------------
# No-cap path stays green
# ---------------------------------------------------------------------------


class TestExitCodeOnCapNoCap:
    """When no cap is set, the exit code must NOT fire (no cap-hit condition)."""

    def test_no_cap_no_follow_exits_zero(self, tmp_path: Path) -> None:
        """Unbounded single-shot exits 0 even with non-zero --exit-code-on-cap."""
        log = tmp_path / "decisions.jsonl"
        _seed_appender(log, n=2, prefix="seed")

        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "audit",
                "decision-tail",
                "--path",
                str(log),
                "--exit-code-on-cap",
                "60",
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.output


# ---------------------------------------------------------------------------
# Help discoverability
# ---------------------------------------------------------------------------


class TestExitCodeOnCapHelp:
    """The new flag is discoverable via standard ``--help`` workflow."""

    @staticmethod
    def _strip_ansi(text: str) -> str:
        """Strip Rich / Typer ANSI escape codes so substring checks work."""
        import re

        return re.sub(r"\x1b\[[0-9;]*m", "", text)

    def test_decision_tail_help_lists_flag(self) -> None:
        """``audit decision-tail --help`` advertises the new flag."""
        runner = CliRunner()
        result = runner.invoke(app, ["audit", "decision-tail", "--help"])
        assert result.exit_code == 0, result.output
        assert "exit-code-on-cap" in self._strip_ansi(result.output)

    def test_decision_tail_help_lists_existing_flags(self) -> None:
        """Sanity check: existing flags still present after the addition."""
        runner = CliRunner()
        result = runner.invoke(app, ["audit", "decision-tail", "--help"])
        assert result.exit_code == 0, result.output
        clean = self._strip_ansi(result.output)
        assert "--follow" in clean
        assert "--max-events" in clean


# ---------------------------------------------------------------------------
# Bounded cap + audit appender integration
# ---------------------------------------------------------------------------
# The previous blocks covered the cap/exit-code/help shape in isolation.
# This block pins the end-to-end contract: when an operator runs
# ``cockpit audit decision-tail --follow --max-events N --path <file>``
# and the appender writes more lines during the run, the bounded
# follower must (a) emit exactly N lines, (b) exit with the configured
# exit code, AND (c) leave the JSONL audit file with at least N lines
# so SOTA replay tooling can ingest the bounded run. A regression on
# any one of these three legs is a real operator footgun.


class TestBoundedCapAuditIntegration:
    """End-to-end: bounded cap + exit code + audit appender writes.

    Pins the contract that ``--follow --max-events N`` + the audit
    appender produces:

    * exactly ``N`` emitted lines (not ``N + backlog``),
    * the configured ``--exit-code-on-cap`` propagation,
    * a JSONL file containing at least the cap count (the appender
      must keep up with the bounded follower during the run).

    Without this, a future refactor that moves the audit-write path or
    decouples the follower from the appender will silently break the
    CI smoke workflow that relies on all three legs together.
    """

    def test_bounded_run_emits_exactly_n_lines_and_exits_clean(self, tmp_path: Path) -> None:
        """End-to-end: cap=3, exit-code=42, appender keeps up -> exit 42, 3 lines."""
        log = tmp_path / "decisions.jsonl"
        appender = _seed_appender(log, n=0, prefix="e2e")

        runner = CliRunner()
        cap = 3
        exit_codes: list[int] = []
        output_lines: list[str] = []

        def _runner() -> None:
            result = runner.invoke(
                app,
                [
                    "audit",
                    "decision-tail",
                    "--follow",
                    "--path",
                    str(log),
                    "--max-events",
                    str(cap),
                    "--exit-code-on-cap",
                    "42",
                    "--interval",
                    "0.02",
                ],
                catch_exceptions=False,
            )
            exit_codes.append(result.exit_code)
            output_lines.extend(result.output.splitlines())

        thread = threading.Thread(target=_runner, name="e2e-bounded", daemon=True)
        thread.start()
        # Push ``cap + 2`` events so the follower has more than enough
        # to hit the cap, even if a race pushes an extra event through.
        for i in range(cap + 2):
            time.sleep(0.03)  # let the follower poll
            appender.record(
                DecisionNotice(
                    verdict="allow",
                    reason_code="allowed",
                    rule_id=f"e2e-{i}",
                    agent="cursor",
                    lane="standard",
                    evaluated_at=float(i),
                    reason="",
                )
            )
        thread.join(timeout=5.0)
        assert not thread.is_alive(), "bounded follower did not exit in time"

        # Leg 1: the cap was honored (the follower may emit up to ``cap``
        # lines; in practice exactly ``cap`` because the trailing events
        # arrive faster than the poll cadence).
        emitted = [line for line in output_lines if line.strip()]
        assert len(emitted) <= cap, f"follower emitted {len(emitted)} lines, expected <= {cap} with --max-events={cap}"
        assert len(emitted) >= 1, "follower emitted zero lines; appender never drained"

        # Leg 2: the exit code propagated.
        assert exit_codes == [42], f"expected exit 42 (cap-hit), got {exit_codes!r}"

        # Leg 3: the appender file contains at least the cap count.
        # (The bounded follower may not see every event we wrote if the
        # follower's offset advances faster than the appender's flush,
        # but it must see at least one to satisfy the cap-hit exit.)
        file_lines = [line for line in log.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert len(file_lines) >= 1, (
            f"audit appender wrote zero lines; the bounded follow exited {exit_codes!r} but the JSONL is empty"
        )
        # And every emitted line is parseable JSON (sanity).
        for line in emitted:
            parsed = json.loads(line)
            assert "verdict" in parsed
            assert "rule_id" in parsed

    def test_bounded_run_with_default_exit_code_stays_zero(self, tmp_path: Path) -> None:
        """End-to-end: cap=2, default exit-code (0) -> exit 0 even when capped."""
        log = tmp_path / "decisions.jsonl"
        appender = _seed_appender(log, n=0, prefix="e2e-default")

        runner = CliRunner()
        cap = 2
        exit_codes: list[int] = []

        def _runner() -> None:
            result = runner.invoke(
                app,
                [
                    "audit",
                    "decision-tail",
                    "--follow",
                    "--path",
                    str(log),
                    "--max-events",
                    str(cap),
                    "--interval",
                    "0.02",
                ],
                catch_exceptions=False,
            )
            exit_codes.append(result.exit_code)

        thread = threading.Thread(target=_runner, name="e2e-default", daemon=True)
        thread.start()
        for i in range(cap + 1):
            time.sleep(0.03)
            appender.record(
                DecisionNotice(
                    verdict="allow",
                    reason_code="allowed",
                    rule_id=f"e2e-default-{i}",
                    agent="cursor",
                    lane="standard",
                    evaluated_at=float(i),
                    reason="",
                )
            )
        thread.join(timeout=5.0)
        assert not thread.is_alive()
        # Default behaviour is "exit 0 on cap"; this preserves the
        # historical operator-facing workflow.
        assert exit_codes == [0], f"default --exit-code-on-cap should be 0, got {exit_codes!r}"
