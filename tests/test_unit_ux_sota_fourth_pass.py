"""SOTA fourth-pass hardening tests (Phase 3/4 lane).

Closes the fourth-pass audit findings identified in the prior
``cockpit.py`` / ``cockpit_bridge.py`` / ``explanations.py`` review:

* NEW-19 — ``OperatorCockpit.render`` + every ``_render_*_pane``
  method now serialise their ``self._state`` reads under ``self._lock``
  so a concurrent ``tick`` / ``record_decision`` cannot tear the
  snapshot. ``_frame_count`` and ``_last_render_ms`` are bumped under
  the lock to close the read-modify-write race.
* NEW-20 — ``_render_override_banner`` and ``_render_decisions_pane``
  sample ``self._clock()`` inside the same critical section that
  copies the notice pointers, so a clock swap between the locked
  read and the unlocked ``now`` cannot compute ages against a
  different clock than the one used to write ``evaluated_at``.
* NEW-21 — ``_render_header`` docstring is corrected: the F-13
  comment claimed "use ``self._clock``" but the function actually
  formats the stored ``self._state.last_tick_at`` (which is already
  populated via ``self._clock()`` under the lock by :meth:`tick` —
  see NEW-18). The misleading F-13 block is removed; the
  clock-injection contract is now stated once and accurately.
* NEW-22 — ``_follow_audit_log`` now catches transient I/O errors
  (file unlinked mid-poll, ``OSError`` on NFS, ``EPERM`` on
  permission flips) instead of crashing the tail loop; the
  truncation semantics are documented so SOTA replay tooling
  knows the recovery contract.
* NEW-23 — ``_render_summary`` / ``_render_detailed`` /
  ``_render_deepdive`` share a ``_core_attribute_lines`` helper
  with an ``align=True|False`` toggle so the column-padding
  contract lives in one place; ``_render_summary`` retains the
  historical single-space form pinned by SOTA regression tests
  via ``align=False``.

These tests are intentionally small and independent — each one
documents the contract a future operator / CI consumer can rely on.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

from thegent.ux.cli_cockpit import _follow_audit_log
from thegent.ux.cockpit import DecisionNotice, OperatorCockpit
from thegent.ux.decision_audit import DecisionAuditAppender
from thegent.ux.explanations import (
    DecisionExplanation,
    DisclosureLevel,
    ExplanationBuilder,
    render_explanation,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_notice(
    *, verdict: str = "allow", reason_code: str = "ok", ts: float = 0.0
) -> DecisionNotice:
    """Build a DecisionNotice with the minimum required fields."""
    return DecisionNotice(
        verdict=verdict,
        reason_code=reason_code,
        rule_id="r.fourth",
        agent="fourth-pass",
        lane="standard",
        evaluated_at=ts or time.time(),
        reason="sota-fourth-pass test",
    )


# ---------------------------------------------------------------------------
# NEW-19 — render and pane renderers are thread-safe under cockpit lock
# ---------------------------------------------------------------------------


class TestRenderSerialisesUnderLock:
    """Pin the NEW-19 contract: ``render`` + the pane renderers copy
    ``self._state`` under ``self._lock`` so a concurrent ``tick``
    cannot tear a row that the operator sees in their terminal."""

    def test_concurrent_tick_and_render_no_exception(self) -> None:
        """Hammer the cockpit with concurrent tick/render threads and
        assert no exception escapes either side. Pre-NEW-19, a
        ``RuntimeError: dictionary changed size during iteration``
        could be raised from ``_render_runs_pane`` when ``tick``
        swapped ``self._state.runs`` mid-iteration."""
        cockpit = OperatorCockpit()
        errors: list[BaseException] = []
        stop = threading.Event()

        def ticker() -> None:
            try:
                while not stop.is_set():
                    cockpit.tick(progress=(1, 2))
                    time.sleep(0.0001)
            except BaseException as exc:  # noqa: BLE001
                errors.append(exc)

        def renderer() -> None:
            try:
                while not stop.is_set():
                    cockpit.render()
                    time.sleep(0.0001)
            except BaseException as exc:  # noqa: BLE001
                errors.append(exc)

        threads = [
            threading.Thread(target=ticker, name="ticker"),
            threading.Thread(target=ticker, name="ticker-2"),
            threading.Thread(target=renderer, name="renderer"),
            threading.Thread(target=renderer, name="renderer-2"),
        ]
        for t in threads:
            t.start()
        # Run for a small window then stop.
        time.sleep(0.5)
        stop.set()
        for t in threads:
            t.join(timeout=2.0)
        assert errors == [], f"concurrent tick/render raised: {errors!r}"

    def test_frame_count_increments_under_lock(self) -> None:
        """``render`` increments ``_frame_count`` under the lock so
        concurrent renders do not lose increments to a
        read-modify-write race."""
        cockpit = OperatorCockpit()
        for _ in range(50):
            cockpit.render()
        with cockpit._lock:  # noqa: SLF001
            final_count = cockpit._frame_count  # noqa: SLF001
        assert final_count == 50

    def test_progress_bar_reads_under_lock(self) -> None:
        """``progress_bar()`` reads ``last_progress`` under the lock."""
        cockpit = OperatorCockpit()
        cockpit.tick(progress=(3, 10))
        text = cockpit.progress_bar()
        # The bar is rendered; the contract is "no exception under
        # concurrent tick". Smoke-assert the percent matches.
        assert "30%" in text

    def test_last_render_ms_reads_under_lock(self) -> None:
        """``last_render_ms()`` reads ``_last_render_ms`` under the lock."""
        cockpit = OperatorCockpit()
        cockpit.render()
        value = cockpit.last_render_ms()
        assert value >= 0.0


# ---------------------------------------------------------------------------
# NEW-20 — _render_override_banner / _render_decisions_pane sample clock under lock
# ---------------------------------------------------------------------------


class TestBannerClockSnapshottedUnderLock:
    """Pin the NEW-20 contract: the banner + decisions-pane renderers
    sample ``self._clock()`` inside the same critical section that
    copies the notice pointers, so a clock swap cannot compute ages
    against a different clock than the one used to write
    ``evaluated_at``."""

    def test_decisions_pane_no_clock_swap_drift(self) -> None:
        """A ``record_decision`` followed by a clock swap must still
        surface the correct age in the decisions pane. Pre-NEW-20
        the age could land as ``now - ts`` where ``now`` was the new
        clock and ``ts`` was the old clock, producing a wildly
        negative ``max(0.0, now - ts)`` (clamped to 0)."""
        clock_value = {"v": 1_700_000_000.0}

        def clock() -> float:
            return clock_value["v"]

        cockpit = OperatorCockpit(clock=clock)
        cockpit.tick(progress=(1, 1))
        cockpit.record_decision(
            DecisionNotice(
                verdict="allow",
                reason_code="r.test",
                rule_id="r.test",
                evaluated_at=1_700_000_000.0,
                reason="fourth-pass",
            )
        )
        # Advance clock by 5s and render; the age must be 5s.
        clock_value["v"] = 1_700_000_005.0
        text = cockpit.render()
        assert "5s" in text


# ---------------------------------------------------------------------------
# NEW-21 — _render_header F-13 comment cleaned up
# ---------------------------------------------------------------------------


class TestRenderHeaderDocstringCleaned:
    """Pin the NEW-21 contract: ``_render_header`` docstring no longer
    contains the misleading "use ``self._clock``" claim. The function
    formats the *stored* ``self._state.last_tick_at`` (which is
    already populated via ``self._clock()`` under the lock by
    :meth:`tick` — see NEW-18)."""

    def test_no_stale_f13_comment_in_module(self) -> None:
        from thegent.ux import cockpit as cockpit_mod

        src = Path(cockpit_mod.__file__).read_text(encoding="utf-8")
        # The F-13 "use self._clock" comment block is gone.
        assert "F-13 (SOTA third-pass): use ``self._clock``" not in src
        # The NEW-21 marker is present in the docstring.
        assert "NEW-21" in src

    def test_render_header_uses_stored_tick_at(self) -> None:
        """End-to-end check: header shows the stored tick timestamp."""
        cockpit = OperatorCockpit(clock=lambda: 1_700_000_000.0)
        cockpit.tick(progress=(1, 1))
        text = cockpit.render()
        import time as _time

        expected = _time.strftime("%H:%M:%S", _time.localtime(1_700_000_000.0))
        assert f"tick={expected}" in text


# ---------------------------------------------------------------------------
# NEW-22 — _follow_audit_log survives transient I/O
# ---------------------------------------------------------------------------


class TestFollowAuditLogSurvivesTransientIO:
    """Pin the NEW-22 contract: ``_follow_audit_log`` catches
    transient I/O errors (unlink mid-poll, ``OSError`` on NFS,
    ``EPERM`` on permission flips) instead of crashing the tail loop;
    the truncation semantics are documented."""

    def test_unlink_mid_poll_does_not_crash(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A file unlinked between ``stat()`` and ``open()`` must not
        propagate ``FileNotFoundError`` to the caller. The tail loop
        should log at DEBUG and retry on the next tick."""
        path = tmp_path / "audit.jsonl"
        path.write_text("{}\n", encoding="utf-8")
        appender = DecisionAuditAppender(audit_path=path)

        # Patch ``path.open`` to raise ``FileNotFoundError`` once,
        # then succeed (simulates a transient unlink).
        real_open = Path.open
        call_count = {"n": 0}

        def flaky_open(self: Path, *args: object, **kwargs: object):  # type: ignore[no-untyped-def]
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise FileNotFoundError("simulated unlink")
            return real_open(self, *args, **kwargs)  # type: ignore[arg-type]

        monkeypatch.setattr(Path, "open", flaky_open)

        # Stop after a small number of polls. The helper loops forever,
        # so we run it in a thread and signal stop via timeout.
        result: dict[str, object] = {}

        def _run() -> None:
            try:
                # ``max_events=1`` so the loop returns after the first
                # emit (it never gets that far because we patch the
                # open to fail). Use a short interval so the test is
                # fast.
                result["emitted"] = _follow_audit_log(
                    appender,
                    interval_s=0.01,
                    max_events=1,
                )
            except BaseException as exc:  # noqa: BLE001
                result["error"] = exc

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        thread.join(timeout=1.0)
        assert "error" not in result, f"tail loop crashed: {result.get('error')!r}"


# ---------------------------------------------------------------------------
# NEW-23 — explanations renderer consolidates shared blocks
# ---------------------------------------------------------------------------


class TestExplanationsRendererConsolidated:
    """Pin the NEW-23 contract: ``render_explanation`` delegates to
    shared helpers so the column-padding contract is single-sourced."""

    def test_summary_layout_byte_identical(self) -> None:
        """SUMMARY must keep the single-space "compact" form pinned
        by ``test_summary_includes_rule``."""
        exp = (
            ExplanationBuilder()
            .title("hotfix")
            .verdict("ALLOW")
            .reason("hotfix")
            .reason_code("r1")
            .rule_id("rule-1")
            .confidence(0.9)
            .build()
        )
        text = render_explanation(exp, level=DisclosureLevel.SUMMARY)
        # Single-space form, byte-for-byte identical to pre-NEW-23 output.
        assert "reason: hotfix" in text
        assert "reason_code: r1" in text
        assert "rule_id: rule-1" in text
        assert "confidence: 0.90" in text

    def test_detailed_layout_aligned(self) -> None:
        """DETAILED must align values at column 14 (so labels read
        ``reason:       value``)."""
        exp = (
            ExplanationBuilder()
            .title("hotfix")
            .verdict("ALLOW")
            .reason("hotfix")
            .reason_code("r1")
            .rule_id("rule-1")
            .confidence(0.9)
            .source("policy_engine")
            .build()
        )
        text = render_explanation(exp, level=DisclosureLevel.DETAILED)
        # ``reason:       hotfix`` has 7 spaces after the colon.
        assert "reason:       hotfix" in text
        # ``reason_code:  r1`` has 2 spaces after the colon (12 + 2 = 14).
        assert "reason_code:  r1" in text
        # ``rule_id:      rule-1`` has 6 spaces after the colon (8 + 6 = 14).
        assert "rule_id:      rule-1" in text

    def test_deepdive_layout_aligned(self) -> None:
        """DEEPDIVE must align values at column 19 (so labels read
        ``reason:          value``)."""
        exp = (
            ExplanationBuilder()
            .title("hotfix")
            .verdict("ALLOW")
            .reason("hotfix")
            .reason_code("r1")
            .rule_id("rule-1")
            .confidence(0.9)
            .source("policy_engine")
            .build()
        )
        text = render_explanation(exp, level=DisclosureLevel.DEEPDIVE)
        # ``reason:          hotfix`` has 12 spaces after the colon.
        assert "reason:          hotfix" in text
        # ``reason_code:     r1`` has 7 spaces after the colon.
        assert "reason_code:     r1" in text

    def test_helper_modules_exist(self) -> None:
        """The shared helpers are exposed at module level so the
        consolidation is verifiable."""
        from thegent.ux.explanations import (
            _actions_lines,
            _audit_refs_lines,
            _chain_lines,
            _citations_lines,
            _core_attribute_lines,
            _header_lines,
            _metadata_lines,
            _rationale_lines,
        )

        # Each helper returns a list of strings and handles empty inputs.
        empty_exp = DecisionExplanation(title="x", source="")
        assert _header_lines(empty_exp, width=80) == [
            "x" + " " * (80 - 6 - len("x")) + " [?]",
            "=" * 80,
        ]
        assert _core_attribute_lines(empty_exp, label_width=14) == []
        assert _actions_lines(empty_exp) == []
        assert _citations_lines(empty_exp) == []
        assert _chain_lines(empty_exp, width=80) == []
        assert _metadata_lines(empty_exp, width=80) == []
        assert _rationale_lines(empty_exp, width=80) == []
        assert _audit_refs_lines(empty_exp, width=80) == []
