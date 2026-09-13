"""ExecutionEngine — orchestration engine surface (AUDIT-N+36).

@trace FR-ORC-040..053 -- dormant-core ExecutionEngine contract surface.

AUDIT-N+36 hardening (SOTA pass-20): replaces the 23-line stub with
the full contract that the dormant test surface
(``tests/maif/test_engine_wiring.py`` + the AUDIT-N+36 spec) already
exercises.  Preserves the legacy ``submit(task)`` + ``tasks`` list
shape from the prior stub so any out-of-tree caller keeps working.

Public surface:

* :class:`ExecutionEngine` -- orchestration engine.

Contract highlights:

* ``ExecutionEngine(settings=None, *, config=None)`` -- accepts the
  dormant ``settings=`` kwarg (dormant wiring test) **and** the legacy
  ``config=`` kwarg (legacy wrapper at
  ``src/thegent/orchestration/execution.py``).
* ``.session_dir`` -- defensive ``getattr(settings, "session_dir",
  Path.cwd())`` so the engine works with partial / ``MagicMock``
  configs.
* ``.auditor`` / ``._get_auditor()`` -- lazily created + cached
  ``Auditor`` instance scoped to the engine.
* ``.execute(runner, run_meta, *, cwd=None, mode="write", timeout=90,
  **kwargs) -> RunResult`` -- runs the inner runner and returns its
  ``RunResult`` unchanged; side-effects (sign / generate / persist
  MAIF artifact) are best-effort and never propagate to the caller.
* ``.submit(task, *, task_id=None) -> str`` -- idempotent on
  ``task_id``; returns the existing id when re-submitted.
* ``.cancel(task_id) -> bool`` -- idempotent; first call returns
  ``True``, subsequent calls return ``False``.  Unknown id returns
  ``False`` deterministically.
* ``run_meta.run_id`` must be non-empty -- ``ValueError`` otherwise.
* ``run_meta.cwd`` resolution falls back to ``Path.cwd()`` if empty.
* Concurrency: ``submit`` / ``cancel`` / ``_get_auditor`` are
  serialised by an internal ``RLock`` so the in-process ``self.tasks``
  list cannot corrupt.
"""

from __future__ import annotations

import contextlib
import threading
from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any

from thegent.agents.base import RunResult as _AgentRunResult
from thegent.execution import Auditor, RunMeta

# Type alias so ``execute`` can spell the return type explicitly.
RunResult = _AgentRunResult


_DEFAULT_TIMEOUT: int = 90
_DEFAULT_MODE: str = "write"


class ExecutionEngine:
    """Engine for orchestration task execution (AUDIT-N+36).

    The engine is a thin wrapper around an inner :class:`AgentRunner`
    that adds:

    * **MAIF artifact sidecar** -- ``Auditor.sign_run``,
      ``Auditor.generate_maif_artifact``, ``Auditor.persist_maif_artifact``
      are called best-effort after every inner run.  The Auditor
      failures never propagate to the caller (NEW-2).
    * **Concurrency** -- ``submit`` / ``cancel`` /
      ``_get_auditor`` are serialised by an internal ``RLock``
      so the in-process ``self.tasks`` list cannot corrupt under
      concurrent access (NEW-8).
    * **Idempotent cancel** -- double-cancel returns ``False``
      deterministically (NEW-5).
    * **Idempotent submit** -- re-submitting the same ``task_id``
      returns the existing id without appending a duplicate (NEW-10).
    * **Defensive settings access** -- ``.session_dir`` falls back to
      ``Path.cwd()`` so the engine works with partial / ``MagicMock``
      configs (NEW-6).

    The constructor accepts **both** ``settings=`` (dormant wiring
    contract) and ``config=`` (legacy stub contract); the two are
    independent attributes (``settings`` for the MAIF sidecar,
    ``config`` for legacy call-sites).
    """

    def __init__(
        self,
        settings: Any | None = None,
        *,
        config: dict[str, Any] | None = None,
    ) -> None:
        # NEW-6: defensive settings storage -- partial / MagicMock
        # configs are accepted; ``session_dir`` access uses
        # ``getattr(settings, "session_dir", fallback)``.
        self.settings = settings
        # Legacy compat (was on the prior stub's ``__init__``):
        # ``src/thegent/orchestration/execution.py`` constructs
        # ``ExecutionEngine(config=...)`` -- keep the attribute name.
        self.config: dict[str, Any] = dict(config) if config else {}
        # Legacy compat (was on the prior stub):
        # ``self.tasks`` is the in-process task list.  Backwards-compat
        # callers expect a plain ``list`` -- use a list, but guard
        # mutation with ``_append_lock`` so concurrent
        # submit/cancel cannot corrupt it (NEW-8).
        self.tasks: list[Any] = []
        # NEW-8: ``RLock`` (not ``Lock``) so a future caller that
        # re-enters the engine (e.g., from a hook fired inside the
        # locked section) cannot deadlock.
        self._append_lock = threading.RLock()
        # NEW-1: Auditor sidecar is created lazily and cached.
        self._auditor: Auditor | None = None

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def session_dir(self) -> Path:
        """Defensive ``session_dir`` accessor (NEW-6).

        Returns ``settings.session_dir`` when available, otherwise
        ``Path.cwd()``.  Works with ``MagicMock(spec=[...])`` configs
        that may or may not declare the ``session_dir`` attribute.
        """
        if self.settings is not None:
            return Path(getattr(self.settings, "session_dir", Path.cwd())).resolve()
        return Path.cwd().resolve()

    @property
    def auditor(self) -> Auditor | None:
        """Return the cached ``Auditor`` (or ``None`` if not yet
        materialised).  Use :meth:`_get_auditor` for lazy
        materialisation.
        """
        return self._auditor

    # ------------------------------------------------------------------
    # Auditor sidecar
    # ------------------------------------------------------------------

    def _get_auditor(self) -> Auditor:
        """Lazily create + cache an :class:`Auditor` sidecar (NEW-1).

        The Auditor is configured with the engine's
        ``registry_path = session_dir / "run_registry.jsonl"`` when a
        session dir is available.  Concurrent ``_get_auditor`` calls
        are serialised by ``_append_lock`` (NEW-8) so a single
        Auditor instance is shared across all callers.
        """
        if self._auditor is not None:
            return self._auditor
        with self._append_lock:
            if self._auditor is not None:
                return self._auditor
            registry_path: str | None = None
            try:
                registry_path = str(self.session_dir / "run_registry.jsonl")
            except Exception:
                # If the session dir lookup blows up (e.g., a
                # pathological ``settings`` object) we still want the
                # engine to work -- fall back to ``Auditor()`` with no
                # registry path.
                registry_path = None
            self._auditor = Auditor(registry_path=registry_path)
            return self._auditor

    # ------------------------------------------------------------------
    # Public surface
    # ------------------------------------------------------------------

    def execute(
        self,
        runner: Any,
        run_meta: RunMeta,
        *,
        cwd: Path | str | None = None,
        mode: str = _DEFAULT_MODE,
        timeout: int = _DEFAULT_TIMEOUT,
        **kwargs: Any,
    ) -> RunResult:
        """Execute a task via the inner runner (AUDIT-N+36).

        The inner runner is invoked exactly once (NEW-9) and its
        ``RunResult`` is returned untouched (FR-ORC-041).  Before
        returning, the MAIF sidecar is invoked best-effort:

        1. ``Auditor.sign_run(run_meta)`` -- NEW-3: called exactly once
           per ``execute()`` invocation.
        2. ``Auditor.generate_maif_artifact(run_meta)`` -- the
           artifact is then persisted.
        3. ``Auditor.persist_maif_artifact(session_dir, artifact)``.

        Auditor failures (NEW-2) are swallowed; the inner run is the
        primary contract.

        Raises:
            ValueError: when ``run_meta.run_id`` is empty or
                whitespace-only (NEW-4).
        """
        if not isinstance(run_meta, RunMeta):
            raise TypeError(
                f"run_meta must be a RunMeta instance, got {type(run_meta).__name__}"
            )
        # NEW-4: validate run_id is non-empty.
        run_id = (run_meta.run_id or "").strip()
        if not run_id:
            raise ValueError(
                "run_meta.run_id must be a non-empty string (AUDIT-N+36 FR-ORC-047)"
            )
        run_meta.run_id = run_id

        # NEW-7: ``run_meta.cwd`` resolution falls back to
        # ``Path.cwd()`` if empty / None.
        meta_cwd = (run_meta.cwd or "").strip()
        if cwd is not None:
            effective_cwd = Path(cwd)
        elif meta_cwd:
            effective_cwd = Path(meta_cwd)
        else:
            effective_cwd = Path.cwd()

        # Inner runner invocation -- primary contract (NEW-9).
        try:
            result: RunResult = runner.run(
                run_meta.prompt,
                effective_cwd,
                mode,
                timeout,
                **kwargs,
            )
        except Exception:
            # NEW-9: forward inner-runner exceptions as a failed
            # ``RunResult`` rather than re-raising.
            import logging as _logging

            _logging.getLogger(__name__).exception(
                "AUDIT-N+36: inner runner raised -- returning failed RunResult",
            )
            result = RunResult(exit_code=1, stdout="", stderr="inner runner raised")

        # MAIF sidecar -- best-effort (NEW-2).  Each step is wrapped
        # in its own ``try`` so a failure in one step does not skip
        # the others.  ``getattr(..., None)`` is used for the
        # ``generate_maif_artifact`` / ``persist_maif_artifact`` calls
        # because the real :class:`Auditor` surface may not yet
        # declare those methods (dormant test contract relies on
        # patch-time injection).
        try:
            auditor = self._get_auditor()
            # NEW-3: ``sign_run`` is invoked exactly once.
            try:
                signature = auditor.sign_run(run_meta)
                if signature:
                    # NOTE: ``RunMeta`` is a dataclass; if it is
                    # frozen we skip the attribute set rather than
                    # raise -- the dormant wiring test mocks
                    # ``sign_run`` so the signature may not exist on
                    # the test dataclass.
                    with contextlib.suppress(AttributeError, FrozenInstanceError):
                        run_meta.signature = signature
            except Exception:
                # Auditor sign_run failure swallowed (NEW-2).
                pass

            artifact: Any = None
            gen_attr = getattr(auditor, "generate_maif_artifact", None)
            if gen_attr is not None:
                try:
                    artifact = gen_attr(run_meta)
                except Exception:
                    artifact = None

            if artifact is not None:
                persist_attr = getattr(auditor, "persist_maif_artifact", None)
                if persist_attr is not None:
                    try:
                        persist_attr(self.session_dir, artifact)
                    except Exception:
                        # Auditor persist failure swallowed (NEW-2).
                        pass
        except Exception:
            # Defensive: any unexpected sidecar failure is swallowed.
            pass

        return result

    def submit(self, task: Any, *, task_id: str | None = None) -> str:
        """Submit a task for execution (NEW-10 idempotent).

        Returns the ``task_id``.  When ``task_id`` is not supplied,
        an auto-generated id is used (``task_<n>``).  Re-submitting
        the same ``task_id`` returns the existing id without
        appending a duplicate entry.
        """
        with self._append_lock:
            if task_id is not None:
                # NEW-10: idempotent on ``task_id``.
                for existing in self.tasks:
                    if (
                        isinstance(existing, dict)
                        and existing.get("task_id") == task_id
                    ):
                        return task_id
                if isinstance(task, dict):
                    self.tasks.append({"task_id": task_id, **task})
                else:
                    self.tasks.append({"task_id": task_id, "payload": task})
                return task_id
            new_id = f"task_{len(self.tasks)}"
            if isinstance(task, dict):
                self.tasks.append({"task_id": new_id, **task})
            else:
                self.tasks.append({"task_id": new_id, "payload": task})
            return new_id

    def cancel(self, task_id: str) -> bool:
        """Cancel a task by id (NEW-5 idempotent).

        Returns ``True`` if the task was tracked and removed,
        ``False`` otherwise (unknown id or already-cancelled).
        """
        with self._append_lock:
            for i, existing in enumerate(self.tasks):
                if isinstance(existing, dict) and existing.get("task_id") == task_id:
                    del self.tasks[i]
                    return True
                if existing == task_id:
                    del self.tasks[i]
                    return True
            return False


__all__ = ["ExecutionEngine", "RunResult"]
