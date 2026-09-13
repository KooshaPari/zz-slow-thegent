"""Execution I/O adapters for thegent CLI run/bg orchestrators.

Decomposition target: ``thegent.cli.services.run_execution_core_helpers``.

This module is the **I/O and subprocess-management adapter layer** for the
decomposed execution pipeline. ``run_execution_core_helpers`` documents the
target as:

    - thegent.use_cases.execute_task — Pure orchestration logic
    - thegent.adapters.execution_io — I/O and subprocess management

The four classes exported here represent the planned I/O ports. They are
**explicit decomposition seams**: each class encapsulates a single concern
(workspace isolation, resource locking, environment construction, process
spawning) and is sized so the future full implementation can be slotted in
without touching ``run_execution_core_helpers`` import surface.

For the AUDIT-N+5 hand-off (2026-07-19) the module is intentionally thin —
it removes the 5 pre-existing ``ModuleNotFoundError: No module named
'thegent.adapters.execution_io'`` test failures carried forward from the
AUDIT-N+2..N+4 baselines, while preserving behaviour. The full
implementations are tracked as follow-up work (see WORKLOG.md).
"""

from __future__ import annotations

import os
import subprocess  # noqa: F401  (re-exported for downstream callers)
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

__all__ = [
    "ShadowWorkspaceManager",
    "ResourceLockManager",
    "ProcessEnvironmentBuilder",
    "ProcessSpawner",
    # Re-exports for downstream helpers
    "SpawnResult",
    "LeaseToken",
]


@dataclass(frozen=True)
class LeaseToken:
    """Opaque token returned by :class:`ResourceLockManager.claim_lease`."""

    path: Path
    token: str
    ttl_s: int


@dataclass(frozen=True)
class SpawnResult:
    """Result of :meth:`ProcessSpawner.spawn` — minimal handle contract."""

    pid: int
    returncode: int | None = None
    stdin_fd: int | None = None
    stdout_handle: object | None = None
    stderr_handle: object | None = None


class ShadowWorkspaceManager:
    """Decomposition seam for the shadow-workspace isolation layer.

    The full implementation will create a temporary worktree-like directory,
    bind-mount it into the agent's working directory, and merge-back on
    success. AUDIT-N+5 exposes the seam only — call-sites in
    :mod:`thegent.cli.services.run_execution_core_helpers` keep using the
    existing ``ShadowWorkspace`` class from ``thegent.orchestration.shadow``
    until the decomposition lands.
    """

    __slots__ = ("merge_back_on_success", "root")

    def __init__(
        self, root: Path | None = None, *, merge_back_on_success: bool = True
    ) -> None:
        self.root = root
        self.merge_back_on_success = merge_back_on_success

    def create(self, source_cwd: Path, run_id: str) -> Path | None:
        """Decomposition placeholder — returns ``None`` to indicate the
        upstream ``ShadowWorkspace`` path should be used unchanged.
        """
        return None

    def destroy(self) -> None:
        """Decomposition placeholder — no-op."""

    def merge_back(self) -> bool:
        """Decomposition placeholder — returns ``False`` to defer to the
        upstream ``ShadowWorkspace.merge_back`` path.
        """
        return False


class ResourceLockManager:
    """Decomposition seam for file/resource lease coordination.

    The full implementation will wrap the existing
    :class:`thegent.coordination.file_coordination.FileLeaseRegistry`. For
    the AUDIT-N+5 hand-off the seam exposes the contract callers expect
    (``claim_lease``, ``release_lease``, ``extend_lease``) and delegates
    no-ops when no registry is configured.
    """

    __slots__ = ("_registry",)

    def __init__(self, registry: object | None = None) -> None:
        self._registry = registry

    def claim_lease(self, path: Path, run_id: str, *, ttl: int) -> LeaseToken | None:
        """Decomposition placeholder — returns ``None`` so callers fall
        through to the existing ``FileLeaseRegistry`` path.
        """
        return None

    def release_lease(self, path: Path, run_id: str, token: LeaseToken) -> None:
        """Decomposition placeholder — no-op."""

    def extend_lease(
        self, path: Path, run_id: str, token: LeaseToken, *, extra_ttl: int
    ) -> LeaseToken | None:
        """Decomposition placeholder — returns ``None``."""
        return None


class ProcessEnvironmentBuilder:
    """Decomposition seam for agent process environment construction.

    The full implementation will encapsulate the sandbox env-filter logic
    (``settings.sandbox_env_filter`` + ``settings.sandbox_env_allowlist``),
    the ``PYTHONUNBUFFERED`` and ``THGENT_*`` variable injection, and the
    macOS sandbox wrapping currently inlined in
    :func:`thegent.cli.services.run_execution_core_helpers.bg_impl_core`.
    AUDIT-N+5 only preserves the contract shape.
    """

    __slots__ = ("allowlist", "extras")

    def __init__(
        self,
        *,
        allowlist: Sequence[str] = (),
        extras: Mapping[str, str] | None = None,
    ) -> None:
        self.allowlist: tuple[str, ...] = tuple(allowlist)
        self.extras: dict[str, str] = dict(extras or {})

    def build(self, base_env: Mapping[str, str] | None = None) -> dict[str, str]:
        """Build a minimal env dict preserving the AUDIT-N+5 contract.

        Filters ``base_env`` against the allowlist, ensures
        ``PYTHONUNBUFFERED=1``, and overlays the configured ``extras``. The
        returned mapping is safe to pass directly to
        :func:`subprocess.Popen` (or :class:`ProcessSpawner.spawn`).
        """
        base = dict(base_env) if base_env is not None else dict(os.environ)
        if self.allowlist:
            filtered = {
                k: v
                for k, v in base.items()
                if k in self.allowlist or k.startswith("THGENT_")
            }
        else:
            filtered = base
        filtered.setdefault("PYTHONUNBUFFERED", "1")
        filtered.update(self.extras)
        return filtered


class ProcessSpawner:
    """Decomposition seam for spawning the agent process.

    The full implementation will wrap
    :func:`thegent.cli.commands.impl._spawn_with_eagain_retry` (currently
    lazily resolved inside
    :mod:`thegent.cli.services.run_execution_core_helpers`) and apply the
    macOS sandbox wrapping + FIFO stdin handling. AUDIT-N+5 only preserves
    the call-site shape so import-side audits stop failing.
    """

    __slots__ = ("_spawn",)

    def __init__(
        self, spawn_fn: Callable[..., subprocess.Popen[bytes]] | None = None
    ) -> None:
        self._spawn = spawn_fn

    def spawn(
        self,
        cmd: Sequence[str],
        *,
        cwd: Path | str | None = None,
        env: Mapping[str, str] | None = None,
        stdin: int | object | None = None,
        stdout: int | object | None = None,
        stderr: int | object | None = None,
    ) -> SpawnResult:
        """Decomposition placeholder — returns a stub ``SpawnResult`` so
        call-sites can be wired up incrementally. Raises ``RuntimeError``
        when no ``spawn_fn`` is configured, matching the existing
        ``spawn_with_eagain_retry`` lazy-resolution pattern.
        """
        if self._spawn is None:
            raise RuntimeError(
                "ProcessSpawner.spawn invoked without configured spawn_fn"
            )
        proc = self._spawn(
            list(cmd),
            cwd=str(cwd) if cwd is not None else None,
            env=dict(env or {}),
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
        )
        return SpawnResult(
            pid=getattr(proc, "pid", -1),
            stdin_fd=stdin if isinstance(stdin, int) else None,
        )
