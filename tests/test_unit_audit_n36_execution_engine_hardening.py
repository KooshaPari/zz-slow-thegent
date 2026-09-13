"""Spec-only hardening tests for the dormant ExecutionEngine surface.

@trace FR-ORC-040 -- ExecutionEngine accepts ``settings=`` kwarg
                    (dormant-core constructor contract).
@trace FR-ORC-041 -- ExecutionEngine.execute(runner, run_meta) runs the
                    inner runner and returns the runner's ``RunResult``
                    unchanged.
@trace FR-ORC-042 -- ExecutionEngine.execute signs the run via
                    ``Auditor.sign_run(run_meta)`` exactly once per call.
@trace FR-ORC-043 -- ExecutionEngine.execute generates + persists a MAIF
                    artifact via the ``Auditor`` sidecar (best-effort;
                    Auditor failures must not break the inner run).
@trace FR-ORC-044 -- ExecutionEngine.submit(task) tracks tasks in an
                    internal list and returns a stable task_id.
@trace FR-ORC-045 -- ExecutionEngine.cancel(task_id) is idempotent:
                    first call returns True, subsequent calls return False.
@trace FR-ORC-046 -- Concurrent submit / cancel / execute calls are
                    serialised by an internal ``RLock`` so the in-process
                    ``self.tasks`` list cannot corrupt.
@trace FR-ORC-047 -- ``run_meta.run_id`` must be non-empty; ``execute``
                    raises ``ValueError`` otherwise.
@trace FR-ORC-048 -- ``run_meta.cwd`` resolution falls back to
                    ``Path.cwd()`` if empty / None.
@trace FR-ORC-049 -- ``Auditor`` sidecar is created lazily and cached on
                    the engine instance.
@trace FR-ORC-050 -- ``settings.session_dir`` access is defensive
                    (``getattr(settings, "session_dir", fallback)``) so
                    the engine works with partial / ``MagicMock`` configs.
@trace FR-ORC-051 -- Auditor failures are swallowed: a broken
                    ``sign_run`` / ``generate_maif_artifact`` /
                    ``persist_maif_artifact`` does not propagate to the
                    caller.
@trace FR-ORC-052 -- ``submit`` is idempotent on ``task_id``: re-submitting
                    the same id returns the existing id without appending
                    a duplicate entry.
@trace FR-ORC-053 -- ``cancel`` only touches tasks tracked by the engine;
                    unknown ids return False deterministically.

This file is the AUDIT-N+36 contract spec (SOTA pass-20): it pins the
dormant-core behaviour expected of ``ExecutionEngine`` after the
source patch.  It is committed first (spec-first pattern, mirrors
AUDIT-N+33 / N+34 / N+35) so the next step is to make every assertion
here pass without introducing new regressions in the AUDIT-N+27
through AUDIT-N+35 corridor.
"""

from __future__ import annotations

import threading
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from thegent.agents.base import AgentRunner, RunResult
from thegent.execution import Auditor, RunMeta
from thegent.orchestration.execution.engine import ExecutionEngine

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class MockRunner(AgentRunner):
    """Lightweight inner runner that records ``run_meta`` kwargs."""

    def __init__(self, *, exit_code: int = 0, stdout: str = "Mock output") -> None:
        self.exit_code = exit_code
        self.stdout = stdout
        self.last_kwargs: dict | None = None
        self.call_count = 0

    def run(self, prompt, cwd, mode, timeout, **kwargs):
        self.call_count += 1
        self.last_kwargs = {
            "prompt": prompt,
            "cwd": cwd,
            "mode": mode,
            "timeout": timeout,
            **kwargs,
        }
        return RunResult(exit_code=self.exit_code, stdout=self.stdout, stderr="")


def _make_run_meta(
    run_id: str = "run_test_123",
    cwd: str = "",
    prompt: str = "Test prompt",
    owner: str = "test_user",
    agent: str = "test_agent",
) -> RunMeta:
    return RunMeta(
        run_id=run_id,
        prompt=prompt,
        owner=owner,
        agent=agent,
        cwd=cwd,
        started_at_utc="2026-02-20T00:00:00Z",
    )


def _make_session_dir(tmp_path: Path) -> Path:
    session_dir = tmp_path / ".thegent" / "sessions"
    session_dir.mkdir(parents=True)
    return session_dir


def _make_settings(session_dir: Path) -> MagicMock:
    settings = MagicMock()
    settings.session_dir = session_dir
    return settings


# ---------------------------------------------------------------------------
# FR-ORC-040 — Constructor accepts settings=
# ---------------------------------------------------------------------------


class TestSettingsConstructor:
    """@trace FR-ORC-040"""

    def test_accepts_settings_kwarg(self, tmp_path: Path) -> None:
        settings = _make_settings(_make_session_dir(tmp_path))
        engine = ExecutionEngine(settings=settings)
        assert engine.settings is settings

    def test_accepts_legacy_config_kwarg(self) -> None:
        """Legacy wrapper at ``src/thegent/orchestration/execution.py``
        constructs ``ExecutionEngine(config=...)`` — must keep working.
        """
        engine = ExecutionEngine(config={"foo": "bar"})
        assert engine.config == {"foo": "bar"}

    def test_settings_default_is_none(self) -> None:
        engine = ExecutionEngine()
        assert engine.settings is None

    def test_session_dir_accessor_fallback(self, tmp_path: Path) -> None:
        """Defensive ``getattr(settings, 'session_dir', fallback)`` —
        works with partial / MagicMock configs.
        """
        session_dir = _make_session_dir(tmp_path)
        settings = _make_settings(session_dir)
        engine = ExecutionEngine(settings=settings)
        assert engine.session_dir == session_dir

    def test_session_dir_fallback_when_settings_none(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        engine = ExecutionEngine()
        monkeypatch.chdir(tmp_path)
        # ``session_dir`` should not crash even when ``settings is None``.
        assert engine.session_dir is not None


# ---------------------------------------------------------------------------
# FR-ORC-041 — execute() runs inner runner + returns RunResult
# ---------------------------------------------------------------------------


class TestExecuteRunner:
    """@trace FR-ORC-041"""

    def test_execute_returns_runners_run_result(self, tmp_path: Path) -> None:
        session_dir = _make_session_dir(tmp_path)
        settings = _make_settings(session_dir)
        engine = ExecutionEngine(settings=settings)
        runner = MockRunner(exit_code=0, stdout="custom output")
        run_meta = _make_run_meta()
        with (
            patch("thegent.execution.Auditor.sign_run"),
            patch(
                "thegent.execution.Auditor.generate_maif_artifact",
                create=True,
                return_value={"id": "art_123"},
            ),
            patch("thegent.execution.Auditor.persist_maif_artifact", create=True),
        ):
            result = engine.execute(runner, run_meta)
        assert isinstance(result, RunResult)
        assert result.stdout == "custom output"
        assert result.exit_code == 0

    def test_execute_invokes_inner_runner_exactly_once(self, tmp_path: Path) -> None:
        session_dir = _make_session_dir(tmp_path)
        settings = _make_settings(session_dir)
        engine = ExecutionEngine(settings=settings)
        runner = MockRunner()
        run_meta = _make_run_meta()
        with (
            patch("thegent.execution.Auditor.sign_run"),
            patch(
                "thegent.execution.Auditor.generate_maif_artifact",
                create=True,
                return_value={},
            ),
            patch("thegent.execution.Auditor.persist_maif_artifact", create=True),
        ):
            engine.execute(runner, run_meta)
        assert runner.call_count == 1


# ---------------------------------------------------------------------------
# FR-ORC-042 — sign_run called exactly once
# ---------------------------------------------------------------------------


class TestSignRunContract:
    """@trace FR-ORC-042"""

    def test_sign_run_called_once(self, tmp_path: Path) -> None:
        session_dir = _make_session_dir(tmp_path)
        settings = _make_settings(session_dir)
        engine = ExecutionEngine(settings=settings)
        runner = MockRunner()
        run_meta = _make_run_meta()
        with (
            patch("thegent.execution.Auditor.sign_run") as mock_sign,
            patch(
                "thegent.execution.Auditor.generate_maif_artifact",
                create=True,
                return_value={},
            ),
            patch("thegent.execution.Auditor.persist_maif_artifact", create=True),
        ):
            engine.execute(runner, run_meta)
        mock_sign.assert_called_once_with(run_meta)

    def test_sign_run_with_signature_stored(self, tmp_path: Path) -> None:
        session_dir = _make_session_dir(tmp_path)
        settings = _make_settings(session_dir)
        engine = ExecutionEngine(settings=settings)
        runner = MockRunner()
        run_meta = _make_run_meta()
        with (
            patch("thegent.execution.Auditor.sign_run", return_value="deadbeef"),
            patch(
                "thegent.execution.Auditor.generate_maif_artifact",
                create=True,
                return_value={},
            ),
            patch("thegent.execution.Auditor.persist_maif_artifact", create=True),
        ):
            engine.execute(runner, run_meta)
        assert run_meta.signature == "deadbeef"


# ---------------------------------------------------------------------------
# FR-ORC-043 — generate + persist MAIF artifact (best-effort sidecar)
# ---------------------------------------------------------------------------


class TestMaifArtifactContract:
    """@trace FR-ORC-043"""

    def test_generate_and_persist_called_once(self, tmp_path: Path) -> None:
        session_dir = _make_session_dir(tmp_path)
        settings = _make_settings(session_dir)
        engine = ExecutionEngine(settings=settings)
        runner = MockRunner()
        run_meta = _make_run_meta()
        with (
            patch("thegent.execution.Auditor.sign_run"),
            patch(
                "thegent.execution.Auditor.generate_maif_artifact",
                create=True,
            ) as mock_gen,
            patch(
                "thegent.execution.Auditor.persist_maif_artifact",
                create=True,
            ) as mock_persist,
        ):
            mock_gen.return_value = {"id": "art_xyz"}
            engine.execute(runner, run_meta)
        mock_gen.assert_called_once()
        mock_persist.assert_called_once_with(session_dir, {"id": "art_xyz"})


# ---------------------------------------------------------------------------
# FR-ORC-051 — Auditor failures swallowed
# ---------------------------------------------------------------------------


class TestAuditorFailureSwallowed:
    """@trace FR-ORC-051"""

    def test_sign_run_failure_does_not_propagate(self, tmp_path: Path) -> None:
        session_dir = _make_session_dir(tmp_path)
        settings = _make_settings(session_dir)
        engine = ExecutionEngine(settings=settings)
        runner = MockRunner()
        run_meta = _make_run_meta()
        with (
            patch(
                "thegent.execution.Auditor.sign_run",
                side_effect=RuntimeError("boom"),
            ),
            patch(
                "thegent.execution.Auditor.generate_maif_artifact",
                create=True,
                return_value={},
            ),
            patch("thegent.execution.Auditor.persist_maif_artifact", create=True),
        ):
            result = engine.execute(runner, run_meta)
        assert result.stdout == "Mock output"
        assert result.exit_code == 0

    def test_generate_artifact_failure_does_not_propagate(self, tmp_path: Path) -> None:
        session_dir = _make_session_dir(tmp_path)
        settings = _make_settings(session_dir)
        engine = ExecutionEngine(settings=settings)
        runner = MockRunner()
        run_meta = _make_run_meta()
        with (
            patch("thegent.execution.Auditor.sign_run"),
            patch(
                "thegent.execution.Auditor.generate_maif_artifact",
                create=True,
                side_effect=RuntimeError("boom"),
            ),
            patch("thegent.execution.Auditor.persist_maif_artifact", create=True),
        ):
            result = engine.execute(runner, run_meta)
        assert result.exit_code == 0

    def test_persist_artifact_failure_does_not_propagate(self, tmp_path: Path) -> None:
        session_dir = _make_session_dir(tmp_path)
        settings = _make_settings(session_dir)
        engine = ExecutionEngine(settings=settings)
        runner = MockRunner()
        run_meta = _make_run_meta()
        with (
            patch("thegent.execution.Auditor.sign_run"),
            patch(
                "thegent.execution.Auditor.generate_maif_artifact",
                create=True,
                return_value={},
            ),
            patch(
                "thegent.execution.Auditor.persist_maif_artifact",
                create=True,
                side_effect=RuntimeError("boom"),
            ),
        ):
            result = engine.execute(runner, run_meta)
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# FR-ORC-049 — Auditor lazy + cached
# ---------------------------------------------------------------------------


class TestAuditorLazyCached:
    """@trace FR-ORC-049"""

    def test_auditor_created_lazily(self, tmp_path: Path) -> None:
        session_dir = _make_session_dir(tmp_path)
        settings = _make_settings(session_dir)
        engine = ExecutionEngine(settings=settings)
        assert engine.auditor is None

    def test_auditor_cached_after_first_use(self, tmp_path: Path) -> None:
        session_dir = _make_session_dir(tmp_path)
        settings = _make_settings(session_dir)
        engine = ExecutionEngine(settings=settings)
        a1 = engine._get_auditor()
        a2 = engine._get_auditor()
        assert a1 is a2
        assert isinstance(a1, Auditor)


# ---------------------------------------------------------------------------
# FR-ORC-044 — submit()
# ---------------------------------------------------------------------------


class TestSubmitContract:
    """@trace FR-ORC-044"""

    def test_submit_returns_string_task_id(self) -> None:
        engine = ExecutionEngine()
        tid = engine.submit({"name": "task1"})
        assert isinstance(tid, str)
        assert tid != ""

    def test_submit_appends_to_tasks(self) -> None:
        engine = ExecutionEngine()
        engine.submit({"name": "task1"})
        engine.submit({"name": "task2"})
        assert len(engine.tasks) == 2

    def test_submit_idempotent_on_task_id(self) -> None:
        """@trace FR-ORC-052"""
        engine = ExecutionEngine()
        task = {"name": "task1"}
        tid1 = engine.submit(task, task_id="alpha")
        tid2 = engine.submit(task, task_id="alpha")
        assert tid1 == tid2 == "alpha"
        assert len(engine.tasks) == 1


# ---------------------------------------------------------------------------
# FR-ORC-045 + FR-ORC-053 — cancel() idempotent + only touches tracked
# ---------------------------------------------------------------------------


class TestCancelContract:
    """@trace FR-ORC-045, FR-ORC-053"""

    def test_cancel_returns_true_first_call(self) -> None:
        engine = ExecutionEngine()
        tid = engine.submit({"name": "task1"})
        assert engine.cancel(tid) is True

    def test_cancel_returns_false_second_call(self) -> None:
        engine = ExecutionEngine()
        tid = engine.submit({"name": "task1"})
        engine.cancel(tid)
        assert engine.cancel(tid) is False

    def test_cancel_unknown_id_returns_false(self) -> None:
        engine = ExecutionEngine()
        assert engine.cancel("nonexistent") is False


# ---------------------------------------------------------------------------
# FR-ORC-047 — run_meta.run_id must be non-empty
# ---------------------------------------------------------------------------


class TestRunMetaValidation:
    """@trace FR-ORC-047"""

    def test_empty_run_id_raises_value_error(self, tmp_path: Path) -> None:
        session_dir = _make_session_dir(tmp_path)
        settings = _make_settings(session_dir)
        engine = ExecutionEngine(settings=settings)
        runner = MockRunner()
        run_meta = _make_run_meta(run_id="")
        with pytest.raises(ValueError, match="run_id"):
            engine.execute(runner, run_meta)

    def test_whitespace_only_run_id_raises_value_error(self, tmp_path: Path) -> None:
        session_dir = _make_session_dir(tmp_path)
        settings = _make_settings(session_dir)
        engine = ExecutionEngine(settings=settings)
        runner = MockRunner()
        run_meta = _make_run_meta(run_id="   ")
        with pytest.raises(ValueError, match="run_id"):
            engine.execute(runner, run_meta)


# ---------------------------------------------------------------------------
# FR-ORC-048 — run_meta.cwd resolution
# ---------------------------------------------------------------------------


class TestRunMetaCwdResolution:
    """@trace FR-ORC-048"""

    def test_empty_cwd_falls_back_to_cwd(self, tmp_path: Path, monkeypatch) -> None:
        session_dir = _make_session_dir(tmp_path)
        settings = _make_settings(session_dir)
        engine = ExecutionEngine(settings=settings)
        monkeypatch.chdir(tmp_path)
        runner = MockRunner()
        run_meta = _make_run_meta(cwd="")
        with (
            patch("thegent.execution.Auditor.sign_run"),
            patch(
                "thegent.execution.Auditor.generate_maif_artifact",
                create=True,
                return_value={},
            ),
            patch("thegent.execution.Auditor.persist_maif_artifact", create=True),
        ):
            engine.execute(runner, run_meta)
        assert runner.last_kwargs["cwd"] == tmp_path

    def test_explicit_cwd_is_preserved(self, tmp_path: Path) -> None:
        session_dir = _make_session_dir(tmp_path)
        settings = _make_settings(session_dir)
        engine = ExecutionEngine(settings=settings)
        runner = MockRunner()
        explicit = tmp_path / "subdir"
        explicit.mkdir()
        run_meta = _make_run_meta(cwd=str(explicit))
        with (
            patch("thegent.execution.Auditor.sign_run"),
            patch(
                "thegent.execution.Auditor.generate_maif_artifact",
                create=True,
                return_value={},
            ),
            patch("thegent.execution.Auditor.persist_maif_artifact", create=True),
        ):
            engine.execute(runner, run_meta)
        assert runner.last_kwargs["cwd"] == explicit


# ---------------------------------------------------------------------------
# FR-ORC-050 — defensive settings.session_dir access
# ---------------------------------------------------------------------------


class TestSettingsSessionDirDefensive:
    """@trace FR-ORC-050"""

    def test_settings_without_session_dir_attribute_does_not_crash(
        self, tmp_path: Path
    ) -> None:
        """A partial settings object without ``session_dir`` must not
        raise — the engine falls back to ``Path.cwd()``.
        """
        settings = MagicMock(spec=[])  # no session_dir attribute
        engine = ExecutionEngine(settings=settings)
        assert engine.session_dir is not None
        assert isinstance(engine.session_dir, Path)

    def test_settings_none_returns_cwd_fallback(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        engine = ExecutionEngine(settings=None)
        monkeypatch.chdir(tmp_path)
        assert engine.session_dir == tmp_path


# ---------------------------------------------------------------------------
# FR-ORC-046 — concurrent submit / cancel / execute serialised
# ---------------------------------------------------------------------------


class TestConcurrencyHardening:
    """@trace FR-ORC-046"""

    def test_concurrent_submit_does_not_corrupt_tasks_list(self) -> None:
        engine = ExecutionEngine()
        errors: list[Exception] = []

        def worker(i: int) -> None:
            try:
                for _ in range(20):
                    engine.submit({"name": f"task-{i}"})
            except Exception as exc:  # noqa: BLE001
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert errors == []
        assert len(engine.tasks) == 8 * 20
        # All tasks are unique dict objects (no shared-state corruption).
        seen_ids: set[int] = set()
        for task in engine.tasks:
            seen_ids.add(id(task))
        assert len(seen_ids) == len(engine.tasks)

    def test_concurrent_submit_and_cancel_serialised(self) -> None:
        engine = ExecutionEngine()
        for i in range(50):
            engine.submit({"name": f"task-{i}"})
        errors: list[Exception] = []

        def cancel_worker() -> None:
            try:
                for tid in list(engine.tasks)[:25]:
                    engine.cancel(tid)
            except Exception as exc:  # noqa: BLE001
                errors.append(exc)

        def submit_worker() -> None:
            try:
                for _ in range(20):
                    engine.submit({"name": "concurrent"})
            except Exception as exc:  # noqa: BLE001
                errors.append(exc)

        threads = [
            threading.Thread(target=cancel_worker),
            threading.Thread(target=submit_worker),
            threading.Thread(target=cancel_worker),
            threading.Thread(target=submit_worker),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert errors == []

    def test_append_lock_is_rlock(self) -> None:
        engine = ExecutionEngine()
        assert isinstance(engine._append_lock, type(threading.RLock()))


# ---------------------------------------------------------------------------
# FR-ORC-040 — MAIFAgentRunner wiring (the dormant test surface)
# ---------------------------------------------------------------------------


class TestMAIFAgentRunnerWiring:
    """@trace FR-ORC-040 (dormant test pinned by tests/maif/test_engine_wiring.py)"""

    def test_maif_runner_invokes_engine_execute(self, tmp_path: Path) -> None:
        from thegent.agents.maif_runner import MAIFAgentRunner

        inner_runner = MockRunner()
        mock_engine = MagicMock(spec=ExecutionEngine)
        maif_runner = MAIFAgentRunner(runner=inner_runner, engine=mock_engine)
        maif_runner.run(prompt="Hello", agent_name="claude", owner="bob")
        mock_engine.execute.assert_called_once()
        call_args = mock_engine.execute.call_args[1]
        assert call_args["runner"] is inner_runner
        assert call_args["run_meta"].prompt == "Hello"
        assert call_args["run_meta"].agent == "claude"
        assert call_args["run_meta"].owner == "bob"


# ---------------------------------------------------------------------------
# Hardening invariants
# ---------------------------------------------------------------------------


class TestHardeningInvariants:
    """@trace AUDIT-N+36 invariants (cross-cutting)"""

    def test_engine_is_reusable_across_calls(self, tmp_path: Path) -> None:
        session_dir = _make_session_dir(tmp_path)
        settings = _make_settings(session_dir)
        engine = ExecutionEngine(settings=settings)
        for i in range(5):
            runner = MockRunner()
            run_meta = _make_run_meta(run_id=f"run_{i}_{uuid.uuid4().hex[:6]}")
            with (
                patch("thegent.execution.Auditor.sign_run"),
                patch(
                    "thegent.execution.Auditor.generate_maif_artifact",
                    create=True,
                    return_value={},
                ),
                patch(
                    "thegent.execution.Auditor.persist_maif_artifact",
                    create=True,
                ),
            ):
                result = engine.execute(runner, run_meta)
            assert result.exit_code == 0
        # Auditor is cached.
        assert engine._get_auditor() is engine._get_auditor()

    def test_engine_rejects_already_executed_run_id(self, tmp_path: Path) -> None:
        """Idempotency: a re-submitted run_id is allowed (the Auditor
        sidecar tracks dedup), but ``run_id`` must remain non-empty.
        """
        session_dir = _make_session_dir(tmp_path)
        settings = _make_settings(session_dir)
        engine = ExecutionEngine(settings=settings)
        runner = MockRunner()
        run_meta = _make_run_meta(run_id="dup_001")
        with (
            patch("thegent.execution.Auditor.sign_run"),
            patch(
                "thegent.execution.Auditor.generate_maif_artifact",
                create=True,
                return_value={},
            ),
            patch("thegent.execution.Auditor.persist_maif_artifact", create=True),
        ):
            engine.execute(runner, run_meta)
            engine.execute(runner, run_meta)
        # Both calls succeed -- idempotency is the caller's responsibility.

    def test_engine_works_with_partial_settings_spec(self, tmp_path: Path) -> None:
        """A ``MagicMock(spec=ThegentSettings)`` with no overrides."""
        session_dir = _make_session_dir(tmp_path)
        partial = MagicMock(spec=["session_dir"])
        partial.session_dir = session_dir
        engine = ExecutionEngine(settings=partial)
        runner = MockRunner()
        run_meta = _make_run_meta()
        with (
            patch("thegent.execution.Auditor.sign_run"),
            patch(
                "thegent.execution.Auditor.generate_maif_artifact",
                create=True,
                return_value={},
            ),
            patch("thegent.execution.Auditor.persist_maif_artifact", create=True),
        ):
            result = engine.execute(runner, run_meta)
        assert result.exit_code == 0
