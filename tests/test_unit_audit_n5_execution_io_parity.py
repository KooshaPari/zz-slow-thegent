"""AUDIT-N+5 — run_execution_core_helpers import-side shim parity.

Pins the AUDIT-N+5 hand-off: every missing module / missing name that
:mod:`thegent.cli.services.run_execution_core_helpers` imports at module
top must resolve, and every helper must accept the canonical kwargs the
production call-sites pass.

This guards against regression so that future refactors that remove any
of these shim surfaces (or rename a call-site kwarg) fail this test in
CI instead of silently re-introducing the AUDIT-N+2 baseline.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# AUDIT-N+5 — module-import surface (must resolve cleanly)
# ---------------------------------------------------------------------------


SHIM_MODULES: tuple[str, ...] = (
    "thegent.adapters.execution_io",
    "thegent.cli.commands.observability_impl",
    "thegent.cli.commands.session_meta_impl",
    "thegent.cli.services.run_execution_core_helpers",
)


@pytest.mark.parametrize("module_name", SHIM_MODULES)
def test_audit_n5_module_imports_cleanly(module_name: str) -> None:
    """Every AUDIT-N+5 shim must import without raising."""
    importlib.import_module(module_name)


# ---------------------------------------------------------------------------
# AUDIT-N+5 — adapters.execution_io exports
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "symbol_name",
    [
        "ShadowWorkspaceManager",
        "ResourceLockManager",
        "ProcessEnvironmentBuilder",
        "ProcessSpawner",
        "LeaseToken",
        "SpawnResult",
    ],
)
def test_audit_n5_execution_io_exports(symbol_name: str) -> None:
    """``thegent.adapters.execution_io`` must export the four decomposition
    seams that ``run_execution_core_helpers.py:28-33`` imports at module top,
    plus the supporting ``LeaseToken`` / ``SpawnResult`` dataclasses."""
    execution_io = importlib.import_module("thegent.adapters.execution_io")
    assert hasattr(execution_io, symbol_name), (
        f"thegent.adapters.execution_io.{symbol_name} is missing — "
        f"AUDIT-N+5 shim contract broken."
    )


def test_audit_n5_process_environment_builder_default() -> None:
    """``ProcessEnvironmentBuilder.build()`` must default to allow-all and
    inject ``PYTHONUNBUFFERED=1`` for safe subprocess handoff."""
    from thegent.adapters.execution_io import ProcessEnvironmentBuilder

    builder = ProcessEnvironmentBuilder(extras={"FOO": "bar"})
    env = builder.build()

    assert env["PYTHONUNBUFFERED"] == "1"
    assert env["FOO"] == "bar"


def test_audit_n5_process_environment_builder_allowlist() -> None:
    """``ProcessEnvironmentBuilder.build()`` must filter ``base_env`` against
    ``allowlist`` plus any ``THGENT_*`` prefix when an allowlist is set."""
    from thegent.adapters.execution_io import ProcessEnvironmentBuilder

    base = {"PATH": "/usr/bin", "FOO": "leak", "THGENT_SESSION_ID": "abc"}
    builder = ProcessEnvironmentBuilder(allowlist=("PATH",), extras={})
    env = builder.build(base)

    assert env["PATH"] == "/usr/bin"
    assert "FOO" not in env
    assert env["THGENT_SESSION_ID"] == "abc"


def test_audit_n5_process_spawner_requires_spawn_fn() -> None:
    """``ProcessSpawner.spawn()`` must raise when no ``spawn_fn`` is wired —
    matching the existing ``spawn_with_eagain_retry`` lazy-resolution pattern."""
    from thegent.adapters.execution_io import ProcessSpawner

    spawner = ProcessSpawner()
    with pytest.raises(RuntimeError, match="spawn_fn"):
        spawner.spawn([sys_executable_path(), "-c", "pass"], cwd=Path("."))


def sys_executable_path() -> str:
    import sys

    return sys.executable


# ---------------------------------------------------------------------------
# AUDIT-N+5 — observability_impl contract
# ---------------------------------------------------------------------------


def test_audit_n5_observability_impl_exposes_envelope_parity() -> None:
    """``observability_impl`` must expose ``err_console`` and re-export
    ``print_exc`` so the AUDIT-N+2 envelope-parity contract holds."""
    from thegent.ux import cli_errors

    observability_impl = importlib.import_module("thegent.cli.commands.observability_impl")
    assert hasattr(observability_impl, "err_console")
    assert observability_impl.err_console.stderr is True
    assert observability_impl.print_exc is cli_errors.print_exc


def test_audit_n5_escalate_add_impl_accepts_canonical_kwargs(tmp_path: Path) -> None:
    """``escalate_add_impl`` must accept the kwarg signatures used by the
    four ``run_execution_core_helpers`` call-sites (lines 703, 736, 1431,
    1463) without raising."""
    from thegent.cli.commands import observability_impl

    observability_impl.escalate_add_impl(
        run_id="run_test_audit_n5",
        reason="smoke",
        sla_minutes=30,
        owner="audit-n5",
        agent="antigravity",
        lane="critical",
    )
    observability_impl.escalate_add_impl(
        run_id="run_test_audit_n5_pause",
        reason="HITL pause",
        sla_minutes=30,
        owner="audit-n5",
        agent="antigravity",
        lane="critical",
        priority=1,
    )


def test_audit_n5_escalate_add_impl_returns_none() -> None:
    """``escalate_add_impl`` must return ``None`` so existing
    ``escalate_add_impl(...)`` call-sites stay valid (the original
    behaviour was void-return)."""
    from thegent.cli.commands import observability_impl

    result = observability_impl.escalate_add_impl(
        run_id="run_test_void",
        reason="void-return",
        sla_minutes=10,
        owner="audit-n5",
        agent="antigravity",
        lane="standard",
    )
    assert result is None


# ---------------------------------------------------------------------------
# AUDIT-N+5 — session_meta_impl contract
# ---------------------------------------------------------------------------


def test_audit_n5_session_meta_impl_exposes_envelope_parity() -> None:
    """``session_meta_impl`` must expose ``err_console`` and re-export
    ``print_exc`` so the AUDIT-N+2 envelope-parity contract holds."""
    from thegent.ux import cli_errors

    session_meta_impl = importlib.import_module("thegent.cli.commands.session_meta_impl")
    assert hasattr(session_meta_impl, "err_console")
    assert session_meta_impl.err_console.stderr is True
    assert session_meta_impl.print_exc is cli_errors.print_exc


def test_audit_n5_save_session_meta_writes_json(tmp_path: Path) -> None:
    """``_save_session_meta`` must serialise the meta dict to JSON at the
    supplied path, creating parents as needed."""
    from thegent.cli.commands.session_meta_impl import _save_session_meta

    meta_path = tmp_path / "sub" / "meta.json"
    meta = {"run_id": "run_smoke", "status": "running"}
    _save_session_meta(meta_path, meta)

    import json

    assert json.loads(meta_path.read_text(encoding="utf-8")) == meta


def test_audit_n5_build_continuation_prompt_returns_prompt_when_no_prior(
    tmp_path: Path,
) -> None:
    """``_build_continuation_prompt`` must return ``prompt`` unchanged when
    no prior session output is available."""
    from thegent.cli.commands.session_meta_impl import _build_continuation_prompt

    class _Settings:
        session_dir = str(tmp_path)

    result = _build_continuation_prompt(
        _Settings(),
        "nonexistent-session",
        "hello world",
        include_stderr=False,
    )
    assert result == "hello world"


# ---------------------------------------------------------------------------
# AUDIT-N+5 — thegent.execution surface extension
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "symbol_name",
    [
        "AgentSource",
        "InteractivityMode",
        "FreshnessValidator",
        "DeferralQueue",
        "DLQManager",
        "EvidenceLinter",
    ],
)
def test_audit_n5_execution_module_exports(symbol_name: str) -> None:
    """``thegent.execution`` must export the six new orchestrator-surfaces
    that ``run_execution_core_helpers`` references."""
    execution = importlib.import_module("thegent.execution")
    assert hasattr(execution, symbol_name), (
        f"thegent.execution.{symbol_name} is missing — AUDIT-N+5 "
        f"extension contract broken."
    )


def test_audit_n5_agent_source_is_str_enum() -> None:
    """``AgentSource`` must behave as ``str, Enum`` so callers can compare
    to plain strings (mirrors downstream ``run_meta.source`` persistence)."""
    from thegent.execution import AgentSource

    assert AgentSource.THEGENT_RUN == "thegent_run"
    assert AgentSource.THEGENT_SUBAGENT == "thegent_subagent"


def test_audit_n5_load_classifier_get_load_level_default(tmp_path: Path) -> None:
    """``LoadClassifier.get_load_level()`` must return ``\"normal\"`` when
    no burst signal is available, matching the original orchestrator
    branch contract."""
    from thegent.execution import LoadClassifier

    classifier = LoadClassifier(session_dir=tmp_path)
    assert classifier.get_load_level() == "normal"


# ---------------------------------------------------------------------------
# AUDIT-N+5 — thegent.maif.MAIFRunner contract
# ---------------------------------------------------------------------------


def test_audit_n5_maif_runner_record_run_start() -> None:
    """``MAIFRunner.record_run_start`` must accept the four keyword
    arguments used at ``run_execution_core_helpers.py:761-766``."""
    from thegent.maif import MAIFRunner

    runner = MAIFRunner()
    runner.record_run_start(
        run_id="run_maif_test",
        owner="audit-n5",
        prompt="hello",
        agent="antigravity",
    )


def test_audit_n5_maif_runner_record_run_end() -> None:
    """``MAIFRunner.record_run_end`` must accept the three keyword
    arguments used at ``run_execution_core_helpers.py:1039-1042``."""
    from thegent.maif import MAIFRunner

    runner = MAIFRunner()
    runner.record_run_end(
        run_id="run_maif_test",
        status="completed",
        output_summary="all good",
    )


# ---------------------------------------------------------------------------
# AUDIT-N+5 — run_execution_core_helpers envelope-parity contract
# ---------------------------------------------------------------------------


def test_audit_n5_run_execution_core_helpers_exposes_envelope_parity() -> None:
    """``run_execution_core_helpers`` must expose ``err_console`` and
    re-export ``print_exc`` (AUDIT-N+2 contract preserved through AUDIT-N+5)."""
    from thegent.ux import cli_errors

    helpers = importlib.import_module("thegent.cli.services.run_execution_core_helpers")
    assert hasattr(helpers, "err_console")
    assert helpers.err_console.stderr is True
    assert helpers.print_exc is cli_errors.print_exc


def test_audit_n5_run_execution_core_helpers_re_exports_io_seams() -> None:
    """``run_execution_core_helpers`` must re-export the four
    decomposition seams from ``thegent.adapters.execution_io`` so
    downstream callers that already import through the helpers don't
    need a second import line."""
    from thegent.adapters import execution_io

    helpers = importlib.import_module("thegent.cli.services.run_execution_core_helpers")
    assert helpers.ShadowWorkspaceManager is execution_io.ShadowWorkspaceManager
    assert helpers.ResourceLockManager is execution_io.ResourceLockManager
    assert helpers.ProcessEnvironmentBuilder is execution_io.ProcessEnvironmentBuilder
    assert helpers.ProcessSpawner is execution_io.ProcessSpawner
