"""Spec-only hardening tests for the dormant resilience cluster (SOTA pass-23).

Covers five dormant orchestration modules that share a cluster
(resilience / oversight / probes / deferral / smart_prune) and have
never been audited in the dormant-core chain:

  * ``thegent.orchestration.resilience.circuit_breaker``
    -- ``is_open`` / ``should_allow`` per-circuit TTL'd failure
    counters persisted under ``<root>/.circuits/<circuit_name>.json``
    so a tripped circuit survives across invocations (FR-RES-001).
  * ``thegent.orchestration.resilience.deferral``
    -- ``extract_deferred_tasks`` (regex $defer parser),
    ``inject_deferred_tasks`` (PromptQueue append),
    ``process_output_for_deferrals`` (end-to-end wrapper)
    (FR-RES-002).
  * ``thegent.orchestration.oversight``
    -- ``should_trigger_oversight`` (threshold ladder),
    ``get_oversight_action`` (continue / pause / escalate),
    per-agent persistent state file (FR-RES-003).
  * ``thegent.orchestration.probes``
    -- ``HealthProbe.check()`` returns ``ProbeResult``,
    ``run_pre_promote_probes`` and ``run_post_rollback_probes``
    return ``{passed, findings}`` (FR-RES-004).
  * ``thegent.orchestration.pruning.smart_prune``
    -- Triple-Lock evaluation (``detect_completion``,
    ``check_docs_written``, ``check_triple_lock``),
    protected-process guard (``_is_protected_process``),
    ``run_cycle`` (dry_run / yes / confirmation logic),
    ``smart_prune_main`` (FR-RES-005).
  * ``thegent.orchestration.pruning.prune``
    -- ``mcp_prune(session, pane=...)`` is the actual prune
    side-effect, gated by the protected-process guard
    (FR-RES-006).

This file is the AUDIT-N+39 contract spec (SOTA pass-23). It is
committed first (spec-first pattern, mirrors AUDIT-N+33 / N+34 / N+35
/ N+36 / N+37 / N+38) so the next step is to make every assertion
here pass without breaking any dormant corridor
(``test_unit_orchestration_recovery``,
``test_unit_smart_prune``, ``test_defer_injection``,
``test_shadow_cleanup``) or any other SOTA audit-N+ invariant
cluster.

@trace FR-RES-001 -- ``CircuitBreaker.record_failure(circuit_name)``
                   increments the failure count for the named
                   circuit, persists it under
                   ``<root>/.circuits/<circuit_name>.json`` with
                   an ISO-8601 ``opened_at`` timestamp, and
                   ``is_open(root, circuit_name)`` returns
                   ``True`` once the count crosses the threshold;
                   ``should_allow`` is the inverse of ``is_open``.
@trace FR-RES-002 -- ``extract_deferred_tasks(output)`` parses
                   ``$defer`` / ``$DEFER`` / ``$defer:`` lines,
                   returns ``list[str]`` of the task descriptions
                   in source order, and is case-insensitive.
@trace FR-RES-003 -- ``inject_deferred_tasks(queue, tasks)``
                   appends each task to ``queue`` as
                   ``{"prompt": task, "source": "deferral"}``
                   dicts and returns the queue.
@trace FR-RES-004 -- ``process_output_for_deferrals(output)``
                   calls ``extract_deferred_tasks`` on the output,
                   returns ``{"deferred": [...], "processed":
                   True, "output": output}`` so callers can
                   audit the deferred list without re-parsing.
@trace FR-RES-005 -- ``should_trigger_oversight(path, agent,
                   attempts, threshold=3)`` returns ``True`` when
                   ``attempts >= threshold`` and persists the
                   attempt count under ``<path>/.oversight/<agent>.json``
                   so the next call sees a higher counter.
@trace FR-RES-006 -- ``get_oversight_action(agent, context=None)``
                   returns ``"continue"`` for ``agent < 3``,
                   ``"pause"`` for ``3 <= agent < 5``,
                   ``"escalate"`` for ``agent >= 5``; the action
                   is selected from ``context`` if
                   ``context.get("forced_action")`` is set.
@trace FR-RES-007 -- ``HealthProbe.check()`` returns
                   ``ProbeResult(name, healthy, message)`` where
                   ``healthy`` reflects the result of the probe's
                   internal check; ``is_healthy()`` is the
                   boolean shortcut.
@trace FR-RES-008 -- ``run_pre_promote_probes()`` returns
                   ``{"passed": <bool>, "findings": [ProbeResult.to_dict()]}``
                   and ``run_post_rollback_probes()`` returns the
                   same shape for the post-rollback probe set;
                   both aggregate ``passed = all(r.healthy for r
                   in results)``.
@trace FR-RES-009 -- ``_is_protected_process(name)`` returns
                   ``True`` for any case-insensitive substring
                   match of the protected list
                   (``cursor-agent``, ``claude``, ``codex``,
                   ``droid``, ``thegent``, ``bash``, ``zsh``,
                   ``ghostty``, ``terminal``, ``iterm``) and
                   ``False`` otherwise; an empty string returns
                   ``False``.
@trace FR-RES-010 -- ``SmartPruner.detect_completion(output)``
                   returns ``True`` when the last 1000 chars of
                   ``output`` contain a completion marker
                   (``Task finished``, ``completed successfully``,
                   ``Task complete.``, ``[done]``,
                   ``Migration successful.``, ``Cursor turned
                   off``, etc.) and ``False`` otherwise.
@trace FR-RES-011 -- ``SmartPruner.check_docs_written(start_time,
                   project_root=None)`` returns ``True`` when at
                   least one ``*.md`` file under
                   ``<project_root>/docs/research/`` (or
                   ``<project_root>/docs/``) has ``mtime >=
                   start_time`` and ``False`` otherwise; returns
                   ``False`` when no ``docs/research/`` dir
                   exists.
@trace FR-RES-012 -- ``SmartPruner.check_triple_lock(snap,
                   output, start_time, now)`` returns
                   ``(is_idle, is_complete, docs_written)`` where
                   ``is_idle = snap.idle_count >= IDLE_COUNT_THRESHOLD``,
                   ``is_complete = self.detect_completion(output)``,
                   ``docs_written = self.check_docs_written(start_time)``.
@trace FR-RES-013 -- ``SmartPruner.run_cycle(force_prune=False,
                   reprompt=False, dry_run=False, yes=False)``
                   returns ``{"pruned": int, "kept": int,
                   "dry_run": bool}``; protected-agent sessions
                   (matched via ``_is_protected_process``) are
                   skipped and counted under ``kept``; dry_run
                   and !yes paths never call
                   ``mcp_prune(...)``.
@trace FR-RES-014 -- ``smart_prune_main(force, reprompt, dry_run,
                   yes)`` returns the same dict shape and
                   delegates to ``SmartPruner.run_cycle``;
                   ``pruned = 0`` when ``ps_impl`` returns an
                   empty list.
@trace FR-RES-015 -- ``mcp_prune(session, pane=None)`` from
                   ``thegent.orchestration.pruning.prune`` is
                   the actual side-effect; ``SmartPruner._prune_session``
                   is the only legitimate caller and it must
                   re-check the protected-process guard before
                   invoking ``mcp_prune``.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from thegent.orchestration.oversight import (
    get_oversight_action,
    record_oversight_event,
    should_trigger_oversight,
)
from thegent.orchestration.probes import (
    HealthProbe,
    ProbeResult,
    run_post_rollback_probes,
    run_pre_promote_probes,
)
from thegent.orchestration.pruning.prune import mcp_prune
from thegent.orchestration.pruning.smart_prune import (
    IDLE_COUNT_THRESHOLD,
    SessionSnapshot,
    SmartPruner,
    _is_protected_process,
    smart_prune_main,
)
from thegent.orchestration.resilience.circuit_breaker import (
    is_open,
    record_failure,
    record_success,
    should_allow,
)
from thegent.orchestration.resilience.deferral import (
    extract_deferred_tasks,
    inject_deferred_tasks,
    process_output_for_deferrals,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# circuit_breaker
# ---------------------------------------------------------------------------


class TestCircuitBreakerState:
    """FR-RES-001 -- per-circuit TTL'd failure counters persisted to disk."""

    def test_is_open_initially_false(self, tmp_path: Path) -> None:
        assert is_open(tmp_path, "agent-x") is False

    def test_should_allow_when_closed(self, tmp_path: Path) -> None:
        assert should_allow(tmp_path, "agent-x") is True

    def test_record_failure_opens_after_threshold(self, tmp_path: Path) -> None:
        for _ in range(3):
            record_failure(tmp_path, "agent-x", threshold=3)
        assert is_open(tmp_path, "agent-x") is True
        assert should_allow(tmp_path, "agent-x") is False

    def test_record_failure_persists_to_disk(self, tmp_path: Path) -> None:
        record_failure(tmp_path, "agent-x", threshold=1)
        state_file = tmp_path / ".circuits" / "agent-x.json"
        assert state_file.exists(), "Circuit state must be persisted to .circuits/"
        state = json.loads(state_file.read_text())
        assert state["count"] >= 1
        assert "opened_at" in state

    def test_record_success_resets_counter(self, tmp_path: Path) -> None:
        for _ in range(2):
            record_failure(tmp_path, "agent-x", threshold=3)
        record_success(tmp_path, "agent-x")
        assert is_open(tmp_path, "agent-x") is False

    def test_independent_circuits(self, tmp_path: Path) -> None:
        record_failure(tmp_path, "agent-a", threshold=1)
        assert is_open(tmp_path, "agent-a") is True
        assert is_open(tmp_path, "agent-b") is False


# ---------------------------------------------------------------------------
# deferral
# ---------------------------------------------------------------------------


class TestExtractDeferredTasks:
    """FR-RES-002 -- $defer / $DEFER / $defer: parsing."""

    def test_single_defer(self) -> None:
        out = "Some output\n$defer Implement WL-039\nMore"
        assert extract_deferred_tasks(out) == ["Implement WL-039"]

    def test_multiple_defers_in_order(self) -> None:
        out = "$defer Task one\nx\n$defer Task two\n$defer Task three"
        assert extract_deferred_tasks(out) == [
            "Task one",
            "Task two",
            "Task three",
        ]

    def test_case_insensitive(self) -> None:
        out = "$DEFER Upper\n$Defer Mixed"
        tasks = extract_deferred_tasks(out)
        assert "Upper" in tasks
        assert "Mixed" in tasks
        assert len(tasks) == 2

    def test_colon_variant(self) -> None:
        out = "$defer: Run ruff check"
        assert extract_deferred_tasks(out) == ["Run ruff check"]

    def test_no_defers(self) -> None:
        assert extract_deferred_tasks("Just text\nNo deferral here.") == []

    def test_empty_input(self) -> None:
        assert extract_deferred_tasks("") == []


class TestInjectDeferredTasks:
    """FR-RES-003 -- PromptQueue append."""

    def test_injects_into_queue(self) -> None:
        from thegent.queue.storage import PromptQueue

        queue: PromptQueue = PromptQueue()
        inject_deferred_tasks(queue, ["Task A", "Task B"])
        assert queue.size() == 2
        first = queue.peek()
        assert first is not None
        assert first["prompt"] == "Task A"
        assert first["source"] == "deferral"

    def test_returns_queue(self) -> None:
        from thegent.queue.storage import PromptQueue

        queue: PromptQueue = PromptQueue()
        result = inject_deferred_tasks(queue, ["X"])
        assert result is queue


class TestProcessOutputForDeferrals:
    """FR-RES-004 -- end-to-end wrapper."""

    def test_returns_dict_shape(self) -> None:
        out = "$defer Do thing"
        result = process_output_for_deferrals(out)
        assert result["processed"] is True
        assert result["output"] == out
        assert result["deferred"] == ["Do thing"]

    def test_no_defers(self) -> None:
        result = process_output_for_deferrals("plain text")
        assert result["deferred"] == []
        assert result["processed"] is True


# ---------------------------------------------------------------------------
# oversight
# ---------------------------------------------------------------------------


class TestShouldTriggerOversight:
    """FR-RES-005 -- threshold ladder."""

    def test_below_threshold(self, tmp_path: Path) -> None:
        assert should_trigger_oversight(tmp_path, "agent-a", 2, threshold=3) is False

    def test_at_threshold(self, tmp_path: Path) -> None:
        assert should_trigger_oversight(tmp_path, "agent-a", 3, threshold=3) is True

    def test_above_threshold(self, tmp_path: Path) -> None:
        assert should_trigger_oversight(tmp_path, "agent-a", 5, threshold=3) is True

    def test_persists_event(self, tmp_path: Path) -> None:
        record_oversight_event(tmp_path, "agent-a", attempts=2)
        event_file = tmp_path / ".oversight" / "agent-a.json"
        assert event_file.exists()
        state = json.loads(event_file.read_text())
        assert state["attempts"] == 2


class TestGetOversightAction:
    """FR-RES-006 -- continue / pause / escalate ladder."""

    def test_continue_low(self) -> None:
        assert get_oversight_action(1) == "continue"
        assert get_oversight_action(2) == "continue"

    def test_pause_mid(self) -> None:
        assert get_oversight_action(3) == "pause"
        assert get_oversight_action(4) == "pause"

    def test_escalate_high(self) -> None:
        assert get_oversight_action(5) == "escalate"
        assert get_oversight_action(10) == "escalate"

    def test_forced_action_from_context(self) -> None:
        assert get_oversight_action(1, context={"forced_action": "escalate"}) == "escalate"


# ---------------------------------------------------------------------------
# probes
# ---------------------------------------------------------------------------


class TestHealthProbe:
    """FR-RES-007 -- HealthProbe.check() returns ProbeResult."""

    def test_default_probe_is_healthy(self) -> None:
        probe = HealthProbe("db")
        result = probe.check()
        assert isinstance(result, ProbeResult)
        assert result.name == "db"
        assert result.healthy is True

    def test_probe_can_be_unhealthy(self) -> None:
        probe = HealthProbe("db", healthy=False)
        assert probe.is_healthy() is False

    def test_probe_result_to_dict(self) -> None:
        result = ProbeResult("db", True, "ok")
        d = result.to_dict()
        assert d["name"] == "db"
        assert d["healthy"] is True
        assert d["message"] == "ok"


class TestProbeRunners:
    """FR-RES-008 -- run_pre_promote_probes / run_post_rollback_probes."""

    def test_pre_promote_returns_shape(self, tmp_path: Path) -> None:
        result = run_pre_promote_probes(tmp_path)
        assert "passed" in result
        assert "findings" in result
        assert isinstance(result["findings"], list)

    def test_post_rollback_returns_shape(self, tmp_path: Path) -> None:
        result = run_post_rollback_probes(tmp_path)
        assert "passed" in result
        assert "findings" in result
        assert isinstance(result["findings"], list)

    def test_findings_are_dicts(self, tmp_path: Path) -> None:
        result = run_pre_promote_probes(tmp_path)
        for finding in result["findings"]:
            assert isinstance(finding, dict)
            assert "name" in finding
            assert "healthy" in finding


# ---------------------------------------------------------------------------
# smart_prune -- _is_protected_process
# ---------------------------------------------------------------------------


class TestIsProtectedProcess:
    """FR-RES-009 -- protected process guard."""

    @pytest.mark.parametrize(
        "name",
        [
            "cursor-agent",
            "thegent",
            "claude",
            "codex",
            "droid",
            "bash",
            "zsh",
            "ghostty",
            "terminal",
            "iterm",
            "/usr/bin/zsh",
            "/Applications/Ghostty.app/Contents/MacOS/ghostty",
            "CURSOR-AGENT",  # case insensitive
            "BASH",
            "ZSH",
        ],
    )
    def test_protected_names(self, name: str) -> None:
        assert _is_protected_process(name) is True, f"{name!r} must be protected"

    @pytest.mark.parametrize(
        "name",
        ["node", "npm", "python3", "uvicorn", "", "@playwright/mcp"],
    )
    def test_non_protected(self, name: str) -> None:
        assert _is_protected_process(name) is False


# ---------------------------------------------------------------------------
# smart_prune -- Triple-Lock evaluation
# ---------------------------------------------------------------------------


class TestSmartPrunerTripleLock:
    """FR-RES-010 / FR-RES-011 / FR-RES-012."""

    def _make_pruner(self, tmp_path: Path) -> SmartPruner:
        with patch("thegent.orchestration.pruning.smart_prune.ThegentSettings"):
            pruner = SmartPruner.__new__(SmartPruner)
            pruner.settings = MagicMock()
            pruner.project_root = tmp_path
            pruner.state_file = tmp_path / "state.json"
            pruner.snapshots = {}
        return pruner

    @pytest.mark.parametrize(
        "output",
        [
            "...\nTask finished\n",
            "...\ncompleted successfully\n",
            "...\nTask complete.\n",
            "...\n[done]\n",
            "...\nMigration successful.\n",
            "...\nCursor turned off\n",
        ],
    )
    def test_detect_completion_markers(self, output: str, tmp_path: Path) -> None:
        pruner = self._make_pruner(tmp_path)
        assert pruner.detect_completion(output) is True

    def test_detect_completion_no_marker(self, tmp_path: Path) -> None:
        pruner = self._make_pruner(tmp_path)
        assert pruner.detect_completion("Still working...") is False

    def test_detect_completion_only_in_last_1000(self, tmp_path: Path) -> None:
        pruner = self._make_pruner(tmp_path)
        long_prefix = "A" * 2000
        assert pruner.detect_completion(long_prefix + " nothing here") is False
        assert pruner.detect_completion(long_prefix + " Task finished") is True

    def test_check_docs_written_true_when_newer(self, tmp_path: Path) -> None:
        pruner = self._make_pruner(tmp_path)
        research = tmp_path / "docs" / "research"
        research.mkdir(parents=True)
        (research / "dump.md").write_text("# Done")
        assert pruner.check_docs_written(time.time() - 10) is True

    def test_check_docs_written_false_when_older(self, tmp_path: Path) -> None:
        pruner = self._make_pruner(tmp_path)
        research = tmp_path / "docs" / "research"
        research.mkdir(parents=True)
        (research / "OLD.md").write_text("# Old")
        assert pruner.check_docs_written(time.time() + 9999) is False

    def test_check_docs_written_no_dir(self, tmp_path: Path) -> None:
        pruner = self._make_pruner(tmp_path)
        assert pruner.check_docs_written(time.time() - 10) is False

    def test_check_triple_lock_all_pass(self, tmp_path: Path) -> None:
        pruner = self._make_pruner(tmp_path)
        research = tmp_path / "docs" / "research"
        research.mkdir(parents=True)
        (research / "dump.md").write_text("done")
        snap = SessionSnapshot(
            session_id="s1",
            last_output="Task finished\n",
            last_check_time=time.time(),
            idle_count=IDLE_COUNT_THRESHOLD,
        )
        is_idle, is_complete, docs = pruner.check_triple_lock(snap, "Task finished\n", time.time() - 10, time.time())
        assert is_idle is True
        assert is_complete is True
        assert docs is True


# ---------------------------------------------------------------------------
# smart_prune -- run_cycle
# ---------------------------------------------------------------------------


class TestSmartPrunerRunCycle:
    """FR-RES-013 / FR-RES-014 / FR-RES-015."""

    def _make_pruner_with_session(
        self,
        tmp_path: Path,
        *,
        agent: str = "lsp-worker",
        idle_count: int = IDLE_COUNT_THRESHOLD + 1,
    ) -> tuple[SmartPruner, dict[str, Any]]:
        research = tmp_path / "docs" / "research"
        research.mkdir(parents=True)
        (research / "dump.md").write_text("done")

        with patch("thegent.orchestration.pruning.smart_prune.ThegentSettings"):
            pruner = SmartPruner.__new__(SmartPruner)
            pruner.settings = MagicMock(platform="linux")
            pruner.project_root = tmp_path
            pruner.state_file = tmp_path / "state.json"
            pruner.snapshots = {}

        session: dict[str, Any] = {
            "id": "sess-1",
            "pid": 9999,
            "agent": agent,
            "status": "running",
            "started_at_utc": None,
            "tty": "",
            "source": "other",
        }
        pruner.snapshots["sess-1"] = SessionSnapshot(
            session_id="sess-1",
            last_output="Task finished\n",
            last_check_time=time.time() - 90,
            idle_count=idle_count,
        )
        return pruner, session

    def test_dry_run_does_not_kill(self, tmp_path: Path) -> None:
        pruner, session = self._make_pruner_with_session(tmp_path)
        with (
            patch.object(pruner, "_prune_session") as mock_prune,
            patch("thegent.orchestration.pruning.smart_prune.ps_impl", return_value=[session]),
            patch("thegent.orchestration.pruning.smart_prune.list_tmux_panes", return_value=[]),
            patch(
                "thegent.orchestration.pruning.smart_prune.capture_tmux_pane",
                return_value="Task finished\n",
            ),
        ):
            results = pruner.run_cycle(force_prune=True, dry_run=True, yes=True)
        mock_prune.assert_not_called()
        assert results["dry_run"] is True

    def test_no_yes_does_not_kill(self, tmp_path: Path) -> None:
        pruner, session = self._make_pruner_with_session(tmp_path)
        with (
            patch.object(pruner, "_prune_session") as mock_prune,
            patch("thegent.orchestration.pruning.smart_prune.ps_impl", return_value=[session]),
            patch("thegent.orchestration.pruning.smart_prune.list_tmux_panes", return_value=[]),
            patch(
                "thegent.orchestration.pruning.smart_prune.capture_tmux_pane",
                return_value="Task finished\n",
            ),
        ):
            results = pruner.run_cycle(force_prune=True, dry_run=False, yes=False)
        mock_prune.assert_not_called()
        assert results["pruned"] == 0

    def test_force_and_yes_kills(self, tmp_path: Path) -> None:
        pruner, session = self._make_pruner_with_session(tmp_path)
        with (
            patch.object(pruner, "_prune_session") as mock_prune,
            patch("thegent.orchestration.pruning.smart_prune.ps_impl", return_value=[session]),
            patch("thegent.orchestration.pruning.smart_prune.list_tmux_panes", return_value=[]),
            patch(
                "thegent.orchestration.pruning.smart_prune.capture_tmux_pane",
                return_value="Task finished\n",
            ),
        ):
            results = pruner.run_cycle(force_prune=True, dry_run=False, yes=True)
        mock_prune.assert_called_once()
        assert results["pruned"] == 1

    @pytest.mark.parametrize("agent", ["cursor-agent", "claude", "codex", "droid", "thegent", "bash"])
    def test_protected_agent_skipped(self, agent: str, tmp_path: Path) -> None:
        pruner, session = self._make_pruner_with_session(tmp_path, agent=agent)
        with (
            patch.object(pruner, "_prune_session") as mock_prune,
            patch("thegent.orchestration.pruning.smart_prune.ps_impl", return_value=[session]),
            patch("thegent.orchestration.pruning.smart_prune.list_tmux_panes", return_value=[]),
        ):
            results = pruner.run_cycle(force_prune=True, dry_run=False, yes=True)
        mock_prune.assert_not_called()
        assert results["pruned"] == 0
        assert results["kept"] == 1

    def test_no_sessions_no_kills(self, tmp_path: Path) -> None:
        results = smart_prune_main(force=True, reprompt=False, dry_run=False, yes=True)
        assert results["pruned"] == 0

    def test_smart_prune_main_dry_run_shape(self) -> None:
        results = smart_prune_main(force=False, reprompt=False, dry_run=True, yes=False)
        assert "pruned" in results
        assert "kept" in results
        assert results["dry_run"] is True


# ---------------------------------------------------------------------------
# pruning.prune -- mcp_prune
# ---------------------------------------------------------------------------


class TestMcpPrune:
    """FR-RES-015 -- mcp_prune is the actual side-effect."""

    def test_mcp_prune_returns_dict(self) -> None:
        session = {
            "id": "s1",
            "pid": 1234,
            "agent": "lsp-worker",
            "status": "running",
            "tty": "",
            "source": "other",
        }
        result = mcp_prune(session, pane=None)
        assert isinstance(result, dict)
        assert "pruned" in result or "removed" in result or "status" in result
